"""Tests for src/llm.py"""

import os
from typing import Any

import pytest
from pytest_mock import MockerFixture

from src.llm import TEMPERATURE, check_drift, generate_doc, initialize_llm
from src.records import DocumentationDriftCheck, ModuleDocumentation

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


def test_check_drift_creates_program(
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test check_drift creates LLMTextCompletionProgram with correct parameters."""
    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_drift_check_no_drift
    mock_program_class.from_defaults.return_value = mock_program

    context = "Sample code context"
    current_doc = "Sample documentation"

    result = check_drift(llm=mock_llm_client, context=context, current_doc=current_doc)

    # Verify program was created with correct parameters
    mock_program_class.from_defaults.assert_called_once()
    call_kwargs = mock_program_class.from_defaults.call_args[1]
    assert call_kwargs["llm"] == mock_llm_client
    assert "prompt_template_str" in call_kwargs

    # Verify program was called with correct arguments
    mock_program.assert_called_once_with(context=context, current_doc=current_doc)
    assert result == sample_drift_check_no_drift


def test_check_drift_uses_drift_check_prompt(
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test check_drift uses DRIFT_CHECK_PROMPT template."""
    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_drift_check_no_drift
    mock_program_class.from_defaults.return_value = mock_program

    check_drift(llm=mock_llm_client, context="ctx", current_doc="doc")

    call_kwargs = mock_program_class.from_defaults.call_args[1]
    prompt = call_kwargs["prompt_template_str"]

    # Verify it's using the drift check prompt
    assert "Documentation Drift Detector" in prompt
    assert "{context}" in prompt or "context" in str(mock_program.call_args)
    assert "{current_doc}" in prompt or "current_doc" in str(mock_program.call_args)


def test_check_drift_returns_drift_check_object(
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_drift_check_with_drift: DocumentationDriftCheck,
) -> None:
    """Test check_drift returns DocumentationDriftCheck object."""
    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_drift_check_with_drift
    mock_program_class.from_defaults.return_value = mock_program

    result = check_drift(llm=mock_llm_client, context="ctx", current_doc="doc")

    assert result == sample_drift_check_with_drift
    assert result.drift_detected is True


def test_generate_doc_creates_program(
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test generate_doc creates LLMTextCompletionProgram with correct parameters."""
    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_component_documentation
    mock_program_class.from_defaults.return_value = mock_program

    context = "Sample code context"

    result = generate_doc(llm=mock_llm_client, context=context)

    # Verify program was created with correct parameters
    mock_program_class.from_defaults.assert_called_once()
    call_kwargs = mock_program_class.from_defaults.call_args[1]
    assert call_kwargs["llm"] == mock_llm_client
    assert "prompt_template_str" in call_kwargs

    # Verify program was called with correct arguments
    mock_program.assert_called_once_with(context=context, human_intent_section="")
    assert result == sample_component_documentation


def test_generate_doc_uses_generation_prompt(
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test generate_doc uses DOCUMENTATION_GENERATION_PROMPT template."""
    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_component_documentation
    mock_program_class.from_defaults.return_value = mock_program

    generate_doc(llm=mock_llm_client, context="ctx")

    call_kwargs = mock_program_class.from_defaults.call_args[1]
    prompt = call_kwargs["prompt_template_str"]

    # Verify it's using the documentation generation prompt
    assert "technical writer" in prompt
    assert "{context}" in prompt or "context" in str(mock_program.call_args)


def test_generate_doc_returns_component_documentation(
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test generate_doc returns ModuleDocumentation object."""
    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_component_documentation
    mock_program_class.from_defaults.return_value = mock_program

    result = generate_doc(llm=mock_llm_client, context="ctx")

    assert result == sample_component_documentation
    assert isinstance(result, ModuleDocumentation)
    assert result.component_name == "Sample Component"
    assert result.key_design_decisions


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

    result = check_drift(llm=mock_llm_client, context=context, current_doc=current_doc)

    # Verify the program was called with the provided inputs
    mock_program.assert_called_once_with(context=context, current_doc=current_doc)
    assert result is not None


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

    result = generate_doc(llm=mock_llm_client, context=context)

    # Verify the program was called with the provided context
    mock_program.assert_called_once_with(context=context, human_intent_section="")
    assert result is not None


def test_generate_doc_with_human_intent(
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test generate_doc includes human intent when provided."""
    from src.records import HumanIntent

    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_component_documentation
    mock_program_class.from_defaults.return_value = mock_program

    human_intent = HumanIntent(
        problems_solved="Handles user authentication",
        core_responsibilities="Login and registration",
        non_responsibilities="Payment processing",
        system_context="Part of auth system",
    )

    result = generate_doc(
        llm=mock_llm_client, context="test context", human_intent=human_intent
    )

    # Verify the program was called with human intent section
    call_args = mock_program.call_args
    assert call_args is not None
    assert "context" in call_args.kwargs
    assert "human_intent_section" in call_args.kwargs

    # Verify the human intent section contains the expected content
    intent_section = call_args.kwargs["human_intent_section"]
    assert "HUMAN-PROVIDED CONTEXT" in intent_section
    assert "Handles user authentication" in intent_section
    assert "Login and registration" in intent_section
    assert "Payment processing" in intent_section
    assert "Part of auth system" in intent_section

    assert result == sample_component_documentation


def test_generate_doc_with_partial_human_intent(
    mocker: MockerFixture,
    mock_llm_client: Any,
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test generate_doc handles partial human intent."""
    from src.records import HumanIntent

    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_component_documentation
    mock_program_class.from_defaults.return_value = mock_program

    # Only provide some fields
    human_intent = HumanIntent(
        problems_solved="Handles authentication", core_responsibilities="User login"
    )

    result = generate_doc(
        llm=mock_llm_client, context="test context", human_intent=human_intent
    )

    # Verify the program was called with human intent section
    call_args = mock_program.call_args
    assert call_args is not None
    intent_section = call_args.kwargs["human_intent_section"]

    # Should include provided fields
    assert "Handles authentication" in intent_section
    assert "User login" in intent_section

    # Should not include empty fields
    assert "Non-Responsibilities" not in intent_section

    assert result == sample_component_documentation
