"""Tests for src/prompts.py"""

from typing import Any

import pytest

from src.prompts import (
    DRIFT_CHECK_PROMPT,
    MODULE_GENERATION_PROMPT,
    PROJECT_README_GENERATION_PROMPT,
    STYLE_GUIDE_GENERATION_PROMPT,
)


def test_drift_check_prompt_exists() -> None:
    """Test that DRIFT_CHECK_PROMPT constant exists and is non-empty."""
    assert DRIFT_CHECK_PROMPT
    assert isinstance(DRIFT_CHECK_PROMPT, str)
    assert len(DRIFT_CHECK_PROMPT) > 0


def test_drift_check_prompt_contains_placeholders() -> None:
    """Test that DRIFT_CHECK_PROMPT contains required placeholders."""
    assert "{context}" in DRIFT_CHECK_PROMPT
    assert "{current_doc}" in DRIFT_CHECK_PROMPT


@pytest.mark.parametrize(
    "prompt_name,prompt_value",
    [
        ("DRIFT_CHECK_PROMPT", DRIFT_CHECK_PROMPT),
        ("MODULE_GENERATION_PROMPT", MODULE_GENERATION_PROMPT),
    ],
)
def test_prompts_are_strings(prompt_name: str, prompt_value: Any) -> None:
    """Test that all prompts are string constants."""
    assert isinstance(prompt_value, str), f"{prompt_name} should be a string"


@pytest.mark.parametrize(
    "prompt,expected_keywords",
    [
        (
            DRIFT_CHECK_PROMPT,
            [
                "Documentation Drift Detector",
                "code context",
                "documentation",
                "JSON",
            ],
        ),
        (
            MODULE_GENERATION_PROMPT,
            ["technical writer", "code context", "documentation", "JSON"],
        ),
    ],
)
def test_prompts_contain_expected_keywords(
    prompt: str, expected_keywords: list[str]
) -> None:
    """Test that prompts contain expected instructional keywords."""
    for keyword in expected_keywords:
        assert keyword in prompt, f"Expected keyword '{keyword}' not found in prompt"


def test_prompts_request_json_output() -> None:
    """Test that both prompts explicitly request JSON output."""
    assert "JSON" in DRIFT_CHECK_PROMPT
    assert "JSON" in MODULE_GENERATION_PROMPT


def test_drift_check_prompt_formatting() -> None:
    """Test that DRIFT_CHECK_PROMPT can be formatted with context and current_doc."""
    context = "Sample code context"
    current_doc = "Sample documentation"

    formatted = DRIFT_CHECK_PROMPT.format(context=context, current_doc=current_doc)

    assert context in formatted
    assert current_doc in formatted
    assert "{context}" not in formatted
    assert "{current_doc}" not in formatted


# Tests for new prompts


def test_module_generation_prompt_exists() -> None:
    """Test that MODULE_GENERATION_PROMPT constant exists and is non-empty."""
    assert MODULE_GENERATION_PROMPT
    assert isinstance(MODULE_GENERATION_PROMPT, str)
    assert len(MODULE_GENERATION_PROMPT) > 0


def test_project_readme_generation_prompt_exists() -> None:
    """Test that PROJECT_README_GENERATION_PROMPT constant exists and is non-empty."""
    assert PROJECT_README_GENERATION_PROMPT
    assert isinstance(PROJECT_README_GENERATION_PROMPT, str)
    assert len(PROJECT_README_GENERATION_PROMPT) > 0


def test_style_guide_generation_prompt_exists() -> None:
    """Test that STYLE_GUIDE_GENERATION_PROMPT constant exists and is non-empty."""
    assert STYLE_GUIDE_GENERATION_PROMPT
    assert isinstance(STYLE_GUIDE_GENERATION_PROMPT, str)
    assert len(STYLE_GUIDE_GENERATION_PROMPT) > 0


def test_module_generation_prompt_contains_placeholders() -> None:
    """Test that MODULE_GENERATION_PROMPT contains required placeholders."""
    assert "{context}" in MODULE_GENERATION_PROMPT
    assert "{human_intent_section}" in MODULE_GENERATION_PROMPT


def test_project_readme_generation_prompt_contains_placeholders() -> None:
    """Test that PROJECT_README_GENERATION_PROMPT contains required placeholders."""
    assert "{context}" in PROJECT_README_GENERATION_PROMPT
    assert "{human_intent_section}" in PROJECT_README_GENERATION_PROMPT


def test_style_guide_generation_prompt_contains_placeholders() -> None:
    """Test that STYLE_GUIDE_GENERATION_PROMPT contains required placeholders."""
    assert "{context}" in STYLE_GUIDE_GENERATION_PROMPT
    assert "{human_intent_section}" in STYLE_GUIDE_GENERATION_PROMPT


def test_all_generation_prompts_request_json() -> None:
    """Test that all generation prompts request JSON output."""
    assert (
        "JSON" in MODULE_GENERATION_PROMPT or "json" in MODULE_GENERATION_PROMPT.lower()
    )
    assert (
        "JSON" in PROJECT_README_GENERATION_PROMPT
        or "json" in PROJECT_README_GENERATION_PROMPT.lower()
    )
    assert (
        "JSON" in STYLE_GUIDE_GENERATION_PROMPT
        or "json" in STYLE_GUIDE_GENERATION_PROMPT.lower()
    )


def test_project_readme_prompt_contains_expected_keywords() -> None:
    """Test that PROJECT_README_GENERATION_PROMPT contains expected keywords."""
    expected_keywords = [
        "project",
        "installation",
        "setup",
        "README",
    ]
    for keyword in expected_keywords:
        assert (
            keyword in PROJECT_README_GENERATION_PROMPT
            or keyword.lower() in PROJECT_README_GENERATION_PROMPT.lower()
        ), f"Expected keyword '{keyword}' not found in PROJECT_README_GENERATION_PROMPT"


def test_style_guide_prompt_contains_expected_keywords() -> None:
    """Test that STYLE_GUIDE_GENERATION_PROMPT contains expected keywords."""
    expected_keywords = [
        "style",
        "conventions",
        "patterns",
        "code",
    ]
    for keyword in expected_keywords:
        assert (
            keyword in STYLE_GUIDE_GENERATION_PROMPT
            or keyword.lower() in STYLE_GUIDE_GENERATION_PROMPT.lower()
        ), f"Expected keyword '{keyword}' not found in STYLE_GUIDE_GENERATION_PROMPT"


def test_module_generation_prompt_formatting() -> None:
    """Test that MODULE_GENERATION_PROMPT can be formatted with context."""
    context = "Sample code context"
    human_intent_section = "Sample intent"

    formatted = MODULE_GENERATION_PROMPT.format(
        context=context, human_intent_section=human_intent_section
    )

    assert context in formatted
    assert human_intent_section in formatted
    assert "{context}" not in formatted
    assert "{human_intent_section}" not in formatted


def test_project_readme_generation_prompt_formatting() -> None:
    """Test that PROJECT_README_GENERATION_PROMPT can be formatted."""
    context = "Sample code context"
    human_intent_section = "Sample intent"

    formatted = PROJECT_README_GENERATION_PROMPT.format(
        context=context, human_intent_section=human_intent_section
    )

    assert context in formatted
    assert human_intent_section in formatted
    assert "{context}" not in formatted
    assert "{human_intent_section}" not in formatted


def test_style_guide_generation_prompt_formatting() -> None:
    """Test that STYLE_GUIDE_GENERATION_PROMPT can be formatted."""
    context = "Sample code context"
    human_intent_section = "Sample intent"

    formatted = STYLE_GUIDE_GENERATION_PROMPT.format(
        context=context, human_intent_section=human_intent_section
    )

    assert context in formatted
    assert human_intent_section in formatted
    assert "{context}" not in formatted
    assert "{human_intent_section}" not in formatted
