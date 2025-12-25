"""Tests for src/utils.py"""

from pathlib import Path
from typing import Any

import pytest
from pytest_mock import MockerFixture

from src.doc_types import DocType
from src.records import DocumentationDriftCheck
from src.utils import (
    DRIFT_CACHE_SIZE,
    _generate_cache_key,
    _hash_content,
    clear_drift_cache,
    ensure_output_directory,
    find_repo_root,
    get_drift_cache_info,
    resolve_output_path,
)


def test_find_repo_root_with_git(tmp_path: Path) -> None:
    """Test find_repo_root finds .git directory."""
    # Create repo structure with .git
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    # Create nested directory
    nested = repo_root / "src" / "module"
    nested.mkdir(parents=True)

    # Should find repo root from nested directory
    result = find_repo_root(str(nested))

    assert result == str(repo_root)


def test_find_repo_root_no_git(tmp_path: Path) -> None:
    """Test find_repo_root returns None when no .git directory exists."""
    # Create directory without .git
    module_dir = tmp_path / "no_git"
    module_dir.mkdir()

    result = find_repo_root(str(module_dir))

    assert result is None


def test_find_repo_root_from_root_directory(tmp_path: Path) -> None:
    """Test find_repo_root when starting from repo root."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    result = find_repo_root(str(repo_root))

    assert result == str(repo_root)


def test_resolve_output_path_module_readme(tmp_path: Path) -> None:
    """Test resolve_output_path for MODULE_README."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    result = resolve_output_path(
        doc_type=DocType.MODULE_README, module_path=str(module_dir)
    )

    assert result == str(module_dir / "README.md")


def test_resolve_output_path_project_readme(tmp_path: Path) -> None:
    """Test resolve_output_path for PROJECT_README."""
    # Create repo structure
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    module_dir = repo_root / "src"
    module_dir.mkdir()

    result = resolve_output_path(
        doc_type=DocType.PROJECT_README, module_path=str(module_dir)
    )

    assert result == str(repo_root / "README.md")


def test_resolve_output_path_style_guide(tmp_path: Path) -> None:
    """Test resolve_output_path for STYLE_GUIDE."""
    # Create repo structure
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    module_dir = repo_root / "src"
    module_dir.mkdir()

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


# --- Tests for cache utilities ---


def test_hash_content() -> None:
    """Test _hash_content generates consistent SHA256 hashes."""
    content = "Sample content"
    hash1 = _hash_content(content)
    hash2 = _hash_content(content)

    # Same content should produce same hash
    assert hash1 == hash2

    # Different content should produce different hash
    different_hash = _hash_content("Different content")
    assert hash1 != different_hash

    # Hash should be a valid SHA256 hex string (64 characters)
    assert len(hash1) == 64
    assert all(c in "0123456789abcdef" for c in hash1)


def test_generate_cache_key_includes_llm_model(
    mock_llm_client: Any,
) -> None:
    """Test _generate_cache_key includes LLM model in the cache key."""
    # Mock LLM with model attribute
    mock_llm_client.model = "claude-3-5-haiku-20241022"

    key1 = _generate_cache_key("context", "doc", mock_llm_client)

    # Key should include model identifier
    assert "claude-3-5-haiku-20241022" in key1

    # Different model should produce different key
    mock_llm_client.model = "gpt-4o-mini"
    key2 = _generate_cache_key("context", "doc", mock_llm_client)

    assert key1 != key2
    assert "gpt-4o-mini" in key2


def test_clear_drift_cache_removes_all_entries(
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test clear_drift_cache removes all cached entries."""
    from src.llm import check_drift

    clear_drift_cache()

    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_drift_check_no_drift
    mock_program_class.from_defaults.return_value = mock_program

    # Add some entries to cache
    check_drift(llm=mock_llm_client, context="ctx1", current_doc="doc1")
    check_drift(llm=mock_llm_client, context="ctx2", current_doc="doc2")

    # Verify cache has entries
    cache_info = get_drift_cache_info()
    assert cache_info["size"] == 2

    # Clear cache
    clear_drift_cache()

    # Verify cache is empty
    cache_info = get_drift_cache_info()
    assert cache_info["size"] == 0

    # Next call should trigger LLM again
    check_drift(llm=mock_llm_client, context="ctx1", current_doc="doc1")
    # Should be called 3 times total (2 before clear, 1 after)
    assert mock_program_class.from_defaults.call_count == 3


def test_get_drift_cache_info_returns_correct_stats(
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test get_drift_cache_info returns accurate cache statistics."""
    from src.llm import check_drift

    clear_drift_cache()

    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_drift_check_no_drift
    mock_program_class.from_defaults.return_value = mock_program

    # Initially empty
    cache_info = get_drift_cache_info()
    assert cache_info["size"] == 0
    assert cache_info["maxsize"] == DRIFT_CACHE_SIZE

    # Add one entry
    check_drift(llm=mock_llm_client, context="ctx1", current_doc="doc1")
    cache_info = get_drift_cache_info()
    assert cache_info["size"] == 1

    # Add another entry
    check_drift(llm=mock_llm_client, context="ctx2", current_doc="doc2")
    cache_info = get_drift_cache_info()
    assert cache_info["size"] == 2
