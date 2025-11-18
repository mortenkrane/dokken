"""Tests for src/prompts.py"""

import pytest

from src.prompts import DOCUMENTATION_GENERATION_PROMPT, DRIFT_CHECK_PROMPT


def test_drift_check_prompt_exists():
    """Test that DRIFT_CHECK_PROMPT constant exists and is non-empty."""
    assert DRIFT_CHECK_PROMPT
    assert isinstance(DRIFT_CHECK_PROMPT, str)
    assert len(DRIFT_CHECK_PROMPT) > 0


def test_documentation_generation_prompt_exists():
    """Test that DOCUMENTATION_GENERATION_PROMPT constant exists and is non-empty."""
    assert DOCUMENTATION_GENERATION_PROMPT
    assert isinstance(DOCUMENTATION_GENERATION_PROMPT, str)
    assert len(DOCUMENTATION_GENERATION_PROMPT) > 0


def test_drift_check_prompt_contains_placeholders():
    """Test that DRIFT_CHECK_PROMPT contains required placeholders."""
    assert "{context}" in DRIFT_CHECK_PROMPT
    assert "{current_doc}" in DRIFT_CHECK_PROMPT


def test_documentation_generation_prompt_contains_placeholders():
    """Test that DOCUMENTATION_GENERATION_PROMPT contains required placeholders."""
    assert "{context}" in DOCUMENTATION_GENERATION_PROMPT


@pytest.mark.parametrize(
    "prompt_name,prompt_value",
    [
        ("DRIFT_CHECK_PROMPT", DRIFT_CHECK_PROMPT),
        ("DOCUMENTATION_GENERATION_PROMPT", DOCUMENTATION_GENERATION_PROMPT),
    ],
)
def test_prompts_are_strings(prompt_name, prompt_value):
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
            DOCUMENTATION_GENERATION_PROMPT,
            ["technical writer", "code context", "documentation", "JSON"],
        ),
    ],
)
def test_prompts_contain_expected_keywords(prompt, expected_keywords):
    """Test that prompts contain expected instructional keywords."""
    for keyword in expected_keywords:
        assert keyword in prompt, f"Expected keyword '{keyword}' not found in prompt"


def test_prompts_request_json_output():
    """Test that both prompts explicitly request JSON output."""
    assert "JSON" in DRIFT_CHECK_PROMPT
    assert "JSON" in DOCUMENTATION_GENERATION_PROMPT


def test_drift_check_prompt_formatting():
    """Test that DRIFT_CHECK_PROMPT can be formatted with context and current_doc."""
    context = "Sample code context"
    current_doc = "Sample documentation"

    formatted = DRIFT_CHECK_PROMPT.format(context=context, current_doc=current_doc)

    assert context in formatted
    assert current_doc in formatted
    assert "{context}" not in formatted
    assert "{current_doc}" not in formatted


def test_documentation_generation_prompt_formatting():
    """Test that DOCUMENTATION_GENERATION_PROMPT can be formatted with context."""
    context = "Sample code context"

    formatted = DOCUMENTATION_GENERATION_PROMPT.format(context=context)

    assert context in formatted
    assert "{context}" not in formatted
