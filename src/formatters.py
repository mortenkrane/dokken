"""Documentation formatting utilities."""

from src.records import (
    ModuleDocumentation,
    ProjectDocumentation,
    StyleGuideDocumentation,
)


def format_module_documentation(*, doc_data: ModuleDocumentation) -> str:
    """
    Converts module documentation to a human-readable Markdown string.

    NOTE: This templating step is CRITICAL for output stability!

    Args:
        doc_data: The structured module documentation data.

    Returns:
        A formatted Markdown string.
    """
    md = f"# {doc_data.component_name}\n\n"
    md += f"## Purpose & Scope\n\n{doc_data.purpose_and_scope}\n\n"
    md += f"## Architecture Overview\n\n{doc_data.architecture_overview}\n\n"
    md += f"## Main Entry Points\n\n{doc_data.main_entry_points}\n\n"
    md += f"## Control Flow\n\n{doc_data.control_flow}\n\n"

    if doc_data.external_dependencies:
        md += f"## External Dependencies\n\n{doc_data.external_dependencies}\n\n"

    md += f"## Key Design Decisions\n\n{doc_data.key_design_decisions}\n\n"

    return md


def format_project_documentation(*, doc_data: ProjectDocumentation) -> str:
    """
    Converts project documentation to a human-readable Markdown string.

    Args:
        doc_data: The structured project documentation data.

    Returns:
        A formatted Markdown string for a top-level README.
    """
    md = f"# {doc_data.project_name}\n\n"
    md += f"## Purpose\n\n{doc_data.project_purpose}\n\n"
    md += f"## Key Features\n\n{doc_data.key_features}\n\n"
    md += f"## Installation\n\n{doc_data.installation}\n\n"
    md += f"## Development Setup\n\n{doc_data.development_setup}\n\n"
    md += f"## Usage\n\n{doc_data.usage_examples}\n\n"
    md += f"## Project Structure\n\n{doc_data.project_structure}\n\n"

    if doc_data.contributing:
        md += f"## Contributing\n\n{doc_data.contributing}\n\n"

    return md


def format_style_guide(*, doc_data: StyleGuideDocumentation) -> str:
    """
    Converts style guide documentation to a human-readable Markdown string.

    Args:
        doc_data: The structured style guide documentation data.

    Returns:
        A formatted Markdown string for a style guide.
    """
    md = f"# {doc_data.project_name} Style Guide\n\n"
    md += f"## Languages\n\n{', '.join(doc_data.languages)}\n\n"
    md += f"## Code Style Patterns\n\n{doc_data.code_style_patterns}\n\n"
    md += f"## Architectural Patterns\n\n{doc_data.architectural_patterns}\n\n"
    md += f"## Testing Conventions\n\n{doc_data.testing_conventions}\n\n"
    md += f"## Git Workflow\n\n{doc_data.git_workflow}\n\n"
    md += f"## Module Organization\n\n{doc_data.module_organization}\n\n"
    md += f"## Dependencies Management\n\n{doc_data.dependencies_management}\n\n"

    return md


# Backward compatibility alias
generate_markdown = format_module_documentation
