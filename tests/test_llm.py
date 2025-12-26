"""Tests for src/llm.py"""

import os
from typing import Any

import pytest
from pytest_mock import MockerFixture

from src.cache import get_drift_cache_info
from src.llm import (
    TEMPERATURE,
    GenerationConfig,
    check_drift,
    generate_doc,
    initialize_llm,
)
from src.prompts import MODULE_GENERATION_PROMPT
from src.records import DocumentationDriftCheck, ModuleDocumentation, ModuleIntent

# --- Tests for initialize_llm() ---


def test_initialize_llm_with_anthropic_key(mocker: MockerFixture) -> None:
    """Test initialize_llm creates Anthropic client when ANTHROPIC_API_KEY is set."""
    mocker.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_api_key"}, clear=True)
    mock_anthropic = mocker.patch("src.llm.Anthropic")

    llm = initialize_llm()

    mock_anthropic.assert_called_once_with(
        model="claude-3-5-haiku-20241022", temperature=TEMPERATURE
    )
    assert llm == mock_anthropic.return_value


def test_initialize_llm_with_openai_key(mocker: MockerFixture) -> None:
    """Test initialize_llm creates OpenAI client when OPENAI_API_KEY is set."""
    mocker.patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"}, clear=True)
    mock_openai = mocker.patch("src.llm.OpenAI")

    llm = initialize_llm()

    mock_openai.assert_called_once_with(model="gpt-4o-mini", temperature=TEMPERATURE)
    assert llm == mock_openai.return_value


def test_initialize_llm_with_google_key(mocker: MockerFixture) -> None:
    """Test initialize_llm creates GoogleGenAI client when GOOGLE_API_KEY is set."""
    mocker.patch.dict(os.environ, {"GOOGLE_API_KEY": "test_api_key"}, clear=True)
    mock_genai = mocker.patch("src.llm.GoogleGenAI")

    llm = initialize_llm()

    mock_genai.assert_called_once_with(
        model="gemini-2.5-flash", temperature=TEMPERATURE
    )
    assert llm == mock_genai.return_value


def test_initialize_llm_priority_order(mocker: MockerFixture) -> None:
    """Test initialize_llm prioritizes Anthropic > OpenAI > Google."""
    # Set all three API keys
    mocker.patch.dict(
        os.environ,
        {
            "ANTHROPIC_API_KEY": "anthropic_key",
            "OPENAI_API_KEY": "openai_key",
            "GOOGLE_API_KEY": "google_key",
        },
        clear=True,
    )
    mock_anthropic = mocker.patch("src.llm.Anthropic")
    mock_openai = mocker.patch("src.llm.OpenAI")
    mock_genai = mocker.patch("src.llm.GoogleGenAI")

    llm = initialize_llm()

    # Should use Anthropic (highest priority)
    mock_anthropic.assert_called_once()
    mock_openai.assert_not_called()
    mock_genai.assert_not_called()
    assert llm == mock_anthropic.return_value


def test_initialize_llm_openai_priority_over_google(mocker: MockerFixture) -> None:
    """Test initialize_llm prioritizes OpenAI over Google when both keys are set."""
    mocker.patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "openai_key", "GOOGLE_API_KEY": "google_key"},
        clear=True,
    )
    mock_openai = mocker.patch("src.llm.OpenAI")
    mock_genai = mocker.patch("src.llm.GoogleGenAI")

    llm = initialize_llm()

    # Should use OpenAI (higher priority than Google)
    mock_openai.assert_called_once()
    mock_genai.assert_not_called()
    assert llm == mock_openai.return_value


def test_initialize_llm_missing_all_api_keys(mocker: MockerFixture) -> None:
    """Test initialize_llm raises ValueError when no API keys are set."""
    mocker.patch.dict(os.environ, {}, clear=True)

    with pytest.raises(
        ValueError,
        match=r"No API key found\.",
    ):
        initialize_llm()


@pytest.mark.parametrize(
    "env_var,api_key",
    [
        ("ANTHROPIC_API_KEY", "sk-ant-api03-test"),
        ("OPENAI_API_KEY", "sk-test123"),
        ("GOOGLE_API_KEY", "AIzaSyABC123"),
    ],
)
def test_initialize_llm_with_various_key_formats(
    mocker: MockerFixture, env_var: str, api_key: str
) -> None:
    """Test initialize_llm works with various API key formats."""
    mocker.patch.dict(os.environ, {env_var: api_key}, clear=True)

    if env_var == "ANTHROPIC_API_KEY":
        mocker.patch("src.llm.Anthropic")
    elif env_var == "OPENAI_API_KEY":
        mocker.patch("src.llm.OpenAI")
    else:
        mocker.patch("src.llm.GoogleGenAI")

    llm = initialize_llm()
    assert llm is not None


# --- Tests for check_drift() ---


def test_check_drift_detects_drift_when_functions_removed(
    mocker: MockerFixture,
    mock_llm_client: Any,
) -> None:
    """Test check_drift detects drift when documented functions are removed."""
    # Mock the LLM program to return drift detected
    drift_result = DocumentationDriftCheck(
        drift_detected=True,
        rationale=(
            "Function 'create_session()' is documented but no longer exists in code."
        ),
    )

    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = drift_result
    mock_program_class.from_defaults.return_value = mock_program

    # Given: Code without create_session function
    code = "def authenticate_user(): pass"
    # And: Documentation that mentions create_session
    doc = "## Functions\n- create_session() - Creates user sessions"

    # When: Checking drift
    result = check_drift(llm=mock_llm_client, context=code, current_doc=doc)

    # Then: Drift should be detected
    assert result.drift_detected is True
    assert "create_session()" in result.rationale


def test_check_drift_no_drift_when_code_matches_docs(
    mocker: MockerFixture,
    mock_llm_client: Any,
) -> None:
    """Test check_drift returns no drift when code matches documentation."""
    # Mock the LLM program to return no drift
    no_drift_result = DocumentationDriftCheck(
        drift_detected=False, rationale="Documentation is up-to-date."
    )

    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = no_drift_result
    mock_program_class.from_defaults.return_value = mock_program

    # Given: Code and documentation that match
    code = "def process_payment(): pass"
    doc = "## Functions\n- process_payment() - Processes payments"

    # When: Checking drift
    result = check_drift(llm=mock_llm_client, context=code, current_doc=doc)

    # Then: No drift should be detected
    assert result.drift_detected is False
    assert "up-to-date" in result.rationale


def test_check_drift_detects_new_functions_added(
    mocker: MockerFixture,
    mock_llm_client: Any,
) -> None:
    """Test check_drift detects when new functions are added to code."""
    # Mock the LLM program to return drift detected
    drift_result = DocumentationDriftCheck(
        drift_detected=True,
        rationale=(
            "New function 'generate_token()' exists in code but is not documented."
        ),
    )

    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = drift_result
    mock_program_class.from_defaults.return_value = mock_program

    # Given: Code with new function
    code = "def authenticate_user(): pass\ndef generate_token(): pass"
    # And: Documentation without generate_token
    doc = "## Functions\n- authenticate_user() - Authenticates users"

    # When: Checking drift
    result = check_drift(llm=mock_llm_client, context=code, current_doc=doc)

    # Then: Drift should be detected
    assert result.drift_detected is True
    assert "generate_token()" in result.rationale


# --- Tests for check_drift with caching ---


def test_check_drift_cache_hit(
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test check_drift returns cached result on cache hit."""

    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_drift_check_no_drift
    mock_program_class.from_defaults.return_value = mock_program

    context = "Sample context"
    doc = "Sample doc"

    # First call should trigger LLM
    result1 = check_drift(llm=mock_llm_client, context=context, current_doc=doc)
    assert result1 == sample_drift_check_no_drift
    assert mock_program_class.from_defaults.call_count == 1

    # Second call with same inputs should use cache
    result2 = check_drift(llm=mock_llm_client, context=context, current_doc=doc)
    assert result2 == sample_drift_check_no_drift
    # LLM should not be called again
    assert mock_program_class.from_defaults.call_count == 1

    # Verify both results are identical
    assert result1.drift_detected == result2.drift_detected
    assert result1.rationale == result2.rationale


def test_check_drift_cache_miss_on_different_context(
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test check_drift triggers new LLM call when context changes."""

    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_drift_check_no_drift
    mock_program_class.from_defaults.return_value = mock_program

    # First call
    check_drift(llm=mock_llm_client, context="context1", current_doc="doc")
    assert mock_program_class.from_defaults.call_count == 1

    # Different context should trigger new LLM call
    check_drift(llm=mock_llm_client, context="context2", current_doc="doc")
    assert mock_program_class.from_defaults.call_count == 2


def test_check_drift_cache_miss_on_different_doc(
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test check_drift triggers new LLM call when documentation changes."""

    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_drift_check_no_drift
    mock_program_class.from_defaults.return_value = mock_program

    # First call
    check_drift(llm=mock_llm_client, context="context", current_doc="doc1")
    assert mock_program_class.from_defaults.call_count == 1

    # Different doc should trigger new LLM call
    check_drift(llm=mock_llm_client, context="context", current_doc="doc2")
    assert mock_program_class.from_defaults.call_count == 2


def test_check_drift_cache_evicts_oldest_when_full(
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test cache evicts oldest entry when maxsize is reached."""

    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_drift_check_no_drift
    mock_program_class.from_defaults.return_value = mock_program

    # Temporarily reduce cache size for testing using mocker.patch
    mocker.patch("src.cache.DRIFT_CACHE_SIZE", 2)

    # Fill cache to limit
    check_drift(llm=mock_llm_client, context="ctx1", current_doc="doc1")
    check_drift(llm=mock_llm_client, context="ctx2", current_doc="doc2")

    cache_info = get_drift_cache_info()
    assert cache_info["size"] == 2

    # Add one more entry - should evict oldest
    check_drift(llm=mock_llm_client, context="ctx3", current_doc="doc3")

    cache_info = get_drift_cache_info()
    assert cache_info["size"] == 2  # Still at max size

    # First entry should be evicted, so accessing it should trigger new LLM call
    # Reset call count
    mock_program_class.from_defaults.reset_mock()

    # Access first entry again (should be evicted)
    check_drift(llm=mock_llm_client, context="ctx1", current_doc="doc1")
    assert mock_program_class.from_defaults.call_count == 1  # New call

    # Access third entry (should still be cached)
    mock_program_class.from_defaults.reset_mock()
    check_drift(llm=mock_llm_client, context="ctx3", current_doc="doc3")
    assert mock_program_class.from_defaults.call_count == 0  # Cached


# --- Tests for generate_doc() ---


def test_generate_doc_returns_structured_documentation(
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test generate_doc returns structured ModuleDocumentation."""
    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_component_documentation
    mock_program_class.from_defaults.return_value = mock_program

    # Given: A code context for a payment module
    context = "def process_payment(): pass\ndef validate_payment(): pass"

    # When: Generating documentation
    result = generate_doc(
        llm=mock_llm_client,
        context=context,
        output_model=ModuleDocumentation,
        prompt_template=MODULE_GENERATION_PROMPT,
    )

    # Then: Should return structured documentation
    assert isinstance(result, ModuleDocumentation)
    assert result.component_name == "Sample Component"
    assert result.purpose_and_scope
    assert result.architecture_overview
    assert result.key_design_decisions


def test_generate_doc_without_human_intent(
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test generate_doc works without human intent provided."""
    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_component_documentation
    mock_program_class.from_defaults.return_value = mock_program

    # Given: No human intent (config=None)
    context = "def authenticate(): pass"

    # When: Generating documentation
    result = generate_doc(
        llm=mock_llm_client,
        context=context,
        config=None,
        output_model=ModuleDocumentation,
        prompt_template=MODULE_GENERATION_PROMPT,
    )

    # Then: Should still generate valid documentation
    assert isinstance(result, ModuleDocumentation)
    assert result.component_name
    assert result.purpose_and_scope


@pytest.mark.parametrize(
    "context,current_doc",
    [
        ("short context", "short doc"),
        ("a" * 1000, "b" * 1000),
        ("context with\nnewlines", "doc with\nnewlines"),
    ],
)
def test_check_drift_handles_various_inputs(
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_drift_check_no_drift: DocumentationDriftCheck,
    context: str,
    current_doc: str,
) -> None:
    """Test check_drift handles various context and documentation inputs."""
    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_drift_check_no_drift
    mock_program_class.from_defaults.return_value = mock_program

    # When: Checking drift with various inputs
    result = check_drift(llm=mock_llm_client, context=context, current_doc=current_doc)

    # Then: Should return valid drift check result
    assert isinstance(result, DocumentationDriftCheck)
    assert isinstance(result.drift_detected, bool)
    assert isinstance(result.rationale, str)


@pytest.mark.parametrize(
    "context",
    [
        "simple code",
        "def func():\n    pass",
        "import os\nimport sys\n\nclass Foo:\n    pass",
    ],
)
def test_generate_doc_handles_various_contexts(
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_component_documentation: ModuleDocumentation,
    context: str,
) -> None:
    """Test generate_doc handles various code contexts."""
    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_component_documentation
    mock_program_class.from_defaults.return_value = mock_program

    # When: Generating docs with various code contexts
    result = generate_doc(
        llm=mock_llm_client,
        context=context,
        output_model=ModuleDocumentation,
        prompt_template=MODULE_GENERATION_PROMPT,
    )

    # Then: Should return valid structured documentation
    assert isinstance(result, ModuleDocumentation)
    assert result.component_name
    assert result.purpose_and_scope


def test_generate_doc_with_human_intent(
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test generate_doc includes human intent when provided."""

    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_component_documentation
    mock_program_class.from_defaults.return_value = mock_program

    # Given: Human intent with specific guidance
    human_intent = ModuleIntent(
        problems_solved="Handles user authentication",
        core_responsibilities="Login and registration",
        non_responsibilities="Payment processing",
        system_context="Part of auth system",
    )
    config = GenerationConfig(human_intent=human_intent)

    # When: Generating documentation with human intent
    result = generate_doc(
        llm=mock_llm_client,
        context="def authenticate(): pass",
        config=config,
        output_model=ModuleDocumentation,
        prompt_template=MODULE_GENERATION_PROMPT,
    )

    # Then: Should return valid documentation
    assert isinstance(result, ModuleDocumentation)
    assert result.component_name
    assert result.purpose_and_scope


def test_generate_doc_with_partial_human_intent(
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test generate_doc handles partial human intent."""

    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_component_documentation
    mock_program_class.from_defaults.return_value = mock_program

    # Given: Partial human intent (only some fields provided)
    human_intent = ModuleIntent(
        problems_solved="Handles authentication", core_responsibilities="User login"
    )
    config = GenerationConfig(human_intent=human_intent)

    # When: Generating documentation
    result = generate_doc(
        llm=mock_llm_client,
        context="def authenticate(): pass",
        config=config,
        output_model=ModuleDocumentation,
        prompt_template=MODULE_GENERATION_PROMPT,
    )

    # Then: Should return valid documentation
    assert isinstance(result, ModuleDocumentation)
    assert result.component_name
    assert result.purpose_and_scope
