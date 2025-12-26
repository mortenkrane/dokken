"""Tests for src/prompt_builder.py"""


from src.config import CustomPrompts
from src.doc_types import DocType
from src.prompt_builder import (
    build_custom_prompt_section,
    build_drift_context_section,
    build_generation_prompt,
    build_human_intent_section,
)
from src.records import ModuleIntent

# --- Tests for build_human_intent_section() ---


def test_build_human_intent_section_with_data() -> None:
    """Test build_human_intent_section formats human intent data correctly."""
    intent = ModuleIntent(
        problems_solved="Authentication and authorization",
        core_responsibilities="Manage user sessions and permissions",
    )

    result = build_human_intent_section(intent)

    assert "--- HUMAN-PROVIDED CONTEXT ---" in result
    assert "Problems Solved: Authentication and authorization" in result
    assert "Core Responsibilities: Manage user sessions and permissions" in result


def test_build_human_intent_section_with_partial_data() -> None:
    """Test build_human_intent_section handles partial intent data."""
    intent = ModuleIntent(problems_solved="User management", core_responsibilities=None)

    result = build_human_intent_section(intent)

    assert "--- HUMAN-PROVIDED CONTEXT ---" in result
    assert "Problems Solved: User management" in result
    assert "Core Responsibilities" not in result


def test_build_human_intent_section_with_no_data() -> None:
    """Test build_human_intent_section returns empty string when no data."""
    intent = ModuleIntent(problems_solved=None, core_responsibilities=None)

    result = build_human_intent_section(intent)

    assert result == ""


# --- Tests for build_drift_context_section() ---


def test_build_drift_context_section_basic() -> None:
    """Test build_drift_context_section formats drift rationale correctly."""
    rationale = "API changed from v1 to v2, authentication module was removed"

    result = build_drift_context_section(rationale)

    assert "--- DETECTED DOCUMENTATION DRIFT ---" in result
    assert "API changed from v1 to v2, authentication module was removed" in result
    assert "documentation drift occurs when" in result.lower()
    assert "IMPORTANT" in result
    assert "addresses these specific drift issues" in result.lower()


def test_build_drift_context_section_educational_content() -> None:
    """Test build_drift_context_section includes educational context."""
    rationale = "Functions renamed: process() -> handle_request()"

    result = build_drift_context_section(rationale)

    # Check for educational elements
    assert "code changes but documentation doesn't" in result.lower()
    assert "automated analysis" in result.lower()
    assert "current code state" in result.lower()


def test_build_drift_context_section_with_special_characters() -> None:
    """Test build_drift_context_section handles special characters."""
    rationale = (
        "Class `UserAuth` removed\nNew module: auth/oauth2.py\n- Added JWT support"
    )

    result = build_drift_context_section(rationale)

    assert "Class `UserAuth` removed" in result
    assert "New module: auth/oauth2.py" in result
    assert "Added JWT support" in result


def test_build_drift_context_section_multiline_rationale() -> None:
    """Test build_drift_context_section preserves multiline rationale formatting."""
    rationale = """Major architectural changes:
1. Switched from REST to GraphQL
2. Removed legacy endpoints
3. Updated authentication flow"""

    result = build_drift_context_section(rationale)

    assert "Switched from REST to GraphQL" in result
    assert "Removed legacy endpoints" in result
    assert "Updated authentication flow" in result


# --- Tests for build_custom_prompt_section() ---


def test_build_custom_prompt_section_none() -> None:
    """Test build_custom_prompt_section returns empty string when None."""
    result = build_custom_prompt_section(custom_prompts=None, doc_type=None)

    assert result == ""


def test_build_custom_prompt_section_empty_prompts() -> None:
    """Test build_custom_prompt_section returns empty string when all prompts None."""
    custom_prompts = CustomPrompts()

    result = build_custom_prompt_section(
        custom_prompts=custom_prompts, doc_type=DocType.MODULE_README
    )

    assert result == ""


def test_build_custom_prompt_section_global_only() -> None:
    """Test build_custom_prompt_section with only global prompt."""
    custom_prompts = CustomPrompts(global_prompt="Use British spelling.")

    result = build_custom_prompt_section(
        custom_prompts=custom_prompts, doc_type=DocType.MODULE_README
    )

    assert "--- USER PREFERENCES (IMPORTANT) ---" in result
    assert "Use British spelling." in result


def test_build_custom_prompt_section_doc_type_specific() -> None:
    """Test build_custom_prompt_section with doc-type-specific prompt."""
    custom_prompts = CustomPrompts(
        module_readme="Focus on implementation details.",
        project_readme="Keep it concise.",
    )

    result = build_custom_prompt_section(
        custom_prompts=custom_prompts, doc_type=DocType.MODULE_README
    )

    assert "--- USER PREFERENCES (IMPORTANT) ---" in result
    assert "Focus on implementation details." in result
    assert "Keep it concise." not in result  # Different doc type


def test_build_custom_prompt_section_project_readme() -> None:
    """Test build_custom_prompt_section with project README doc type."""
    custom_prompts = CustomPrompts(
        module_readme="Focus on implementation.",
        project_readme="Include quick-start guide.",
    )

    result = build_custom_prompt_section(
        custom_prompts=custom_prompts, doc_type=DocType.PROJECT_README
    )

    assert "--- USER PREFERENCES (IMPORTANT) ---" in result
    assert "Include quick-start guide." in result
    assert "Focus on implementation." not in result  # Different doc type


def test_build_custom_prompt_section_style_guide() -> None:
    """Test build_custom_prompt_section with style guide doc type."""
    custom_prompts = CustomPrompts(
        style_guide="Reference existing code patterns.",
        module_readme="Focus on implementation.",
    )

    result = build_custom_prompt_section(
        custom_prompts=custom_prompts, doc_type=DocType.STYLE_GUIDE
    )

    assert "--- USER PREFERENCES (IMPORTANT) ---" in result
    assert "Reference existing code patterns." in result
    assert "Focus on implementation." not in result  # Different doc type


def test_build_custom_prompt_section_global_and_specific() -> None:
    """Test build_custom_prompt_section combines global and doc-type-specific."""
    custom_prompts = CustomPrompts(
        global_prompt="Use clear, simple language.",
        module_readme="Focus on architecture.",
    )

    result = build_custom_prompt_section(
        custom_prompts=custom_prompts, doc_type=DocType.MODULE_README
    )

    assert "--- USER PREFERENCES (IMPORTANT) ---" in result
    assert "Use clear, simple language." in result
    assert "Focus on architecture." in result
    # Check they're separated by double newline
    assert "Use clear, simple language.\n\nFocus on architecture." in result


def test_build_custom_prompt_section_no_doc_type() -> None:
    """Test build_custom_prompt_section with None doc_type uses only global."""
    custom_prompts = CustomPrompts(
        global_prompt="Be concise.",
        module_readme="Focus on implementation.",
    )

    result = build_custom_prompt_section(custom_prompts=custom_prompts, doc_type=None)

    assert "--- USER PREFERENCES (IMPORTANT) ---" in result
    assert "Be concise." in result
    assert "Focus on implementation." not in result  # No doc type specified


# --- Tests for build_generation_prompt() ---


def test_build_generation_prompt_minimal() -> None:
    """Test build_generation_prompt with minimal inputs."""
    context = "def foo(): pass"

    combined_context, combined_intent_section = build_generation_prompt(context=context)

    assert combined_context == "def foo(): pass"
    assert combined_intent_section == ""


def test_build_generation_prompt_with_human_intent() -> None:
    """Test build_generation_prompt includes human intent."""
    context = "def foo(): pass"
    intent = ModuleIntent(
        problems_solved="User authentication", core_responsibilities="Login flow"
    )

    combined_context, combined_intent_section = build_generation_prompt(
        context=context, human_intent=intent
    )

    assert combined_context == context
    assert "--- HUMAN-PROVIDED CONTEXT ---" in combined_intent_section
    assert "Problems Solved: User authentication" in combined_intent_section


def test_build_generation_prompt_with_custom_prompts() -> None:
    """Test build_generation_prompt includes custom prompts."""
    context = "def foo(): pass"
    custom_prompts = CustomPrompts(global_prompt="Be concise.")

    combined_context, combined_intent_section = build_generation_prompt(
        context=context, custom_prompts=custom_prompts, doc_type=DocType.MODULE_README
    )

    assert combined_context == context
    assert "--- USER PREFERENCES (IMPORTANT) ---" in combined_intent_section
    assert "Be concise." in combined_intent_section


def test_build_generation_prompt_with_drift_rationale() -> None:
    """Test build_generation_prompt includes drift context."""
    context = "def foo(): pass"
    drift_rationale = "Function bar() was removed"

    combined_context, combined_intent_section = build_generation_prompt(
        context=context, drift_rationale=drift_rationale
    )

    assert "--- DETECTED DOCUMENTATION DRIFT ---" in combined_context
    assert "Function bar() was removed" in combined_context
    assert combined_intent_section == ""


def test_build_generation_prompt_with_all_sections() -> None:
    """Test build_generation_prompt combines all sections correctly."""
    context = "def foo(): pass"
    intent = ModuleIntent(problems_solved="Auth")
    custom_prompts = CustomPrompts(global_prompt="Be clear.")
    drift_rationale = "Function removed"

    combined_context, combined_intent_section = build_generation_prompt(
        context=context,
        human_intent=intent,
        custom_prompts=custom_prompts,
        doc_type=DocType.MODULE_README,
        drift_rationale=drift_rationale,
    )

    # Context should have drift info
    assert "def foo(): pass" in combined_context
    assert "--- DETECTED DOCUMENTATION DRIFT ---" in combined_context
    assert "Function removed" in combined_context

    # Intent section should have both human intent and custom prompts
    assert "--- HUMAN-PROVIDED CONTEXT ---" in combined_intent_section
    assert "Problems Solved: Auth" in combined_intent_section
    assert "--- USER PREFERENCES (IMPORTANT) ---" in combined_intent_section
    assert "Be clear." in combined_intent_section
