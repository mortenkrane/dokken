"""Tests for src/cache.py"""

from typing import Any

from pytest_mock import MockerFixture

from src.cache import (
    DRIFT_CACHE_SIZE,
    _generate_cache_key,
    _hash_content,
    clear_drift_cache,
    get_drift_cache_info,
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
