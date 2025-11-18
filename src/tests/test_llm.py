"""Tests for src/llm.py"""

import os

import pytest

from src.llm import check_drift, generate_doc, initialize_llm


def test_initialize_llm_success(mocker):
    """Test initialize_llm creates GoogleGenAI client with correct parameters."""
    mocker.patch.dict(os.environ, {"GOOGLE_API_KEY": "test_api_key"})
    mock_genai = mocker.patch("src.llm.GoogleGenAI")

    llm = initialize_llm()

    mock_genai.assert_called_once_with(model="gemini-2.5-flash", temperature=0.0)
    assert llm == mock_genai.return_value


def test_initialize_llm_missing_api_key(mocker):
    """Test initialize_llm raises ValueError when GOOGLE_API_KEY is missing."""
    mocker.patch.dict(os.environ, {}, clear=True)

    with pytest.raises(ValueError, match="GOOGLE_API_KEY environment variable not set"):
        initialize_llm()


@pytest.mark.parametrize(
    "api_key",
    ["key123", "test_key_xyz", "AIzaSyABC123"],
)
def test_initialize_llm_with_various_keys(mocker, api_key):
    """Test initialize_llm works with various API key formats."""
    mocker.patch.dict(os.environ, {"GOOGLE_API_KEY": api_key})
    mock_genai = mocker.patch("src.llm.GoogleGenAI")

    initialize_llm()

    mock_genai.assert_called_once()


def test_check_drift_creates_program(
    mocker, mock_llm_client, sample_drift_check_no_drift
):
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
    mocker, mock_llm_client, sample_drift_check_no_drift
):
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
    mocker, mock_llm_client, sample_drift_check_with_drift
):
    """Test check_drift returns DocumentationDriftCheck object."""
    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_drift_check_with_drift
    mock_program_class.from_defaults.return_value = mock_program

    result = check_drift(llm=mock_llm_client, context="ctx", current_doc="doc")

    assert result == sample_drift_check_with_drift
    assert result.drift_detected is True


def test_generate_doc_creates_program(
    mocker, mock_llm_client, sample_component_documentation
):
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
    mock_program.assert_called_once_with(context=context)
    assert result == sample_component_documentation


def test_generate_doc_uses_generation_prompt(
    mocker, mock_llm_client, sample_component_documentation
):
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
    mocker, mock_llm_client, sample_component_documentation
):
    """Test generate_doc returns ComponentDocumentation object."""
    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_component_documentation
    mock_program_class.from_defaults.return_value = mock_program

    result = generate_doc(llm=mock_llm_client, context="ctx")

    assert result == sample_component_documentation
    assert result.component_name == "Sample Component"
    assert result.design_decisions


@pytest.mark.parametrize(
    "context,current_doc",
    [
        ("short context", "short doc"),
        ("a" * 1000, "b" * 1000),
        ("context with\nnewlines", "doc with\nnewlines"),
    ],
)
def test_check_drift_handles_various_inputs(
    mocker, mock_llm_client, sample_drift_check_no_drift, context, current_doc
):
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
    mocker, mock_llm_client, sample_component_documentation, context
):
    """Test generate_doc handles various code contexts."""
    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_component_documentation
    mock_program_class.from_defaults.return_value = mock_program

    result = generate_doc(llm=mock_llm_client, context=context)

    # Verify the program was called with the provided context
    mock_program.assert_called_once_with(context=context)
    assert result is not None
