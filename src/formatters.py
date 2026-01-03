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

    Template optimized for search/reference:
    - Entry points first (quick start)
    - Scannable structure for both AI and human readers
    - Keyword-rich section headers

    Args:
        doc_data: The structured module documentation data.

    Returns:
        A formatted Markdown string.
    """
    md = f"# {doc_data.component_name}\n\n"

    # Quick reference section - entry points first for immediate use
    md += f"## Main Entry Points\n\n{doc_data.main_entry_points}\n\n"

    # Purpose and scope - what this module does
    md += f"## Purpose & Scope\n\n{doc_data.purpose_and_scope}\n\n"

    # Module structure - key files and submodules (if present)
    if doc_data.module_structure:
        md += f"## Module Structure\n\n{doc_data.module_structure}\n\n"

    # Architecture - how it's structured
    md += f"## Architecture Overview\n\n{doc_data.architecture_overview}\n\n"

    # Control flow - how it works
    md += f"## Control Flow\n\n{doc_data.control_flow}\n\n"

    # Add control flow diagram if present
    if doc_data.control_flow_diagram:
        md += f"{doc_data.control_flow_diagram}\n\n"

    # External dependencies - what it uses
    if doc_data.external_dependencies:
        md += f"## External Dependencies\n\n{doc_data.external_dependencies}\n\n"

    # Design decisions - why it's built this way
    md += f"## Key Design Decisions\n\n{doc_data.key_design_decisions}\n\n"

    return md


def format_project_documentation(*, doc_data: ProjectDocumentation) -> str:
    """
    Converts project documentation to a human-readable Markdown string.

    Template optimized for search/reference:
    - Usage first (quick start)
    - Installation before detailed explanations
    - Structure optimized for grep/search
    - Keyword-rich headers

    Args:
        doc_data: The structured project documentation data.

    Returns:
        A formatted Markdown string for a top-level README.
    """
    md = f"# {doc_data.project_name}\n\n"

    # Quick start - usage examples first
    md += f"## Usage\n\n{doc_data.usage_examples}\n\n"

    # Installation - how to get started
    md += f"## Installation\n\n{doc_data.installation}\n\n"

    # Key features - what this project offers
    md += f"## Key Features\n\n{doc_data.key_features}\n\n"

    # Purpose - why this project exists
    md += f"## Purpose\n\n{doc_data.project_purpose}\n\n"

    # Project structure - where to find things
    md += f"## Project Structure\n\n{doc_data.project_structure}\n\n"

    # Development setup - for contributors
    md += f"## Development\n\n{doc_data.development_setup}\n\n"

    # Contributing guidelines if present
    if doc_data.contributing:
        md += f"## Contributing\n\n{doc_data.contributing}\n\n"

    return md


def format_style_guide(*, doc_data: StyleGuideDocumentation) -> str:
    """
    Converts style guide documentation to a human-readable Markdown string.

    Template optimized for search/reference:
    - Practical sections first (code style, testing)
    - Process sections after (git, dependencies)
    - Keyword-rich headers for easy navigation

    Args:
        doc_data: The structured style guide documentation data.

    Returns:
        A formatted Markdown string for a style guide.
    """
    md = f"# {doc_data.project_name} - Style Guide\n\n"

    # Languages overview
    md += f"## Languages & Tools\n\n{', '.join(doc_data.languages)}\n\n"

    # Code style - most frequently referenced section
    md += f"## Code Style\n\n{doc_data.code_style_patterns}\n\n"

    # Testing - critical for contributors
    md += f"## Testing Conventions\n\n{doc_data.testing_conventions}\n\n"

    # Architecture - design patterns and structure
    md += f"## Architecture & Patterns\n\n{doc_data.architectural_patterns}\n\n"

    # Module organization - where things go
    md += f"## Module Organization\n\n{doc_data.module_organization}\n\n"

    # Git workflow - branching and commits
    md += f"## Git Workflow\n\n{doc_data.git_workflow}\n\n"

    # Dependencies - package management
    md += f"## Dependencies\n\n{doc_data.dependencies_management}\n\n"

    return md
