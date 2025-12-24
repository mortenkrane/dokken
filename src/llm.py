"""LLM client initialization and operations."""

import hashlib
import os
from dataclasses import dataclass
from functools import lru_cache

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

# Cache size for drift detection results (configurable)
DRIFT_CACHE_SIZE = 100


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

    raise ValueError(
        "No API key found. Please set one of the following environment variables:\n"
        "  - ANTHROPIC_API_KEY (for Claude)\n"
        "  - OPENAI_API_KEY (for OpenAI)\n"
        "  - GOOGLE_API_KEY (for Google Gemini)"
    )


def _hash_content(content: str) -> str:
    """
    Computes a SHA256 hash of the given content string.

    Used for cache key generation in drift detection to avoid redundant LLM calls
    when checking the same content multiple times.

    Args:
        content: The string content to hash.

    Returns:
        A hexadecimal string representation of the SHA256 hash.
    """
    return hashlib.sha256(content.encode()).hexdigest()


# Manual cache for drift detection results
# Using a dict instead of @lru_cache because we need to work with non-hashable LLM objects
_drift_cache: dict[str, DocumentationDriftCheck] = {}


def _get_cache_key(context: str, current_doc: str, llm: LLM) -> str:
    """
    Generates a cache key for drift detection based on content hashes and LLM model.

    Args:
        context: The code context string.
        current_doc: The current documentation string.
        llm: The LLM client instance.

    Returns:
        A cache key string combining content hashes and model identifier.
    """
    context_hash = _hash_content(context)
    doc_hash = _hash_content(current_doc)
    # Extract model identifier from LLM instance
    # LLM instances have a 'model' attribute that identifies the specific model
    llm_model = getattr(llm, "model", "unknown")
    return f"{context_hash}:{doc_hash}:{llm_model}"


def clear_drift_cache() -> None:
    """
    Clears the drift detection cache.

    This is useful for testing or when you want to force fresh LLM calls
    regardless of cache state.
    """
    _drift_cache.clear()


def get_drift_cache_info() -> dict[str, int]:
    """
    Returns information about the drift detection cache.

    Returns:
        A dictionary with cache statistics (current size and max size).
    """
    return {"size": len(_drift_cache), "maxsize": DRIFT_CACHE_SIZE}


def check_drift(*, llm: LLM, context: str, current_doc: str) -> DocumentationDriftCheck:
    """
    Analyzes the current documentation against the code changes to detect drift.

    This function implements caching to reduce redundant LLM API calls. When the same
    code context and documentation are checked multiple times, the cached result is
    returned instead of making a new LLM call.

    Caching Behavior:
        - Cache key is based on SHA256 hashes of context and current_doc, plus LLM model
        - Cache size is limited to DRIFT_CACHE_SIZE entries (default: 100)
        - When cache is full, oldest entries are evicted (FIFO)
        - Cache persists for the lifetime of the Python process
        - Cache can be cleared manually via clear_drift_cache()

    Performance Impact:
        - Cache hits avoid LLM API calls entirely (near-instant response)
        - Particularly beneficial in CI/CD where the same files are checked repeatedly
        - Reduces API costs for unchanged code/docs

    Args:
        llm: The LLM client instance.
        context: The code context and diff.
        current_doc: The current documentation content.

    Returns:
        A DocumentationDriftCheck object with drift detection results.
    """
    # Generate cache key
    cache_key = _get_cache_key(context, current_doc, llm)

    # Check cache first
    if cache_key in _drift_cache:
        return _drift_cache[cache_key]

    # Cache miss - perform LLM call
    # Use LLMTextCompletionProgram for structured Pydantic output
    check_program = LLMTextCompletionProgram.from_defaults(
        output_cls=DocumentationDriftCheck,
        llm=llm,
        prompt_template_str=DRIFT_CHECK_PROMPT,
    )

    # Run the check
    result = check_program(context=context, current_doc=current_doc)

    # Store in cache (with size limit)
    if len(_drift_cache) >= DRIFT_CACHE_SIZE:
        # Remove oldest entry (FIFO eviction)
        # In Python 3.7+, dicts maintain insertion order
        oldest_key = next(iter(_drift_cache))
        del _drift_cache[oldest_key]

    _drift_cache[cache_key] = result

    return result


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
    mapping = {
        DocType.MODULE_README: custom_prompts.module_readme,
        DocType.PROJECT_README: custom_prompts.project_readme,
        DocType.STYLE_GUIDE: custom_prompts.style_guide,
    }
    return mapping.get(doc_type)


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

    # Add explicit instructions for the LLM to prioritize user preferences
    header = (
        "\n--- USER PREFERENCES (IMPORTANT) ---\n"
        "The following are custom instructions from the user. These preferences "
        "should be given HIGHEST PRIORITY and followed closely when generating "
        "documentation. If there are conflicts between these preferences and "
        "standard documentation guidelines, prefer the user's preferences.\n\n"
    )

    return header + "\n\n".join(prompt_parts) + "\n"


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

    # Build human intent section if provided
    human_intent_section = (
        _build_human_intent_section(config.human_intent) if config.human_intent else ""
    )

    # Build custom prompt section if provided
    custom_prompt_section = _build_custom_prompt_section(
        config.custom_prompts, config.doc_type
    )

    # Build drift context section if provided
    drift_context_section = (
        _build_drift_context_section(config.drift_rationale)
        if config.drift_rationale
        else ""
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
