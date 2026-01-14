"""Tests for src/cache.py"""

import json
from pathlib import Path

import pytest
from llama_index.core.llms import LLM
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
from src.llm import check_drift
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
    mock_llm_client: LLM,
) -> None:
    """Test _generate_cache_key includes LLM model in the cache key."""
    # Mock LLM with model attribute
    mock_llm_client.model = "claude-3-5-haiku-20241022"  # type: ignore[attr-defined]

    key1 = _generate_cache_key("context", "doc", mock_llm_client)

    # Key should include model identifier
    assert "claude-3-5-haiku-20241022" in key1

    # Different model should produce different key
    mock_llm_client.model = "gpt-4o-mini"  # type: ignore[attr-defined]
    key2 = _generate_cache_key("context", "doc", mock_llm_client)

    assert key1 != key2
    assert "gpt-4o-mini" in key2


def test_clear_drift_cache_removes_all_entries(
    mocker: MockerFixture,
    mock_llm_client: LLM,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test clear_drift_cache removes all cached entries."""
    clear_drift_cache()

    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
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
    mock_llm_client: LLM,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test get_drift_cache_info returns accurate cache statistics."""
    clear_drift_cache()

    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
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


@pytest.mark.parametrize(
    "file_setup,description",
    [
        (None, "missing file"),
        ("invalid json{{{", "corrupted file"),
        (
            {
                "version": 999,
                "entries": {"key": {"drift_detected": True, "rationale": "Test"}},
            },
            "invalid version",
        ),
    ],
)
def test_load_handles_errors(
    tmp_path: Path, file_setup: object, description: str
) -> None:
    """Test load_drift_cache_from_disk handles various error conditions gracefully."""
    clear_drift_cache()

    cache_file = tmp_path / "test_cache.json"

    # Setup file based on test case
    if file_setup is None:
        # Don't create the file (missing file case)
        pass
    elif isinstance(file_setup, str):
        # Corrupted file case
        cache_file.write_text(file_setup)
    elif isinstance(file_setup, dict):
        # Invalid version case
        cache_file.write_text(json.dumps(file_setup))

    # Should not raise error, cache should be empty
    load_drift_cache_from_disk(str(cache_file))

    cache_info = get_drift_cache_info()
    assert cache_info["size"] == 0


def test_save_and_load_roundtrip(
    tmp_path: Path,
    mocker: MockerFixture,
    mock_llm_client: LLM,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test save and load cache roundtrip preserves data."""
    clear_drift_cache()

    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
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
    mock_llm_client: LLM,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test set_cache_max_size updates the maximum cache size."""
    clear_drift_cache()

    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
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
    mock_llm_client: LLM,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test save_drift_cache_to_disk creates parent directories."""
    clear_drift_cache()

    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
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
    mock_llm_client: LLM,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test save_drift_cache_to_disk handles OSError gracefully."""
    clear_drift_cache()

    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_drift_check_no_drift
    mock_program_class.from_defaults.return_value = mock_program

    # Add entry to cache
    check_drift(llm=mock_llm_client, context="test", current_doc="doc")

    # Mock Path.write_text to raise OSError
    mock_path = mocker.patch("src.cache.Path")
    mock_path_instance = mocker.MagicMock()
    mock_path.return_value = mock_path_instance
    mock_path_instance.with_suffix.return_value.write_text.side_effect = OSError(
        "Permission denied"
    )

    # Should not raise exception, just silently fail
    save_drift_cache_to_disk("/some/path/cache.json")  # Should not crash


def test_save_drift_cache_atomic_write(
    tmp_path: Path,
    mocker: MockerFixture,
    mock_llm_client: LLM,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test save_drift_cache_to_disk uses atomic write."""
    clear_drift_cache()

    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
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
