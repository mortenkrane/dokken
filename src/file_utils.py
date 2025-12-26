"""File system utility functions for path resolution and directory operations."""

import os
from pathlib import Path

from src.constants import ERROR_CANNOT_CREATE_DIR, ERROR_NOT_IN_GIT_REPO
from src.doc_types import DocType


def find_repo_root(start_path: str) -> str | None:
    """
    Find the repository root by searching for .git directory.

    Args:
        start_path: Path to start searching from.

    Returns:
        Path to repository root, or None if not found.
    """
    current = Path(start_path).resolve()

    # Search up the directory tree
    while current != current.parent:
        if (current / ".git").exists():
            return str(current)
        current = current.parent

    return None


def resolve_output_path(*, doc_type: DocType, module_path: str) -> str:
    """
    Resolve output path for documentation file.

    NOTE: This function does NOT create directories. Call ensure_output_directory()
    before writing to the returned path if needed.

    Args:
        doc_type: Type of documentation being generated.
        module_path: Path to the module directory (or any directory in the repo).

    Returns:
        Absolute path to the output documentation file.

    Raises:
        ValueError: If git root not found for repo-wide doc types.
    """
    if doc_type == DocType.MODULE_README:
        return os.path.join(module_path, "README.md")

    # Find git root for repo-wide docs
    repo_root = find_repo_root(module_path)
    if not repo_root:
        raise ValueError(
            f"Cannot generate {doc_type.value}: {ERROR_NOT_IN_GIT_REPO}. "
            f"Initialize git or use MODULE_README type."
        )

    if doc_type == DocType.PROJECT_README:
        return os.path.join(repo_root, "README.md")

    if doc_type == DocType.STYLE_GUIDE:
        return os.path.join(repo_root, "docs", "style-guide.md")

    raise ValueError(f"Unknown doc type: {doc_type}")


def ensure_output_directory(output_path: str) -> None:
    """
    Ensure the parent directory exists for the output path.

    Args:
        output_path: Full path to the output file.

    Raises:
        PermissionError: If cannot create the directory.
    """
    parent_dir = os.path.dirname(output_path)
    if parent_dir and not os.path.exists(parent_dir):
        try:
            os.makedirs(parent_dir, exist_ok=True)
        except PermissionError as e:
            raise PermissionError(
                ERROR_CANNOT_CREATE_DIR.format(parent_dir=parent_dir, error=e)
            ) from e
