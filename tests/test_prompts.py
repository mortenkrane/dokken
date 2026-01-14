"""Tests for src/prompts.py"""

from src.llm import (
    DRIFT_CHECK_PROMPT,
    MODULE_GENERATION_PROMPT,
    PROJECT_README_GENERATION_PROMPT,
    STYLE_GUIDE_GENERATION_PROMPT,
)


def test_all_prompts_exist_and_are_valid() -> None:
    """Smoke test that all prompts exist and can be formatted."""
    # Check all prompts exist and are strings
    assert DRIFT_CHECK_PROMPT and isinstance(DRIFT_CHECK_PROMPT, str)
    assert MODULE_GENERATION_PROMPT and isinstance(MODULE_GENERATION_PROMPT, str)
    assert PROJECT_README_GENERATION_PROMPT and isinstance(
        PROJECT_README_GENERATION_PROMPT, str
    )
    assert STYLE_GUIDE_GENERATION_PROMPT and isinstance(
        STYLE_GUIDE_GENERATION_PROMPT, str
    )

    # Test that prompts can be formatted without errors
    DRIFT_CHECK_PROMPT.format(context="test", current_doc="test")
    MODULE_GENERATION_PROMPT.format(context="test", human_intent_section="")
    PROJECT_README_GENERATION_PROMPT.format(context="test", human_intent_section="")
    STYLE_GUIDE_GENERATION_PROMPT.format(context="test", human_intent_section="")


def test_prompts_contain_required_placeholders() -> None:
    """Test that prompts contain their required format placeholders."""
    # Drift check prompt needs both context and current_doc
    assert "{context}" in DRIFT_CHECK_PROMPT
    assert "{current_doc}" in DRIFT_CHECK_PROMPT

    # Generation prompts need context and human_intent_section
    assert "{context}" in MODULE_GENERATION_PROMPT
    assert "{human_intent_section}" in MODULE_GENERATION_PROMPT

    assert "{context}" in PROJECT_README_GENERATION_PROMPT
    assert "{human_intent_section}" in PROJECT_README_GENERATION_PROMPT

    assert "{context}" in STYLE_GUIDE_GENERATION_PROMPT
    assert "{human_intent_section}" in STYLE_GUIDE_GENERATION_PROMPT
