"""Tests for src/formatters.py"""

import pytest

from src.formatters import generate_markdown
from src.records import ComponentDocumentation


def test_generate_markdown_basic_structure(
    sample_component_documentation: ComponentDocumentation,
) -> None:
    """Test generate_markdown creates correct basic structure."""
    markdown = generate_markdown(doc_data=sample_component_documentation)

    assert markdown.startswith("# Sample Component Overview")
    assert "## Purpose & Scope" in markdown
    assert "## Key Design Decisions (The 'Why')" in markdown


def test_generate_markdown_includes_component_name(
    sample_component_documentation: ComponentDocumentation,
) -> None:
    """Test generate_markdown includes the component name as H1 header."""
    markdown = generate_markdown(doc_data=sample_component_documentation)

    assert "# Sample Component Overview" in markdown


def test_generate_markdown_includes_purpose(
    sample_component_documentation: ComponentDocumentation,
) -> None:
    """Test generate_markdown includes purpose and scope section."""
    markdown = generate_markdown(doc_data=sample_component_documentation)

    assert "## Purpose & Scope" in markdown
    assert sample_component_documentation.purpose_and_scope in markdown


def test_generate_markdown_includes_dependencies(
    sample_component_documentation: ComponentDocumentation,
) -> None:
    """Test generate_markdown includes external dependencies section."""
    markdown = generate_markdown(doc_data=sample_component_documentation)

    assert "## External Dependencies" in markdown
    assert sample_component_documentation.external_dependencies is not None
    assert sample_component_documentation.external_dependencies in markdown


def test_generate_markdown_without_dependencies() -> None:
    """Test generate_markdown handles missing external dependencies."""
    doc_data = ComponentDocumentation(
        component_name="Test Component",
        purpose_and_scope="Test purpose",
        design_decisions={"KEY": "value"},
        external_dependencies=None,
    )

    markdown = generate_markdown(doc_data=doc_data)

    assert "## External Dependencies" not in markdown


def test_generate_markdown_includes_design_decisions(
    sample_component_documentation: ComponentDocumentation,
) -> None:
    """Test generate_markdown includes all design decisions."""
    markdown = generate_markdown(doc_data=sample_component_documentation)

    for key, value in sample_component_documentation.design_decisions.items():
        assert f"### Decision: {key}" in markdown
        assert value in markdown


def test_generate_markdown_sorts_design_decisions() -> None:
    """Test generate_markdown sorts design decisions alphabetically."""
    doc_data = ComponentDocumentation(
        component_name="Test",
        purpose_and_scope="Test",
        design_decisions={
            "ZZZZZ": "Last alphabetically",
            "AAAAA": "First alphabetically",
            "MMMMM": "Middle alphabetically",
        },
    )

    markdown = generate_markdown(doc_data=doc_data)

    # Find positions of each decision
    pos_a = markdown.find("### Decision: AAAAA")
    pos_m = markdown.find("### Decision: MMMMM")
    pos_z = markdown.find("### Decision: ZZZZZ")

    # Verify they appear in alphabetical order
    assert pos_a < pos_m < pos_z


@pytest.mark.parametrize(
    "component_name",
    ["Payment Service", "User Auth Module", "Data Pipeline"],
)
def test_generate_markdown_various_component_names(component_name: str) -> None:
    """Test generate_markdown with various component names."""
    doc_data = ComponentDocumentation(
        component_name=component_name,
        purpose_and_scope="Test purpose",
        design_decisions={"KEY": "value"},
    )

    markdown = generate_markdown(doc_data=doc_data)

    assert f"# {component_name} Overview" in markdown


def test_generate_markdown_empty_design_decisions() -> None:
    """Test generate_markdown handles empty design decisions."""
    doc_data = ComponentDocumentation(
        component_name="Test",
        purpose_and_scope="Test",
        design_decisions={},
    )

    markdown = generate_markdown(doc_data=doc_data)

    assert "## Key Design Decisions (The 'Why')" in markdown
    # No decision subsections should be present
    assert "### Decision:" not in markdown


def test_generate_markdown_multiline_content() -> None:
    """Test generate_markdown handles multiline content correctly."""
    doc_data = ComponentDocumentation(
        component_name="Test",
        purpose_and_scope="Line 1\nLine 2\nLine 3",
        design_decisions={"DECISION": "Explanation line 1\nExplanation line 2"},
    )

    markdown = generate_markdown(doc_data=doc_data)

    assert "Line 1\nLine 2\nLine 3" in markdown
    assert "Explanation line 1\nExplanation line 2" in markdown


def test_generate_markdown_special_characters() -> None:
    """Test generate_markdown handles special markdown characters."""
    doc_data = ComponentDocumentation(
        component_name="Test*Component*",
        purpose_and_scope="Purpose with **bold** and _italic_",
        design_decisions={"KEY": "Value with `code` and [link](url)"},
    )

    markdown = generate_markdown(doc_data=doc_data)

    # These should be preserved as-is
    assert "Test*Component*" in markdown
    assert "**bold**" in markdown
    assert "`code`" in markdown


def test_generate_markdown_deterministic_output(
    sample_component_documentation: ComponentDocumentation,
) -> None:
    """Test generate_markdown produces deterministic output."""
    markdown1 = generate_markdown(doc_data=sample_component_documentation)
    markdown2 = generate_markdown(doc_data=sample_component_documentation)

    assert markdown1 == markdown2


def test_generate_markdown_ends_with_newlines() -> None:
    """Test generate_markdown ends sections with proper newlines."""
    doc_data = ComponentDocumentation(
        component_name="Test",
        purpose_and_scope="Purpose",
        design_decisions={"KEY": "Value"},
    )

    markdown = generate_markdown(doc_data=doc_data)

    # Each section should end with double newline for proper markdown spacing
    assert "## Purpose & Scope\n\nPurpose\n\n" in markdown


def test_generate_markdown_section_order() -> None:
    """Test generate_markdown produces sections in correct order."""
    doc_data = ComponentDocumentation(
        component_name="Test",
        purpose_and_scope="Purpose",
        design_decisions={"KEY": "Value"},
        external_dependencies="Deps",
    )

    markdown = generate_markdown(doc_data=doc_data)

    # Find section positions
    purpose_pos = markdown.find("## Purpose & Scope")
    deps_pos = markdown.find("## External Dependencies")
    decisions_pos = markdown.find("## Key Design Decisions")

    # Verify correct order
    assert purpose_pos < deps_pos < decisions_pos


@pytest.mark.parametrize(
    "decision_key,decision_value",
    [
        ("SIMPLE_KEY", "Simple value"),
        ("KEY_WITH_UNDERSCORES", "Value with spaces"),
        ("123_NUMERIC", "Numeric prefix"),
    ],
)
def test_generate_markdown_decision_formats(
    decision_key: str, decision_value: str
) -> None:
    """Test generate_markdown handles various decision key formats."""
    doc_data = ComponentDocumentation(
        component_name="Test",
        purpose_and_scope="Test",
        design_decisions={decision_key: decision_value},
    )

    markdown = generate_markdown(doc_data=doc_data)

    assert f"### Decision: {decision_key}" in markdown
    assert decision_value in markdown
