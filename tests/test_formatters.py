"""Tests for src/formatters.py"""

import pytest

from src.formatters import (
    format_module_documentation,
    format_project_documentation,
    format_style_guide,
)
from src.records import (
    ModuleDocumentation,
    ProjectDocumentation,
    StyleGuideDocumentation,
)


def test_format_module_documentation_basic_structure(
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test format_module_documentation creates correct basic structure."""
    markdown = format_module_documentation(doc_data=sample_component_documentation)

    assert markdown.startswith("# Sample Component\n")
    assert "## Purpose & Scope" in markdown
    assert "## Architecture Overview" in markdown
    assert "## Main Entry Points" in markdown
    assert "## Control Flow" in markdown
    assert "## Key Design Decisions" in markdown


def test_format_module_documentation_includes_component_name(
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test format_module_documentation includes the component name as H1 header."""
    markdown = format_module_documentation(doc_data=sample_component_documentation)

    assert "# Sample Component\n" in markdown


def test_format_module_documentation_includes_purpose(
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test format_module_documentation includes purpose and scope section."""
    markdown = format_module_documentation(doc_data=sample_component_documentation)

    assert "## Purpose & Scope" in markdown
    assert sample_component_documentation.purpose_and_scope in markdown


def test_format_module_documentation_includes_dependencies(
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test format_module_documentation includes external dependencies section."""
    markdown = format_module_documentation(doc_data=sample_component_documentation)

    assert "## External Dependencies" in markdown
    assert sample_component_documentation.external_dependencies is not None
    assert sample_component_documentation.external_dependencies in markdown


def test_format_module_documentation_without_dependencies() -> None:
    """Test format_module_documentation handles missing external dependencies."""
    doc_data = ModuleDocumentation(
        component_name="Test Component",
        purpose_and_scope="Test purpose",
        architecture_overview="Test architecture",
        main_entry_points="Test entry points",
        control_flow="Test control flow",
        key_design_decisions="Test decisions",
        external_dependencies=None,
    )

    markdown = format_module_documentation(doc_data=doc_data)

    assert "## External Dependencies" not in markdown


def test_format_module_documentation_includes_design_decisions(
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test format_module_documentation includes design decisions."""
    markdown = format_module_documentation(doc_data=sample_component_documentation)

    assert "## Key Design Decisions" in markdown
    assert sample_component_documentation.key_design_decisions in markdown


def test_format_module_documentation_includes_architecture_overview(
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test format_module_documentation includes architecture overview."""
    markdown = format_module_documentation(doc_data=sample_component_documentation)

    assert "## Architecture Overview" in markdown
    assert sample_component_documentation.architecture_overview in markdown


def test_format_module_documentation_includes_main_entry_points(
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test format_module_documentation includes main entry points."""
    markdown = format_module_documentation(doc_data=sample_component_documentation)

    assert "## Main Entry Points" in markdown
    assert sample_component_documentation.main_entry_points in markdown


def test_format_module_documentation_includes_control_flow(
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test format_module_documentation includes control flow."""
    markdown = format_module_documentation(doc_data=sample_component_documentation)

    assert "## Control Flow" in markdown
    assert sample_component_documentation.control_flow in markdown


@pytest.mark.parametrize(
    "component_name",
    ["Payment Service", "User Auth Module", "Data Pipeline"],
)
def test_format_module_documentation_various_component_names(
    component_name: str,
) -> None:
    """Test format_module_documentation with various component names."""
    doc_data = ModuleDocumentation(
        component_name=component_name,
        purpose_and_scope="Test purpose",
        architecture_overview="Test architecture",
        main_entry_points="Test entry points",
        control_flow="Test control flow",
        key_design_decisions="Test decisions",
    )

    markdown = format_module_documentation(doc_data=doc_data)

    assert f"# {component_name}\n" in markdown


def test_format_module_documentation_minimal_design_decisions() -> None:
    """Test format_module_documentation handles minimal design decisions."""
    doc_data = ModuleDocumentation(
        component_name="Test",
        purpose_and_scope="Test",
        architecture_overview="Test architecture",
        main_entry_points="Test entry points",
        control_flow="Test control flow",
        key_design_decisions="No significant design decisions were made.",
    )

    markdown = format_module_documentation(doc_data=doc_data)

    assert "## Key Design Decisions" in markdown
    assert "No significant design decisions were made." in markdown


def test_format_module_documentation_multiline_content() -> None:
    """Test format_module_documentation handles multiline content correctly."""
    doc_data = ModuleDocumentation(
        component_name="Test",
        purpose_and_scope="Line 1\nLine 2\nLine 3",
        architecture_overview="Arch line 1\nArch line 2",
        main_entry_points="Entry line 1\nEntry line 2",
        control_flow="Flow line 1\nFlow line 2",
        key_design_decisions="Decision line 1\nDecision line 2",
    )

    markdown = format_module_documentation(doc_data=doc_data)

    assert "Line 1\nLine 2\nLine 3" in markdown
    assert "Decision line 1\nDecision line 2" in markdown


def test_format_module_documentation_special_characters() -> None:
    """Test format_module_documentation handles special markdown characters."""
    doc_data = ModuleDocumentation(
        component_name="Test*Component*",
        purpose_and_scope="Purpose with **bold** and _italic_",
        architecture_overview="Architecture with **emphasis**",
        main_entry_points="Entry points with `code`",
        control_flow="Flow with [link](url)",
        key_design_decisions="Decisions with **formatting**",
    )

    markdown = format_module_documentation(doc_data=doc_data)

    # These should be preserved as-is
    assert "Test*Component*" in markdown
    assert "**bold**" in markdown
    assert "`code`" in markdown


def test_format_module_documentation_deterministic_output(
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test format_module_documentation produces deterministic output."""
    markdown1 = format_module_documentation(doc_data=sample_component_documentation)
    markdown2 = format_module_documentation(doc_data=sample_component_documentation)

    assert markdown1 == markdown2


def test_format_module_documentation_ends_with_newlines() -> None:
    """Test format_module_documentation ends sections with proper newlines."""
    doc_data = ModuleDocumentation(
        component_name="Test",
        purpose_and_scope="Purpose",
        architecture_overview="Architecture",
        main_entry_points="Entry points",
        control_flow="Flow",
        key_design_decisions="Decisions",
    )

    markdown = format_module_documentation(doc_data=doc_data)

    # Each section should end with double newline for proper markdown spacing
    assert "## Purpose & Scope\n\nPurpose\n\n" in markdown


def test_format_module_documentation_section_order() -> None:
    """Test format_module_documentation produces sections in correct order."""
    doc_data = ModuleDocumentation(
        component_name="Test",
        purpose_and_scope="Purpose",
        architecture_overview="Architecture",
        main_entry_points="Entry points",
        control_flow="Flow",
        key_design_decisions="Decisions",
        external_dependencies="Deps",
    )

    markdown = format_module_documentation(doc_data=doc_data)

    # Find section positions
    entry_pos = markdown.find("## Main Entry Points")
    purpose_pos = markdown.find("## Purpose & Scope")
    arch_pos = markdown.find("## Architecture Overview")
    flow_pos = markdown.find("## Control Flow")
    deps_pos = markdown.find("## External Dependencies")
    decisions_pos = markdown.find("## Key Design Decisions")

    # Verify order: entry points first for quick reference
    assert entry_pos < purpose_pos < arch_pos < flow_pos < deps_pos < decisions_pos


@pytest.mark.parametrize(
    "decision_text",
    [
        "We chose approach A because it provides better performance.",
        "The decision to use pattern X was driven by maintainability concerns.",
        "Multiple factors influenced this choice, including scalability and cost.",
    ],
)
def test_format_module_documentation_decision_formats(decision_text: str) -> None:
    """Test format_module_documentation handles various decision text formats."""
    doc_data = ModuleDocumentation(
        component_name="Test",
        purpose_and_scope="Test",
        architecture_overview="Test architecture",
        main_entry_points="Test entry points",
        control_flow="Test control flow",
        key_design_decisions=decision_text,
    )

    markdown = format_module_documentation(doc_data=doc_data)

    assert "## Key Design Decisions" in markdown
    assert decision_text in markdown


# Tests for format_project_documentation


def test_format_project_documentation_basic_structure() -> None:
    """Test format_project_documentation creates correct basic structure."""
    doc_data = ProjectDocumentation(
        project_name="Test Project",
        project_purpose="Test purpose",
        key_features="Test features",
        installation="Test installation",
        development_setup="Test dev setup",
        usage_examples="Test usage",
        project_structure="Test structure",
        contributing="Test contributing",
    )

    markdown = format_project_documentation(doc_data=doc_data)

    assert markdown.startswith("# Test Project\n")
    assert "## Purpose" in markdown
    assert "## Key Features" in markdown
    assert "## Installation" in markdown
    assert "## Development" in markdown
    assert "## Usage" in markdown
    assert "## Project Structure" in markdown
    assert "## Contributing" in markdown


def test_format_project_documentation_includes_all_fields() -> None:
    """Test format_project_documentation includes all field values."""
    doc_data = ProjectDocumentation(
        project_name="My Project",
        project_purpose="Solves problems",
        key_features="Feature A\nFeature B",
        installation="pip install myproject",
        development_setup="Setup instructions",
        usage_examples="Example usage",
        project_structure="Directory structure",
        contributing="Contribution guidelines",
    )

    markdown = format_project_documentation(doc_data=doc_data)

    assert "# My Project\n" in markdown
    assert "Solves problems" in markdown
    assert "Feature A\nFeature B" in markdown
    assert "pip install myproject" in markdown
    assert "Setup instructions" in markdown
    assert "Example usage" in markdown
    assert "Directory structure" in markdown
    assert "Contribution guidelines" in markdown


def test_format_project_documentation_without_contributing() -> None:
    """Test format_project_documentation handles missing contributing section."""
    doc_data = ProjectDocumentation(
        project_name="Test Project",
        project_purpose="Test purpose",
        key_features="Test features",
        installation="Test installation",
        development_setup="Test dev setup",
        usage_examples="Test usage",
        project_structure="Test structure",
        contributing=None,
    )

    markdown = format_project_documentation(doc_data=doc_data)

    assert "## Contributing" not in markdown


def test_format_project_documentation_section_order() -> None:
    """Test format_project_documentation produces sections in correct order."""
    doc_data = ProjectDocumentation(
        project_name="Test",
        project_purpose="Purpose",
        key_features="Features",
        installation="Install",
        development_setup="Dev",
        usage_examples="Usage",
        project_structure="Structure",
        contributing="Contributing",
    )

    markdown = format_project_documentation(doc_data=doc_data)

    # Section order: Usage first (quick start), then Installation, Features,
    # Purpose, Structure, Development, Contributing
    usage_pos = markdown.find("## Usage")
    install_pos = markdown.find("## Installation")
    features_pos = markdown.find("## Key Features")
    purpose_pos = markdown.find("## Purpose")
    structure_pos = markdown.find("## Project Structure")
    dev_pos = markdown.find("## Development")
    contrib_pos = markdown.find("## Contributing")

    assert (
        usage_pos
        < install_pos
        < features_pos
        < purpose_pos
        < structure_pos
        < dev_pos
        < contrib_pos
    )


def test_format_project_documentation_deterministic() -> None:
    """Test format_project_documentation produces deterministic output."""
    doc_data = ProjectDocumentation(
        project_name="Test",
        project_purpose="Purpose",
        key_features="Features",
        installation="Install",
        development_setup="Dev",
        usage_examples="Usage",
        project_structure="Structure",
    )

    markdown1 = format_project_documentation(doc_data=doc_data)
    markdown2 = format_project_documentation(doc_data=doc_data)

    assert markdown1 == markdown2


# Tests for format_style_guide


def test_format_style_guide_basic_structure() -> None:
    """Test format_style_guide creates correct basic structure."""
    doc_data = StyleGuideDocumentation(
        project_name="Test Project",
        languages=["Python", "TypeScript"],
        code_style_patterns="Test patterns",
        architectural_patterns="Test arch",
        testing_conventions="Test testing",
        git_workflow="Test git",
        module_organization="Test modules",
        dependencies_management="Test deps",
    )

    markdown = format_style_guide(doc_data=doc_data)

    assert markdown.startswith("# Test Project - Style Guide\n")
    assert "## Languages & Tools" in markdown
    assert "## Code Style" in markdown
    assert "## Architecture & Patterns" in markdown
    assert "## Testing Conventions" in markdown
    assert "## Git Workflow" in markdown
    assert "## Module Organization" in markdown
    assert "## Dependencies" in markdown


def test_format_style_guide_includes_all_fields() -> None:
    """Test format_style_guide includes all field values."""
    doc_data = StyleGuideDocumentation(
        project_name="My Project",
        languages=["Python", "JavaScript", "Go"],
        code_style_patterns="Use black for formatting",
        architectural_patterns="MVC pattern",
        testing_conventions="pytest for testing",
        git_workflow="Feature branch workflow",
        module_organization="Flat structure",
        dependencies_management="pip-tools",
    )

    markdown = format_style_guide(doc_data=doc_data)

    assert "# My Project - Style Guide\n" in markdown
    assert "Python, JavaScript, Go" in markdown
    assert "Use black for formatting" in markdown
    assert "MVC pattern" in markdown
    assert "pytest for testing" in markdown
    assert "Feature branch workflow" in markdown
    assert "Flat structure" in markdown
    assert "pip-tools" in markdown


def test_format_style_guide_languages_as_comma_separated() -> None:
    """Test format_style_guide formats languages as comma-separated list."""
    doc_data = StyleGuideDocumentation(
        project_name="Test",
        languages=["Python", "Rust", "TypeScript"],
        code_style_patterns="Patterns",
        architectural_patterns="Arch",
        testing_conventions="Testing",
        git_workflow="Git",
        module_organization="Modules",
        dependencies_management="Deps",
    )

    markdown = format_style_guide(doc_data=doc_data)

    assert "Python, Rust, TypeScript" in markdown


def test_format_style_guide_single_language() -> None:
    """Test format_style_guide handles single language."""
    doc_data = StyleGuideDocumentation(
        project_name="Test",
        languages=["Python"],
        code_style_patterns="Patterns",
        architectural_patterns="Arch",
        testing_conventions="Testing",
        git_workflow="Git",
        module_organization="Modules",
        dependencies_management="Deps",
    )

    markdown = format_style_guide(doc_data=doc_data)

    assert "## Languages & Tools\n\nPython\n\n" in markdown


def test_format_style_guide_section_order() -> None:
    """Test format_style_guide produces sections in correct order."""
    doc_data = StyleGuideDocumentation(
        project_name="Test",
        languages=["Python"],
        code_style_patterns="Patterns",
        architectural_patterns="Arch",
        testing_conventions="Testing",
        git_workflow="Git",
        module_organization="Modules",
        dependencies_management="Deps",
    )

    markdown = format_style_guide(doc_data=doc_data)

    # Section order: Languages & Tools, Code Style, Testing, Architecture,
    # Module Org, Git, Dependencies
    lang_pos = markdown.find("## Languages & Tools")
    style_pos = markdown.find("## Code Style")
    test_pos = markdown.find("## Testing Conventions")
    arch_pos = markdown.find("## Architecture & Patterns")
    mod_pos = markdown.find("## Module Organization")
    git_pos = markdown.find("## Git Workflow")
    deps_pos = markdown.find("## Dependencies")

    assert lang_pos < style_pos < test_pos < arch_pos < mod_pos < git_pos < deps_pos


def test_format_style_guide_deterministic() -> None:
    """Test format_style_guide produces deterministic output."""
    doc_data = StyleGuideDocumentation(
        project_name="Test",
        languages=["Python", "Go"],
        code_style_patterns="Patterns",
        architectural_patterns="Arch",
        testing_conventions="Testing",
        git_workflow="Git",
        module_organization="Modules",
        dependencies_management="Deps",
    )

    markdown1 = format_style_guide(doc_data=doc_data)
    markdown2 = format_style_guide(doc_data=doc_data)

    assert markdown1 == markdown2


def test_format_style_guide_multiline_content() -> None:
    """Test format_style_guide handles multiline content."""
    doc_data = StyleGuideDocumentation(
        project_name="Test",
        languages=["Python"],
        code_style_patterns="Line 1\nLine 2\nLine 3",
        architectural_patterns="Arch line 1\nArch line 2",
        testing_conventions="Testing",
        git_workflow="Git",
        module_organization="Modules",
        dependencies_management="Deps",
    )

    markdown = format_style_guide(doc_data=doc_data)

    assert "Line 1\nLine 2\nLine 3" in markdown
    assert "Arch line 1\nArch line 2" in markdown


def test_format_module_documentation_with_control_flow_diagram() -> None:
    """Test format_module_documentation includes control flow diagram when present."""
    doc_data = ModuleDocumentation(
        component_name="Test Component",
        purpose_and_scope="Test purpose",
        architecture_overview="Test architecture",
        main_entry_points="Test entry points",
        control_flow="Test control flow",
        control_flow_diagram="```mermaid\ngraph TD;\n    A-->B;\n```",
        key_design_decisions="Test decisions",
    )

    markdown = format_module_documentation(doc_data=doc_data)

    assert "```mermaid" in markdown
    assert "graph TD;" in markdown
    assert "A-->B;" in markdown
