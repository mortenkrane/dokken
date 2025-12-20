"""LLM client initialization and operations."""

import os

from llama_index.core.llms import LLM
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.llms.anthropic import Anthropic
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.llms.openai import OpenAI
from pydantic import BaseModel

from src.prompts import DRIFT_CHECK_PROMPT
from src.records import (
    DocumentationDriftCheck,
    ModuleIntent,
    ProjectIntent,
    StyleGuideIntent,
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
    human_intent: ModuleIntent | ProjectIntent | StyleGuideIntent,
) -> str:
    """
    Builds a formatted string from human intent data.

    Args:
        human_intent: The intent model containing user responses.

    Returns:
        Formatted string with human-provided context, or empty string if no data.
    """
    # Get all fields from the intent model
    intent_dict = human_intent.model_dump()

    # Build formatted lines for non-null values
    intent_lines = []
    for key, value in intent_dict.items():
        if value is not None:
            # Convert snake_case to Title Case
            label = key.replace("_", " ").title()
            intent_lines.append(f"{label}: {value}")

    if not intent_lines:
        return ""

    return "\n--- HUMAN-PROVIDED CONTEXT ---\n" + "\n".join(intent_lines) + "\n"


def generate_doc(
    *,
    llm: LLM,
    context: str,
    human_intent: ModuleIntent | ProjectIntent | StyleGuideIntent | None = None,
    output_model: type[BaseModel],
    prompt_template: str,
) -> BaseModel:
    """
    Generates structured documentation based on code context.

    Args:
        llm: The LLM client instance.
        context: The code context to generate documentation from.
        human_intent: Optional human-provided intent and context.
        output_model: Pydantic model class for structured output.
        prompt_template: Prompt template string to use.

    Returns:
        An instance of output_model with structured documentation data.
    """
    # Build human intent section if provided
    human_intent_section = (
        _build_human_intent_section(human_intent) if human_intent else ""
    )

    # Use LLMTextCompletionProgram for structured Pydantic output
    generate_program = LLMTextCompletionProgram.from_defaults(
        output_cls=output_model,
        llm=llm,
        prompt_template_str=prompt_template,
    )

    # Run the generation
    return generate_program(context=context, human_intent_section=human_intent_section)
