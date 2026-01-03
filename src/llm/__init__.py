"""LLM operations, prompts, and prompt building for documentation generation.

This submodule provides:
- LLM client initialization and operations (llm.py)
- Prompt templates for generation and drift detection (prompts.py)
- Prompt assembly logic (prompt_builder.py)
"""

from src.llm.llm import (
    TEMPERATURE,
    GenerationConfig,
    check_drift,
    fix_doc_incrementally,
    generate_doc,
    initialize_llm,
)
from src.llm.prompt_builder import (
    build_custom_prompt_section,
    build_drift_context_section,
    build_generation_prompt,
    build_human_intent_section,
)
from src.llm.prompts import (
    DRIFT_CHECK_PROMPT,
    INCREMENTAL_FIX_PROMPT,
    MODULE_GENERATION_PROMPT,
    PROJECT_README_GENERATION_PROMPT,
    STYLE_GUIDE_GENERATION_PROMPT,
)

__all__ = [
    # LLM operations
    "TEMPERATURE",
    "GenerationConfig",
    "check_drift",
    "fix_doc_incrementally",
    "generate_doc",
    "initialize_llm",
    # Prompt templates
    "DRIFT_CHECK_PROMPT",
    "INCREMENTAL_FIX_PROMPT",
    "MODULE_GENERATION_PROMPT",
    "PROJECT_README_GENERATION_PROMPT",
    "STYLE_GUIDE_GENERATION_PROMPT",
    # Prompt building
    "build_custom_prompt_section",
    "build_drift_context_section",
    "build_generation_prompt",
    "build_human_intent_section",
]
