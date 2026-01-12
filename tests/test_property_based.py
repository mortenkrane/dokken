"""Property-based tests using Hypothesis to discover edge cases.

This module uses Hypothesis to automatically generate test cases and verify
invariants across key components of Dokken:
- Markdown parsing/reconstruction (parse_sections idempotency, never crashes)
- Cache key generation (determinism, format validation, uniqueness)
- Drift detection robustness (never crashes, handles None/empty/large inputs)

Note: Config merging and file path tests are in their respective test files
to avoid circular import issues.
"""

from hypothesis import HealthCheck, given, settings, strategies as st
from llama_index.core.llms import LLM
from pytest_mock import MockerFixture

from src.cache import _generate_cache_key, _hash_content
from src.llm import check_drift
from src.output import parse_sections
from src.records import DocumentationDriftCheck

# ============================================================================
# Markdown Parsing Properties
# ============================================================================


@given(st.text())
@settings(max_examples=100)
def test_parse_sections_never_crashes(markdown: str) -> None:
    """Parsing should never crash, regardless of input."""
    result = parse_sections(markdown)
    assert isinstance(result, dict)
    # All keys should be strings
    assert all(isinstance(k, str) for k in result)
    # All values should be strings
    assert all(isinstance(v, str) for v in result.values())


@given(st.text())
@settings(max_examples=100)
def test_parse_sections_preserves_content_length(markdown: str) -> None:
    """Parsing and reconstructing should preserve approximately the same length.

    While the exact format may change (whitespace normalization), the total
    content length should be similar (within a reasonable margin).
    """
    sections = parse_sections(markdown)
    reconstructed_length = sum(len(content) for content in sections.values())

    # Allow for some variation due to newline normalization
    # but should be roughly same order of magnitude
    if markdown:
        # Reconstructed should be at least 50% of original (accounting for formatting)
        # and not more than 200% (accounting for added structure)
        assert 0.5 <= reconstructed_length / len(markdown) <= 2.0 or len(markdown) < 10


@given(st.text())
@settings(max_examples=100)
def test_parse_sections_idempotent(markdown: str) -> None:
    """Parsing twice should produce the same result (idempotent)."""
    sections1 = parse_sections(markdown)

    # Reconstruct the markdown from sections
    reconstructed_parts = [sections1["_preamble"]] if "_preamble" in sections1 else []

    for key, value in sections1.items():
        if key != "_preamble":
            reconstructed_parts.append(value)

    reconstructed = "\n\n".join(reconstructed_parts) if reconstructed_parts else ""

    # Parse again
    sections2 = parse_sections(reconstructed)

    # Should have same keys
    assert set(sections1.keys()) == set(sections2.keys())


@given(st.lists(st.text(min_size=1), min_size=1, max_size=10))
@settings(max_examples=50)
def test_parse_sections_with_multiple_sections(section_names: list[str]) -> None:
    """Test parsing documents with multiple generated sections."""
    # Create a markdown document with multiple sections
    parts = ["# Title\n"]
    for name in section_names:
        # Clean the name to avoid ## in content
        clean_name = name.replace("\n", " ").replace("#", "")
        parts.append(f"## {clean_name}\n\nContent for {clean_name}.")

    doc = "\n\n".join(parts)
    sections = parse_sections(doc)

    # Should parse without errors
    assert isinstance(sections, dict)
    # Should have at least one section or preamble
    assert len(sections) >= 1


# ============================================================================
# Cache Key Generation Properties
# ============================================================================


@given(st.text(), st.text())
@settings(max_examples=100)
def test_hash_content_deterministic(content1: str, content2: str) -> None:
    """Same content should always produce the same hash."""
    hash1a = _hash_content(content1)
    hash1b = _hash_content(content1)
    hash2a = _hash_content(content2)
    hash2b = _hash_content(content2)

    # Same content produces same hash
    assert hash1a == hash1b
    assert hash2a == hash2b

    # Different content should (with high probability) produce different hashes
    if content1 != content2:
        assert hash1a != hash2a


@given(st.text())
@settings(max_examples=100)
def test_hash_content_valid_format(content: str) -> None:
    """Hash should always be valid SHA256 format (64 hex chars)."""
    result = _hash_content(content)

    # Should be 64 characters
    assert len(result) == 64
    # Should be all hex characters
    assert all(c in "0123456789abcdef" for c in result)


@given(st.text(), st.text() | st.none())
def test_hash_content_handles_none(context: str, doc: str | None) -> None:
    """Hash functions should handle None values gracefully."""
    context_hash = _hash_content(context)
    doc_hash = _hash_content(doc)

    assert isinstance(context_hash, str)
    assert isinstance(doc_hash, str)
    assert len(context_hash) == 64
    assert len(doc_hash) == 64


@given(
    st.text(),
    st.text() | st.none(),
    # Exclude colons from model name to avoid ambiguity in cache key format
    st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters=":")),
)
@settings(max_examples=100)
def test_generate_cache_key_format(context: str, doc: str | None, model: str) -> None:
    """Cache key should have consistent format: hash:hash:model."""

    # Create a mock LLM with model attribute
    class MockLLM:
        def __init__(self, model_name: str):
            self.model = model_name

    llm = MockLLM(model)
    key = _generate_cache_key(context, doc, llm)  # type: ignore[arg-type]

    # Should have format "hash:hash:model"
    parts = key.split(":")
    assert len(parts) == 3

    # First two parts should be hashes (64 hex chars)
    assert len(parts[0]) == 64
    assert len(parts[1]) == 64
    assert all(c in "0123456789abcdef" for c in parts[0])
    assert all(c in "0123456789abcdef" for c in parts[1])

    # Last part should be model name
    assert parts[2] == model


@given(st.text(), st.text())
@settings(max_examples=100)
def test_generate_cache_key_different_contexts_different_keys(
    context1: str, context2: str
) -> None:
    """Different contexts should (usually) produce different cache keys."""

    class MockLLM:
        model = "test-model"

    llm = MockLLM()

    key1 = _generate_cache_key(context1, None, llm)  # type: ignore[arg-type]
    key2 = _generate_cache_key(context2, None, llm)  # type: ignore[arg-type]

    # Different contexts should produce different keys (with high probability)
    if context1 != context2:
        assert key1 != key2


# ============================================================================
# Drift Check Robustness Properties
# ============================================================================


@given(st.text(), st.text())
@settings(
    max_examples=30,
    deadline=2000,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_drift_check_never_crashes(
    mocker: MockerFixture,
    mock_llm_client: LLM,
    sample_drift_check_with_drift: DocumentationDriftCheck,
    code: str,
    doc: str,
) -> None:
    """Drift check should never crash, regardless of input."""
    # Mock the LLM program to return a valid drift check
    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_drift_check_with_drift
    mock_program_class.from_defaults.return_value = mock_program

    result = check_drift(llm=mock_llm_client, context=code, current_doc=doc)

    # Should always return valid DocumentationDriftCheck
    assert isinstance(result, DocumentationDriftCheck)
    assert isinstance(result.drift_detected, bool)
    assert isinstance(result.rationale, str)
    assert len(result.rationale) > 0


@given(st.text())
@settings(
    max_examples=30,
    deadline=2000,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_drift_check_handles_none_doc(
    mocker: MockerFixture,
    mock_llm_client: LLM,
    sample_drift_check_with_drift: DocumentationDriftCheck,
    code: str,
) -> None:
    """Drift check should handle None documentation gracefully."""
    # Mock the LLM program
    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_drift_check_with_drift
    mock_program_class.from_defaults.return_value = mock_program

    result = check_drift(llm=mock_llm_client, context=code, current_doc=None)

    # Should return valid result
    assert isinstance(result, DocumentationDriftCheck)
    assert isinstance(result.drift_detected, bool)

    # The prompt should have been called with "No existing documentation provided."
    call_kwargs = mock_program.call_args[1]
    assert "No existing documentation provided" in call_kwargs["current_doc"]


def test_drift_check_with_empty_strings(
    mocker: MockerFixture,
    mock_llm_client: LLM,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Drift check should handle empty strings correctly.

    Note: This is not a property-based test, but a regular test for
    specific edge cases with empty strings.
    """
    # Mock the LLM program
    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_drift_check_no_drift
    mock_program_class.from_defaults.return_value = mock_program

    # Test with empty context
    result1 = check_drift(llm=mock_llm_client, context="", current_doc="some doc")
    assert isinstance(result1, DocumentationDriftCheck)

    # Test with empty doc
    result2 = check_drift(llm=mock_llm_client, context="some code", current_doc="")
    assert isinstance(result2, DocumentationDriftCheck)

    # Test with both empty
    result3 = check_drift(llm=mock_llm_client, context="", current_doc="")
    assert isinstance(result3, DocumentationDriftCheck)


@given(st.text(min_size=1000, max_size=5000))
@settings(
    max_examples=10,
    deadline=2000,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_drift_check_with_large_inputs(
    mocker: MockerFixture,
    mock_llm_client: LLM,
    sample_drift_check_with_drift: DocumentationDriftCheck,
    large_text: str,
) -> None:
    """Drift check should handle large inputs correctly."""
    # Mock the LLM program
    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_drift_check_with_drift
    mock_program_class.from_defaults.return_value = mock_program

    result = check_drift(
        llm=mock_llm_client, context=large_text, current_doc=large_text
    )

    assert isinstance(result, DocumentationDriftCheck)
    assert isinstance(result.drift_detected, bool)
    assert isinstance(result.rationale, str)
