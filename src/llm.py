"""LLM client initialization and operations."""

import os

from llama_index.core.program import LLMTextCompletionProgram
from llama_index.llms.google_genai import GoogleGenAI

from src.prompts import DOCUMENTATION_GENERATION_PROMPT, DRIFT_CHECK_PROMPT
from src.records import ComponentDocumentation, DocumentationDriftCheck, HumanIntent


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
    return check_program(context=context, current_doc=current_doc)


def generate_doc(
    *, llm: GoogleGenAI, context: str, human_intent: HumanIntent | None = None
) -> ComponentDocumentation:
    """
    Generates structured documentation for a component based on code context.

    Args:
        llm: The LLM client instance.
        context: The code context to generate documentation from.
        human_intent: Optional human-provided intent and context for the module.

    Returns:
        A ComponentDocumentation object with structured documentation data.
    """
    # Build human intent section if provided
    human_intent_section = ""
    if human_intent:
        intent_lines = []
        if human_intent.problems_solved:
            intent_lines.append(f"Problems Solved: {human_intent.problems_solved}")
        if human_intent.core_responsibilities:
            intent_lines.append(
                f"Core Responsibilities: {human_intent.core_responsibilities}"
            )
        if human_intent.non_responsibilities:
            intent_lines.append(
                f"Non-Responsibilities: {human_intent.non_responsibilities}"
            )
        if human_intent.system_context:
            intent_lines.append(f"System Context: {human_intent.system_context}")
        if human_intent.entry_points:
            intent_lines.append(f"Entry Points: {human_intent.entry_points}")
        if human_intent.invariants:
            intent_lines.append(f"Invariants: {human_intent.invariants}")
        if human_intent.limitations:
            intent_lines.append(f"Limitations: {human_intent.limitations}")
        if human_intent.common_pitfalls:
            intent_lines.append(f"Common Pitfalls: {human_intent.common_pitfalls}")

        if intent_lines:
            human_intent_section = (
                "\n--- HUMAN-PROVIDED CONTEXT ---\n" + "\n".join(intent_lines) + "\n"
            )

    # Use LLMTextCompletionProgram for structured Pydantic output
    generate_program = LLMTextCompletionProgram.from_defaults(
        output_cls=ComponentDocumentation,
        llm=llm,
        prompt_template_str=DOCUMENTATION_GENERATION_PROMPT,
    )

    # Run the generation
    return generate_program(context=context, human_intent_section=human_intent_section)
