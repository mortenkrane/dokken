"""LLM client initialization and operations."""

import os

from llama_index.core.llms import LLM
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.llms.anthropic import Anthropic
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.llms.openai import OpenAI

from src.prompts import DOCUMENTATION_GENERATION_PROMPT, DRIFT_CHECK_PROMPT
from src.records import ComponentDocumentation, DocumentationDriftCheck

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


def generate_doc(*, llm: LLM, context: str) -> ComponentDocumentation:
    """
    Generates structured documentation for a component based on code context.

    Args:
        llm: The LLM client instance.
        context: The code context to generate documentation from.

    Returns:
        A ComponentDocumentation object with structured documentation data.
    """
    # Use LLMTextCompletionProgram for structured Pydantic output
    generate_program = LLMTextCompletionProgram.from_defaults(
        output_cls=ComponentDocumentation,
        llm=llm,
        prompt_template_str=DOCUMENTATION_GENERATION_PROMPT,
    )

    # Run the generation
    return generate_program(context=context)
