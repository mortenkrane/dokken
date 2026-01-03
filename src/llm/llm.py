"""LLM client initialization and operations."""

import os
from dataclasses import dataclass

from llama_index.core.llms import LLM
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.llms.anthropic import Anthropic
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.llms.openai import OpenAI
from pydantic import BaseModel

from src.cache import _generate_cache_key, content_based_cache
from src.config import CustomPrompts
from src.constants import ERROR_NO_API_KEY
from src.doc_types import DocType
from src.llm.prompt_builder import build_custom_prompt_section, build_generation_prompt
from src.llm.prompts import DRIFT_CHECK_PROMPT, INCREMENTAL_FIX_PROMPT
from src.records import DocumentationDriftCheck, IncrementalDocumentationFix

# Temperature setting for deterministic, reproducible documentation output
TEMPERATURE = 0.0


@dataclass
class GenerationConfig:
    """Configuration for documentation generation."""

    custom_prompts: CustomPrompts | None = None
    doc_type: DocType | None = None
    human_intent: BaseModel | None = None
    drift_rationale: str | None = None


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

    raise ValueError(ERROR_NO_API_KEY)


@content_based_cache(cache_key_fn=_generate_cache_key)
def check_drift(
    *, llm: LLM, context: str, current_doc: str | None
) -> DocumentationDriftCheck:
    """
    Analyzes the current documentation against the code changes to detect drift.

    This function uses content-based caching to reduce redundant LLM API calls.
    When the same code context and documentation are checked multiple times,
    the cached result is returned instead of making a new LLM call.

    Caching is handled transparently by the @content_based_cache decorator.
    Cache utilities (clear_drift_cache, get_drift_cache_info) are available
    in src.utils for manual cache management.

    Args:
        llm: The LLM client instance.
        context: The code context and diff.
        current_doc: The current documentation content, or None if no
            documentation exists.

    Returns:
        A DocumentationDriftCheck object with drift detection results.
    """
    # Convert None to a message for the prompt
    doc_for_prompt = current_doc or "No existing documentation provided."

    # Use LLMTextCompletionProgram for structured Pydantic output
    check_program = LLMTextCompletionProgram.from_defaults(
        output_cls=DocumentationDriftCheck,
        llm=llm,
        prompt_template_str=DRIFT_CHECK_PROMPT,
    )

    # Run the drift check
    return check_program(context=context, current_doc=doc_for_prompt)


def generate_doc(
    *,
    llm: LLM,
    context: str,
    config: GenerationConfig | None = None,
    output_model: type[BaseModel],
    prompt_template: str,
) -> BaseModel:
    """
    Generates structured documentation based on code context.

    Args:
        llm: The LLM client instance.
        context: The code context to generate documentation from.
        config: Generation configuration (custom prompts, intent, drift info).
               If None, uses default empty configuration.
        output_model: Pydantic model class for structured output.
        prompt_template: Prompt template string to use.

    Returns:
        An instance of output_model with structured documentation data.
    """
    # Use default config if none provided
    if config is None:
        config = GenerationConfig()

    # Build complete prompt from components
    combined_context, combined_intent_section = build_generation_prompt(
        context=context,
        custom_prompts=config.custom_prompts,
        doc_type=config.doc_type,
        human_intent=config.human_intent,
        drift_rationale=config.drift_rationale,
    )

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


def fix_doc_incrementally(
    *,
    llm: LLM,
    context: str,
    current_doc: str,
    drift_rationale: str,
    custom_prompts: CustomPrompts | None = None,
    doc_type: DocType | None = None,
) -> IncrementalDocumentationFix:
    """
    Generates minimal, targeted fixes for documentation drift.

    Unlike generate_doc(), this function preserves the existing documentation
    structure and only modifies sections that need updates to address detected
    drift. This approach is faster, more conservative, and maintains consistency
    with the original documentation's style and voice.

    Args:
        llm: The LLM client instance.
        context: The code context showing current state.
        current_doc: The existing documentation content to fix.
        drift_rationale: Explanation of what drift was detected.
        custom_prompts: Optional custom prompts configuration from .dokken.toml.
        doc_type: Optional documentation type being fixed.

    Returns:
        An IncrementalDocumentationFix with targeted changes.
    """
    # Build custom prompts section if provided
    custom_prompts_section = build_custom_prompt_section(custom_prompts, doc_type)

    # Use LLMTextCompletionProgram for structured Pydantic output
    fix_program = LLMTextCompletionProgram.from_defaults(
        output_cls=IncrementalDocumentationFix,
        llm=llm,
        prompt_template_str=INCREMENTAL_FIX_PROMPT,
    )

    # Run the incremental fix
    return fix_program(
        current_doc=current_doc,
        context=context,
        drift_rationale=drift_rationale,
        custom_prompts_section=custom_prompts_section,
    )
