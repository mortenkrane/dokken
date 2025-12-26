"""Tests for src/file_utils.py"""

from pathlib import Path

import pytest

from src.doc_types import DocType
from src.file_utils import ensure_output_directory, find_repo_root, resolve_output_path


def test_find_repo_root_with_git(git_repo: Path) -> None:
    """Test find_repo_root finds .git directory."""
    # Create nested directory
    nested = git_repo / "src" / "module"
    nested.mkdir(parents=True)

    # Should find repo root from nested directory
    result = find_repo_root(str(nested))

    assert result == str(git_repo)


def test_find_repo_root_no_git(tmp_path: Path) -> None:
    """Test find_repo_root returns None when no .git directory exists."""
    # Create directory without .git
    module_dir = tmp_path / "no_git"
    module_dir.mkdir()

    result = find_repo_root(str(module_dir))

    assert result is None


def test_find_repo_root_from_root_directory(git_repo: Path) -> None:
    """Test find_repo_root when starting from repo root."""
    result = find_repo_root(str(git_repo))

    assert result == str(git_repo)


def test_resolve_output_path_module_readme(tmp_path: Path) -> None:
    """Test resolve_output_path for MODULE_README."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    result = resolve_output_path(
        doc_type=DocType.MODULE_README, module_path=str(module_dir)
    )

    assert result == str(module_dir / "README.md")


def test_resolve_output_path_project_readme(git_repo_with_module: tuple[Path, Path]) -> None:
    """Test resolve_output_path for PROJECT_README."""
    repo_root, module_dir = git_repo_with_module

    result = resolve_output_path(
        doc_type=DocType.PROJECT_README, module_path=str(module_dir)
    )

    assert result == str(repo_root / "README.md")


def test_resolve_output_path_style_guide(git_repo_with_module: tuple[Path, Path]) -> None:
    """Test resolve_output_path for STYLE_GUIDE."""
    repo_root, module_dir = git_repo_with_module

    result = resolve_output_path(
        doc_type=DocType.STYLE_GUIDE, module_path=str(module_dir)
    )

    assert result == str(repo_root / "docs" / "style-guide.md")


def test_resolve_output_path_project_readme_no_git(tmp_path: Path) -> None:
    """Test resolve_output_path raises ValueError for PROJECT_README without git."""
    module_dir = tmp_path / "no_git"
    module_dir.mkdir()

    with pytest.raises(ValueError, match="not in a git repository"):
        resolve_output_path(
            doc_type=DocType.PROJECT_README, module_path=str(module_dir)
        )


def test_resolve_output_path_style_guide_no_git(tmp_path: Path) -> None:
    """Test resolve_output_path raises ValueError for STYLE_GUIDE without git."""
    module_dir = tmp_path / "no_git"
    module_dir.mkdir()

    with pytest.raises(ValueError, match="not in a git repository"):
        resolve_output_path(doc_type=DocType.STYLE_GUIDE, module_path=str(module_dir))


def test_ensure_output_directory_creates_directory(tmp_path: Path) -> None:
    """Test ensure_output_directory creates parent directory."""
    output_path = tmp_path / "new_dir" / "subdir" / "file.md"

    ensure_output_directory(str(output_path))

    # Parent directory should be created
    assert (tmp_path / "new_dir" / "subdir").exists()


def test_ensure_output_directory_existing_directory(tmp_path: Path) -> None:
    """Test ensure_output_directory works when directory already exists."""
    output_dir = tmp_path / "existing"
    output_dir.mkdir(parents=True)
    output_path = output_dir / "file.md"

    # Should not raise
    ensure_output_directory(str(output_path))

    assert output_dir.exists()


def test_ensure_output_directory_file_in_root(tmp_path: Path) -> None:
    """Test ensure_output_directory with file in root directory."""
    output_path = tmp_path / "file.md"

    # Should handle files in existing directories
    ensure_output_directory(str(output_path))

    # tmp_path already exists, should not raise
    assert tmp_path.exists()


def test_ensure_output_directory_permission_error(tmp_path: Path, mocker) -> None:
    """Test ensure_output_directory raises PermissionError when cannot create dir."""
    output_path = tmp_path / "protected" / "file.md"

    # Mock os.makedirs to raise PermissionError
    mocker.patch("os.makedirs", side_effect=PermissionError("Permission denied"))

    with pytest.raises(PermissionError, match="Cannot create"):
        ensure_output_directory(str(output_path))
