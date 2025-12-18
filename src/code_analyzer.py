"""Code analysis and context extraction for documentation generation."""

import ast
import fnmatch
import os
from pathlib import Path

from rich.console import Console

from src.config import load_config

console = Console()


def get_module_context(*, module_path: str, depth: int = 0) -> str:
    """
    Fetches the full code content for all Python files in a module directory.

    Respects exclusion rules from .dokken.toml configuration files.

    Args:
        module_path: The path to the module directory to analyze.
        depth: Directory depth to traverse. 0=root only, 1=root+1 level, -1=infinite.

    Returns:
        A formatted string containing all Python files' content.
    """
    try:
        # Load configuration for exclusions
        config = load_config(module_path=module_path)

        # Find all Python files in the module directory
        python_files = _find_python_files(module_path=module_path, depth=depth)

        if not python_files:
            console.print(f"[yellow]⚠[/yellow] No Python files found in {module_path}")
            return ""

        # Filter out excluded files
        filtered_files = _filter_excluded_files(
            python_files, module_path, config.exclusions.files
        )

        if not filtered_files:
            console.print(
                f"[yellow]⚠[/yellow] All Python files in {module_path} are excluded"
            )
            return ""

        context = f"--- MODULE PATH: {module_path} ---\n\n"

        for file_path in sorted(filtered_files):
            # Get the current file content
            with open(file_path) as f:
                code_content = f.read()

            # Filter out excluded symbols
            filtered_content = _filter_excluded_symbols(
                code_content, config.exclusions.symbols
            )

            # Add file context
            context += f"--- FILE: {file_path} ---\n{filtered_content}\n\n"

        return context
    except Exception as e:  # noqa: BLE001
        console.print(f"[red]Error getting module context for {module_path}:[/red] {e}")
        return ""


def _find_python_files(*, module_path: str, depth: int) -> list[str]:
    """
    Find Python files in a directory up to a specified depth.

    Args:
        module_path: The root directory to search.
        depth: Directory depth to traverse. 0=root only, 1=root+1 level, -1=infinite.

    Returns:
        List of absolute paths to Python files.
    """
    root = Path(module_path)
    python_files = []

    if depth == -1:
        # Infinite recursion using rglob (recursive glob)
        python_files = [str(p) for p in root.rglob("*.py")]
    elif depth == 0:
        # Root level only - direct children with .py extension
        python_files = [str(p) for p in root.glob("*.py")]
    else:
        # Limited depth recursion
        # Start with root level files (*.py)
        python_files = [str(p) for p in root.glob("*.py")]

        # Add files from deeper levels
        # depth=1 adds */*.py, depth=2 adds */*.py and */*/*.py, etc.
        for current_depth in range(1, depth + 1):
            # Build pattern: depth=1 → "*/*.py", depth=2 → "*/*/*.py"
            pattern = "/".join(["*"] * current_depth) + "/*.py"
            python_files.extend([str(p) for p in root.glob(pattern)])

    return python_files


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


def _filter_excluded_symbols(source_code: str, exclusion_patterns: list[str]) -> str:
    """
    Filter out top-level functions and classes matching exclusion patterns.

    Args:
        source_code: Python source code to filter.
        exclusion_patterns: List of symbol name patterns to exclude.

    Returns:
        Filtered source code with excluded symbols removed.
    """
    if not exclusion_patterns:
        return source_code

    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        # If we can't parse, return original code
        return source_code

    symbols_to_exclude = _find_excluded_symbols(tree, exclusion_patterns)

    if not symbols_to_exclude:
        return source_code

    return _remove_excluded_lines(source_code, symbols_to_exclude)


def _find_excluded_symbols(
    tree: ast.Module, exclusion_patterns: list[str]
) -> list[tuple[int, int]]:
    """
    Find line ranges for top-level symbols matching exclusion patterns.

    Args:
        tree: Parsed AST of the source code.
        exclusion_patterns: List of symbol name patterns to exclude.

    Returns:
        List of (start_line, end_line) tuples for excluded symbols.
    """
    symbols_to_exclude = []
    symbol_types = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)

    for node in tree.body:
        if not isinstance(node, symbol_types):
            continue

        matches_pattern = any(
            fnmatch.fnmatch(node.name, pattern) for pattern in exclusion_patterns
        )

        if matches_pattern:
            symbols_to_exclude.append((node.lineno, node.end_lineno or node.lineno))

    return symbols_to_exclude


def _remove_excluded_lines(
    source_code: str, excluded_ranges: list[tuple[int, int]]
) -> str:
    """
    Remove lines from source code that fall within excluded ranges.

    Args:
        source_code: The source code to filter.
        excluded_ranges: List of (start_line, end_line) tuples to remove.

    Returns:
        Filtered source code.
    """
    lines = source_code.splitlines(keepends=True)
    filtered_lines = []

    for line_num, line in enumerate(lines, start=1):
        excluded = any(start <= line_num <= end for start, end in excluded_ranges)

        if not excluded:
            filtered_lines.append(line)

    return "".join(filtered_lines)
