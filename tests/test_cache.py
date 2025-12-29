"""Tests for src/cache.py"""

import json
from pathlib import Path
from typing import Any

from pytest_mock import MockerFixture

from src.cache import (
    DRIFT_CACHE_SIZE,
    _generate_cache_key,
    _hash_content,
    clear_drift_cache,
    get_drift_cache_info,
    load_drift_cache_from_disk,
    save_drift_cache_to_disk,
    set_cache_max_size,
)
from src.records import DocumentationDriftCheck


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


def test_save_drift_cache_to_disk(
    tmp_path: Path,
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test save_drift_cache_to_disk persists cache to JSON file."""
    from src.llm import check_drift

    clear_drift_cache()

    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_drift_check_no_drift
    mock_program_class.from_defaults.return_value = mock_program

    # Add entries to cache
    check_drift(llm=mock_llm_client, context="test_context", current_doc="test_doc")

    # Save to disk
    cache_file = tmp_path / "test_cache.json"
    save_drift_cache_to_disk(str(cache_file))

    # Verify file exists and has correct structure
    assert cache_file.exists()
    data = json.loads(cache_file.read_text())

    assert data["version"] == 1
    assert "entries" in data
    assert len(data["entries"]) == 1

    # Verify entry structure
    entry = next(iter(data["entries"].values()))
    assert "drift_detected" in entry
    assert "rationale" in entry
    assert entry["drift_detected"] is False


def test_load_drift_cache_from_disk(
    tmp_path: Path,
    mocker: MockerFixture,
    mock_llm_client: Any,
) -> None:
    """Test load_drift_cache_from_disk restores cache from JSON file."""
    clear_drift_cache()

    # Create a cache file
    cache_file = tmp_path / "test_cache.json"
    cache_data = {
        "version": 1,
        "entries": {
            "test_key": {
                "drift_detected": True,
                "rationale": "Test rationale",
            }
        },
    }
    cache_file.write_text(json.dumps(cache_data))

    # Load from disk
    load_drift_cache_from_disk(str(cache_file))

    # Verify cache was populated
    cache_info = get_drift_cache_info()
    assert cache_info["size"] == 1


def test_load_drift_cache_from_disk_missing_file(tmp_path: Path) -> None:
    """Test load_drift_cache_from_disk handles missing file gracefully."""
    clear_drift_cache()

    # Try to load from non-existent file
    cache_file = tmp_path / "nonexistent.json"
    load_drift_cache_from_disk(str(cache_file))

    # Should not raise error, cache should be empty
    cache_info = get_drift_cache_info()
    assert cache_info["size"] == 0


def test_load_drift_cache_from_disk_corrupted_file(tmp_path: Path) -> None:
    """Test load_drift_cache_from_disk handles corrupted file gracefully."""
    clear_drift_cache()

    # Create corrupted cache file
    cache_file = tmp_path / "corrupted_cache.json"
    cache_file.write_text("invalid json{{{")

    # Should not raise error, cache should be empty
    load_drift_cache_from_disk(str(cache_file))

    cache_info = get_drift_cache_info()
    assert cache_info["size"] == 0


def test_load_drift_cache_from_disk_invalid_version(tmp_path: Path) -> None:
    """Test load_drift_cache_from_disk ignores file with wrong version."""
    clear_drift_cache()

    # Create cache file with wrong version
    cache_file = tmp_path / "wrong_version.json"
    cache_data = {
        "version": 999,
        "entries": {
            "test_key": {
                "drift_detected": True,
                "rationale": "Test",
            }
        },
    }
    cache_file.write_text(json.dumps(cache_data))

    # Should ignore file with wrong version
    load_drift_cache_from_disk(str(cache_file))

    cache_info = get_drift_cache_info()
    assert cache_info["size"] == 0


def test_save_and_load_roundtrip(
    tmp_path: Path,
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test save and load cache roundtrip preserves data."""
    from src.llm import check_drift

    clear_drift_cache()

    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_drift_check_no_drift
    mock_program_class.from_defaults.return_value = mock_program

    # Add entries to cache
    check_drift(llm=mock_llm_client, context="ctx1", current_doc="doc1")
    check_drift(llm=mock_llm_client, context="ctx2", current_doc="doc2")

    # Save to disk
    cache_file = tmp_path / "roundtrip_cache.json"
    save_drift_cache_to_disk(str(cache_file))

    # Clear in-memory cache
    clear_drift_cache()
    assert get_drift_cache_info()["size"] == 0

    # Load from disk
    load_drift_cache_from_disk(str(cache_file))

    # Verify cache was restored
    cache_info = get_drift_cache_info()
    assert cache_info["size"] == 2

    # Verify cache hits work (LLM should not be called again)
    initial_call_count = mock_program_class.from_defaults.call_count
    check_drift(llm=mock_llm_client, context="ctx1", current_doc="doc1")
    assert mock_program_class.from_defaults.call_count == initial_call_count


def test_set_cache_max_size(
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test set_cache_max_size updates the maximum cache size."""
    from src.llm import check_drift

    clear_drift_cache()

    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_drift_check_no_drift
    mock_program_class.from_defaults.return_value = mock_program

    # Set small cache size
    set_cache_max_size(2)

    # Verify cache info reflects new size
    cache_info = get_drift_cache_info()
    assert cache_info["maxsize"] == 2

    # Add 3 entries (should evict oldest)
    check_drift(llm=mock_llm_client, context="ctx1", current_doc="doc1")
    check_drift(llm=mock_llm_client, context="ctx2", current_doc="doc2")
    check_drift(llm=mock_llm_client, context="ctx3", current_doc="doc3")

    # Cache should only have 2 entries (FIFO eviction)
    cache_info = get_drift_cache_info()
    assert cache_info["size"] == 2

    # Reset to default
    set_cache_max_size(DRIFT_CACHE_SIZE)


def test_save_drift_cache_creates_parent_directory(
    tmp_path: Path,
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test save_drift_cache_to_disk creates parent directories."""
    from src.llm import check_drift

    clear_drift_cache()

    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_drift_check_no_drift
    mock_program_class.from_defaults.return_value = mock_program

    # Add entry to cache
    check_drift(llm=mock_llm_client, context="test", current_doc="doc")

    # Save to nested path that doesn't exist
    nested_path = tmp_path / "cache" / "nested" / "test.json"
    assert not nested_path.parent.exists()

    save_drift_cache_to_disk(str(nested_path))

    # Verify parent directory was created and file exists
    assert nested_path.parent.exists()
    assert nested_path.exists()


def test_save_drift_cache_handles_permission_error(
    tmp_path: Path,
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test save_drift_cache_to_disk handles permission errors gracefully."""
    from src.llm import check_drift

    clear_drift_cache()

    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_drift_check_no_drift
    mock_program_class.from_defaults.return_value = mock_program

    # Add entry to cache
    check_drift(llm=mock_llm_client, context="test", current_doc="doc")

    # Create read-only directory
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()
    readonly_dir.chmod(0o555)  # Read and execute only

    cache_file = readonly_dir / "cache.json"

    # Should not raise exception, just silently fail
    try:
        save_drift_cache_to_disk(str(cache_file))
        # If we got here, save either succeeded or failed gracefully
    finally:
        # Clean up - restore permissions
        readonly_dir.chmod(0o755)


def test_save_drift_cache_atomic_write(
    tmp_path: Path,
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test save_drift_cache_to_disk uses atomic write."""
    from src.llm import check_drift

    clear_drift_cache()

    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_drift_check_no_drift
    mock_program_class.from_defaults.return_value = mock_program

    # Add entry to cache
    check_drift(llm=mock_llm_client, context="test", current_doc="doc")

    cache_file = tmp_path / "cache.json"

    # Save cache
    save_drift_cache_to_disk(str(cache_file))

    # Verify cache file exists and temp file is gone
    assert cache_file.exists()
    temp_file = cache_file.with_suffix(".tmp")
    assert not temp_file.exists()

    # Verify cache file is valid JSON
    data = json.loads(cache_file.read_text())
    assert "version" in data
    assert "entries" in data
