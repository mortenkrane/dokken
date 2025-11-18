"""LLM client initialization and operations."""

import os

from llama_index.core.program import LLMTextCompletionProgram
from llama_index.llms.google_genai import GoogleGenAI

from src.prompts import DOCUMENTATION_GENERATION_PROMPT, DRIFT_CHECK_PROMPT
from src.records import ComponentDocumentation, DocumentationDriftCheck


def initialize_llm() -> GoogleGenAI:
    """Initializes the GoogleGenAI LLM client."""
    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY environment variable not set.")

    # Using Gemini-2.5-Flash as it has a good balance of speed, cost, and context window
    # Low temp for stability
    return GoogleGenAI(model="gemini-2.5-flash", temperature=0.0)


def check_drift(
    *, llm: GoogleGenAI, context: str, current_doc: str
) -> DocumentationDriftCheck:
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
    check_result = check_program(context=context, current_doc=current_doc)
    return check_result


def generate_doc(*, llm: GoogleGenAI, context: str) -> ComponentDocumentation:
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
    doc_result = generate_program(context=context)
    return doc_result
