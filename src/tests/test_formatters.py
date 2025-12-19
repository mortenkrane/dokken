"""Tests for src/formatters.py"""

import pytest

from src.formatters import generate_markdown
from src.records import ComponentDocumentation


def test_generate_markdown_basic_structure(
    sample_component_documentation: ComponentDocumentation,
) -> None:
    """Test generate_markdown creates correct basic structure."""
    markdown = generate_markdown(doc_data=sample_component_documentation)

    assert markdown.startswith("# Sample Component\n")
    assert "## Purpose & Scope" in markdown
    assert "## Architecture Overview" in markdown
    assert "## Main Entry Points" in markdown
    assert "## Control Flow" in markdown
    assert "## Key Design Decisions" in markdown


def test_generate_markdown_includes_component_name(
    sample_component_documentation: ComponentDocumentation,
) -> None:
    """Test generate_markdown includes the component name as H1 header."""
    markdown = generate_markdown(doc_data=sample_component_documentation)

    assert "# Sample Component\n" in markdown


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
        architecture_overview="Test architecture",
        main_entry_points="Test entry points",
        control_flow="Test control flow",
        key_design_decisions="Test decisions",
        external_dependencies=None,
    )

    markdown = generate_markdown(doc_data=doc_data)

    assert "## External Dependencies" not in markdown


def test_generate_markdown_includes_design_decisions(
    sample_component_documentation: ComponentDocumentation,
) -> None:
    """Test generate_markdown includes design decisions."""
    markdown = generate_markdown(doc_data=sample_component_documentation)

    assert "## Key Design Decisions" in markdown
    assert sample_component_documentation.key_design_decisions in markdown


def test_generate_markdown_includes_architecture_overview(
    sample_component_documentation: ComponentDocumentation,
) -> None:
    """Test generate_markdown includes architecture overview."""
    markdown = generate_markdown(doc_data=sample_component_documentation)

    assert "## Architecture Overview" in markdown
    assert sample_component_documentation.architecture_overview in markdown


def test_generate_markdown_includes_main_entry_points(
    sample_component_documentation: ComponentDocumentation,
) -> None:
    """Test generate_markdown includes main entry points."""
    markdown = generate_markdown(doc_data=sample_component_documentation)

    assert "## Main Entry Points" in markdown
    assert sample_component_documentation.main_entry_points in markdown


def test_generate_markdown_includes_control_flow(
    sample_component_documentation: ComponentDocumentation,
) -> None:
    """Test generate_markdown includes control flow."""
    markdown = generate_markdown(doc_data=sample_component_documentation)

    assert "## Control Flow" in markdown
    assert sample_component_documentation.control_flow in markdown


@pytest.mark.parametrize(
    "component_name",
    ["Payment Service", "User Auth Module", "Data Pipeline"],
)
def test_generate_markdown_various_component_names(component_name: str) -> None:
    """Test generate_markdown with various component names."""
    doc_data = ComponentDocumentation(
        component_name=component_name,
        purpose_and_scope="Test purpose",
        architecture_overview="Test architecture",
        main_entry_points="Test entry points",
        control_flow="Test control flow",
        key_design_decisions="Test decisions",
    )

    markdown = generate_markdown(doc_data=doc_data)

    assert f"# {component_name}\n" in markdown


def test_generate_markdown_minimal_design_decisions() -> None:
    """Test generate_markdown handles minimal design decisions."""
    doc_data = ComponentDocumentation(
        component_name="Test",
        purpose_and_scope="Test",
        architecture_overview="Test architecture",
        main_entry_points="Test entry points",
        control_flow="Test control flow",
        key_design_decisions="No significant design decisions were made.",
    )

    markdown = generate_markdown(doc_data=doc_data)

    assert "## Key Design Decisions" in markdown
    assert "No significant design decisions were made." in markdown


def test_generate_markdown_multiline_content() -> None:
    """Test generate_markdown handles multiline content correctly."""
    doc_data = ComponentDocumentation(
        component_name="Test",
        purpose_and_scope="Line 1\nLine 2\nLine 3",
        architecture_overview="Arch line 1\nArch line 2",
        main_entry_points="Entry line 1\nEntry line 2",
        control_flow="Flow line 1\nFlow line 2",
        key_design_decisions="Decision line 1\nDecision line 2",
    )

    markdown = generate_markdown(doc_data=doc_data)

    assert "Line 1\nLine 2\nLine 3" in markdown
    assert "Decision line 1\nDecision line 2" in markdown


def test_generate_markdown_special_characters() -> None:
    """Test generate_markdown handles special markdown characters."""
    doc_data = ComponentDocumentation(
        component_name="Test*Component*",
        purpose_and_scope="Purpose with **bold** and _italic_",
        architecture_overview="Architecture with **emphasis**",
        main_entry_points="Entry points with `code`",
        control_flow="Flow with [link](url)",
        key_design_decisions="Decisions with **formatting**",
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
        architecture_overview="Architecture",
        main_entry_points="Entry points",
        control_flow="Flow",
        key_design_decisions="Decisions",
    )

    markdown = generate_markdown(doc_data=doc_data)

    # Each section should end with double newline for proper markdown spacing
    assert "## Purpose & Scope\n\nPurpose\n\n" in markdown


def test_generate_markdown_section_order() -> None:
    """Test generate_markdown produces sections in correct order."""
    doc_data = ComponentDocumentation(
        component_name="Test",
        purpose_and_scope="Purpose",
        architecture_overview="Architecture",
        main_entry_points="Entry points",
        control_flow="Flow",
        key_design_decisions="Decisions",
        external_dependencies="Deps",
    )

    markdown = generate_markdown(doc_data=doc_data)

    # Find section positions
    purpose_pos = markdown.find("## Purpose & Scope")
    arch_pos = markdown.find("## Architecture Overview")
    entry_pos = markdown.find("## Main Entry Points")
    flow_pos = markdown.find("## Control Flow")
    deps_pos = markdown.find("## External Dependencies")
    decisions_pos = markdown.find("## Key Design Decisions")

    # Verify correct order
    assert purpose_pos < arch_pos < entry_pos < flow_pos < deps_pos < decisions_pos


@pytest.mark.parametrize(
    "decision_text",
    [
        "We chose approach A because it provides better performance.",
        "The decision to use pattern X was driven by maintainability concerns.",
        "Multiple factors influenced this choice, including scalability and cost.",
    ],
)
def test_generate_markdown_decision_formats(decision_text: str) -> None:
    """Test generate_markdown handles various decision text formats."""
    doc_data = ComponentDocumentation(
        component_name="Test",
        purpose_and_scope="Test",
        architecture_overview="Test architecture",
        main_entry_points="Test entry points",
        control_flow="Test control flow",
        key_design_decisions=decision_text,
    )

    markdown = generate_markdown(doc_data=doc_data)

    assert "## Key Design Decisions" in markdown
    assert decision_text in markdown
