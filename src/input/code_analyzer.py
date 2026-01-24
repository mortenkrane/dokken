"""Code analysis and context extraction for documentation generation."""

import fnmatch
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from rich.console import Console

from src.config import load_config

console = Console()


def get_module_context(*, module_path: str, depth: int = 0) -> str:
    """
    Fetches the full code content for all source files in a module directory.

    Respects exclusion rules and file type configuration from .dokken.toml.

    Args:
        module_path: The path to the module directory to analyze.
        depth: Directory depth to traverse. 0=root only, 1=root+1 level, -1=infinite.

    Returns:
        A formatted string containing all source files' content.
    """
    try:
        # Load configuration for exclusions and file types
        config = load_config(module_path=module_path)

        # Find all source files in the module directory
        source_files = _find_source_files(
            module_path=module_path,
            depth=depth,
            file_types=config.file_types,
            excluded_dirs=config.exclusions.dirs,
        )

        if not source_files:
            file_types_str = ", ".join(config.file_types)
            console.print(
                f"[yellow]⚠[/yellow] No source files ({file_types_str}) found in"
                f"{module_path}"
            )
            return ""

        # Filter out excluded files
        filtered_files = _filter_excluded_files(
            source_files, module_path, config.exclusions.files
        )

        if not filtered_files:
            console.print(
                f"[yellow]⚠[/yellow] All source files in {module_path} are excluded"
            )
            return ""

        context = f"--- MODULE PATH: {module_path} ---\n\n"

        # Read files in parallel for better I/O performance on large codebases
        with ThreadPoolExecutor() as executor:
            file_results = list(executor.map(_read_file, sorted(filtered_files)))

        # Combine results in sorted order
        for file_path, file_content in file_results:
            if file_content is not None:
                context += f"--- FILE: {file_path} ---\n{file_content}\n\n"

        return context
    except OSError as e:
        console.print(f"[red]Error accessing module path {module_path}:[/red] {e}")
        return ""


def _read_file(file_path: str) -> tuple[str, str] | tuple[str, None]:
    """
    Read a single file for parallel execution.

    Args:
        file_path: Path to the file to read.

    Returns:
        Tuple of (file_path, content) on success, or (file_path, None) on error.
    """
    try:
        with open(file_path) as f:
            content = f.read()
        return file_path, content
    except OSError as e:
        console.print(f"[yellow]⚠[/yellow] Could not read {file_path}: {e}")
        return file_path, None


def _should_exclude_dir(dir_path: Path, excluded_dirs: list[str]) -> bool:
    """Check if a directory should be excluded based on patterns."""
    dir_name = dir_path.name
    return any(fnmatch.fnmatch(dir_name, pattern) for pattern in excluded_dirs)


def _should_recurse_into_dir(current_depth: int, depth: int) -> bool:
    """Check if we should recurse into a directory based on depth limit."""
    return depth == -1 or current_depth < depth


def _is_matching_file(file_path: Path, normalized_extensions: list[str]) -> bool:
    """Check if a file matches any of the specified extensions."""
    return any(file_path.suffix == ext for ext in normalized_extensions)


def _process_directory(
    item: Path,
    current_depth: int,
    depth: int,
    normalized_extensions: list[str],
    excluded_dirs: list[str],
) -> list[Path]:
    """Process a directory item during recursive file search."""
    # Skip excluded directories
    if _should_exclude_dir(item, excluded_dirs):
        return []
    # Recurse if within depth limit
    if _should_recurse_into_dir(current_depth, depth):
        return _find_files_recursive(
            item, current_depth + 1, depth, normalized_extensions, excluded_dirs
        )
    return []


def _find_files_recursive(
    current_path: Path,
    current_depth: int,
    depth: int,
    normalized_extensions: list[str],
    excluded_dirs: list[str],
) -> list[Path]:
    """Recursively find files while respecting depth and exclusions."""
    files = []

    try:
        for item in current_path.iterdir():
            if item.is_dir():
                files.extend(
                    _process_directory(
                        item, current_depth, depth, normalized_extensions, excluded_dirs
                    )
                )
            elif item.is_file() and _is_matching_file(item, normalized_extensions):
                files.append(item)
    except (PermissionError, OSError):
        # Skip directories we can't access
        pass

    return files


def _find_source_files(
    *,
    module_path: str,
    depth: int,
    file_types: list[str],
    excluded_dirs: list[str],
) -> list[str]:
    """
    Find source files with specified extensions in a directory up to a specified depth.

    Excludes directories matching patterns in excluded_dirs from traversal.

    Args:
        module_path: The root directory to search.
        depth: Directory depth to traverse. 0=root only, 1=root+1 level, -1=infinite.
        file_types: List of file extensions to include (e.g., ['.py', '.js', '.ts']).
        excluded_dirs: List of directory name patterns to exclude from traversal.

    Returns:
        List of absolute paths to matching source files.
    """
    root = Path(module_path)

    # Normalize extensions to ensure they start with a dot
    normalized_extensions = [
        ext if ext.startswith(".") else f".{ext}" for ext in file_types
    ]

    # Use recursive approach for all depths to properly handle exclusions
    found_paths = _find_files_recursive(
        root, 0, depth, normalized_extensions, excluded_dirs
    )
    return [str(p) for p in found_paths]


def _filter_excluded_files(
    file_paths: list[str], module_path: str, exclusion_patterns: list[str]
) -> list[str]:
    """
    Filter out files matching exclusion patterns.

    Args:
        file_paths: List of full file paths to filter.
        module_path: The module directory path (for relative path calculation).
        exclusion_patterns: List of glob patterns to exclude.

    Returns:
        List of file paths that don't match any exclusion pattern.
    """
    if not exclusion_patterns:
        return file_paths

    filtered = []
    for file_path in file_paths:
        # Get filename only (not full path) for pattern matching
        filename = os.path.basename(file_path)

        # Check if filename matches any exclusion pattern
        excluded = any(
            fnmatch.fnmatch(filename, pattern) for pattern in exclusion_patterns
        )

        if not excluded:
            filtered.append(file_path)

    return filtered
