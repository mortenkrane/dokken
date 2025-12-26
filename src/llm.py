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
from src.prompt_builder import build_generation_prompt
from src.prompts import DRIFT_CHECK_PROMPT
from src.records import DocumentationDriftCheck

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
def check_drift(*, llm: LLM, context: str, current_doc: str) -> DocumentationDriftCheck:
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

    # Run the drift check
    return check_program(context=context, current_doc=current_doc)


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
