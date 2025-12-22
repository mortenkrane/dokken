"""LLM client initialization and operations."""

import os

from llama_index.core.llms import LLM
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.llms.anthropic import Anthropic
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.llms.openai import OpenAI
from pydantic import BaseModel

from src.config import CustomPrompts
from src.doc_types import DocType
from src.prompts import DRIFT_CHECK_PROMPT
from src.records import (
    DocumentationDriftCheck,
)

# Temperature setting for deterministic, reproducible documentation output
TEMPERATURE = 0.0


def initialize_llm() -> LLM:
    """
    Initializes the LLM client based on available API keys.

    Checks for API keys in the following priority order:
    1. ANTHROPIC_API_KEY -> Claude (claude-3-5-haiku-20241022)
    2. OPENAI_API_KEY -> OpenAI (gpt-4o-mini)
    3. GOOGLE_API_KEY -> Google Gemini (gemini-2.5-flash)

    Returns:
        LLM: The initialized LLM client.

    Raises:
        ValueError: If no API key is found.
    """
    # Check for Anthropic/Claude API key
    if os.getenv("ANTHROPIC_API_KEY"):
        # Using Claude 3.5 Haiku for fast, cost-effective structured output
        return Anthropic(model="claude-3-5-haiku-20241022", temperature=TEMPERATURE)

    # Check for OpenAI API key
    if os.getenv("OPENAI_API_KEY"):
        # Using GPT-4o-mini for good balance of speed, cost, and quality
        return OpenAI(model="gpt-4o-mini", temperature=TEMPERATURE)

    # Check for Google API key
    if os.getenv("GOOGLE_API_KEY"):
        # Using Gemini-2.5-Flash for speed, cost, and context balance
        return GoogleGenAI(model="gemini-2.5-flash", temperature=TEMPERATURE)

    raise ValueError(
        "No API key found. Please set one of the following environment variables:\n"
        "  - ANTHROPIC_API_KEY (for Claude)\n"
        "  - OPENAI_API_KEY (for OpenAI)\n"
        "  - GOOGLE_API_KEY (for Google Gemini)"
    )


def check_drift(*, llm: LLM, context: str, current_doc: str) -> DocumentationDriftCheck:
    """
    Analyzes the current documentation against the code changes to detect drift.

    Args:
        llm: The LLM client instance.
        context: The code context and diff.
        current_doc: The current documentation content.

    Returns:
        A DocumentationDriftCheck object with drift detection results.
    """
    # Use LLMTextCompletionProgram for structured Pydantic output
    check_program = LLMTextCompletionProgram.from_defaults(
        output_cls=DocumentationDriftCheck,
        llm=llm,
        prompt_template_str=DRIFT_CHECK_PROMPT,
    )

    # Run the check
    return check_program(context=context, current_doc=current_doc)


def _build_human_intent_section(
    human_intent: BaseModel,
) -> str:
    """
    Builds a formatted string from human intent data.

    Args:
        human_intent: The intent model containing user responses.

    Returns:
        Formatted string with human-provided context, or empty string if no data.
    """
    intent_lines = [
        f"{key.replace('_', ' ').title()}: {value}"
        for key, value in human_intent.model_dump().items()
        if value is not None
    ]

    if not intent_lines:
        return ""

    return "\n--- HUMAN-PROVIDED CONTEXT ---\n" + "\n".join(intent_lines) + "\n"


def _get_doc_type_prompt(
    custom_prompts: CustomPrompts, doc_type: DocType
) -> str | None:
    """Get the doc-type-specific custom prompt."""
    if doc_type == DocType.MODULE_README:
        return custom_prompts.module_readme
    if doc_type == DocType.PROJECT_README:
        return custom_prompts.project_readme
    if doc_type == DocType.STYLE_GUIDE:
        return custom_prompts.style_guide
    return None


def _build_custom_prompt_section(
    custom_prompts: CustomPrompts | None,
    doc_type: DocType | None,
) -> str:
    """
    Builds a formatted string from custom prompts configuration.

    Args:
        custom_prompts: The custom prompts configuration from .dokken.toml.
        doc_type: The documentation type being generated.

    Returns:
        Formatted string with custom prompt instructions, or empty string if none.
    """
    if custom_prompts is None:
        return ""

    prompt_parts = []

    # Add global custom prompt if present
    if custom_prompts.global_prompt:
        prompt_parts.append(custom_prompts.global_prompt)

    # Add doc-type-specific custom prompt if present
    if doc_type is not None:
        doc_type_prompt = _get_doc_type_prompt(custom_prompts, doc_type)
        if doc_type_prompt:
            prompt_parts.append(doc_type_prompt)

    if not prompt_parts:
        return ""

    return "\n--- USER PREFERENCES ---\n" + "\n\n".join(prompt_parts) + "\n"


def _build_drift_context_section(
    drift_rationale: str,
) -> str:
    """
    Builds a formatted string from drift detection rationale.

    The returned string includes educational context explaining what documentation
    drift is and explicit instructions for the LLM to address the detected issues.
    This verbose approach improves generation quality by ensuring the LLM
    understands both the concept of drift and the specific problems to fix.

    Args:
        drift_rationale: The rationale explaining what drift was detected.

    Returns:
        Formatted string with drift detection context, ready to append to code context.
    """
    return (
        "\n--- DETECTED DOCUMENTATION DRIFT ---\n"
        "Documentation drift occurs when code changes but documentation doesn't, "
        "causing the docs to become outdated or inaccurate. An automated analysis "
        "has detected the following specific drift issues between the current "
        "documentation and the actual code:\n\n"
        f"{drift_rationale}\n\n"
        "IMPORTANT: Your task is to generate updated documentation that "
        "addresses these specific drift issues. Make sure the new documentation "
        "accurately reflects the current code state and resolves each of the "
        "concerns listed above.\n"
    )


def generate_doc(  # noqa: PLR0913
    *,
    llm: LLM,
    context: str,
    human_intent: BaseModel | None = None,
    drift_rationale: str | None = None,
    custom_prompts: CustomPrompts | None = None,
    doc_type: DocType | None = None,
    output_model: type[BaseModel],
    prompt_template: str,
) -> BaseModel:
    """
    Generates structured documentation based on code context.

    Args:
        llm: The LLM client instance.
        context: The code context to generate documentation from.
        human_intent: Optional human-provided intent and context.
        drift_rationale: Optional drift detection rationale explaining what
            needs to be fixed.
        custom_prompts: Optional custom prompts from configuration.
        doc_type: Optional documentation type for doc-type-specific prompts.
        output_model: Pydantic model class for structured output.
        prompt_template: Prompt template string to use.

    Returns:
        An instance of output_model with structured documentation data.
    """
    # Build human intent section if provided
    human_intent_section = (
        _build_human_intent_section(human_intent) if human_intent else ""
    )

    # Build custom prompt section if provided
    custom_prompt_section = _build_custom_prompt_section(custom_prompts, doc_type)

    # Build drift context section if provided
    drift_context_section = (
        _build_drift_context_section(drift_rationale) if drift_rationale else ""
    )

    # Combine all sections for the prompt
    combined_context = context + drift_context_section
    combined_intent_section = human_intent_section + custom_prompt_section

    # Use LLMTextCompletionProgram for structured Pydantic output
    generate_program = LLMTextCompletionProgram.from_defaults(
        output_cls=output_model,
        llm=llm,
        prompt_template_str=prompt_template,
    )

    # Run the generation
    return generate_program(
        context=combined_context, human_intent_section=combined_intent_section
    )
