"""Documentation formatting utilities."""

from src.constants import (
    SECTION_ARCHITECTURE_OVERVIEW,
    SECTION_ARCHITECTURE_PATTERNS,
    SECTION_CODE_STYLE,
    SECTION_CONTRIBUTING,
    SECTION_CONTROL_FLOW,
    SECTION_DEPENDENCIES,
    SECTION_DEVELOPMENT,
    SECTION_EXTERNAL_DEPENDENCIES,
    SECTION_GIT_WORKFLOW,
    SECTION_INSTALLATION,
    SECTION_KEY_DESIGN_DECISIONS,
    SECTION_KEY_FEATURES,
    SECTION_LANGUAGES_TOOLS,
    SECTION_MAIN_ENTRY_POINTS,
    SECTION_MODULE_ORGANIZATION,
    SECTION_MODULE_STRUCTURE,
    SECTION_PROJECT_STRUCTURE,
    SECTION_PURPOSE,
    SECTION_PURPOSE_SCOPE,
    SECTION_TESTING_CONVENTIONS,
    SECTION_USAGE,
)
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
    md += f"{SECTION_MAIN_ENTRY_POINTS}\n\n{doc_data.main_entry_points}\n\n"

    # Purpose and scope - what this module does
    md += f"{SECTION_PURPOSE_SCOPE}\n\n{doc_data.purpose_and_scope}\n\n"

    # Module structure - key files and submodules (if present)
    if doc_data.module_structure:
        md += f"{SECTION_MODULE_STRUCTURE}\n\n{doc_data.module_structure}\n\n"

    # Architecture - how it's structured
    md += f"{SECTION_ARCHITECTURE_OVERVIEW}\n\n{doc_data.architecture_overview}\n\n"

    # Control flow - how it works
    md += f"{SECTION_CONTROL_FLOW}\n\n{doc_data.control_flow}\n\n"

    # Add control flow diagram if present
    if doc_data.control_flow_diagram:
        md += f"{doc_data.control_flow_diagram}\n\n"

    # External dependencies - what it uses
    if doc_data.external_dependencies:
        md += f"{SECTION_EXTERNAL_DEPENDENCIES}\n\n{doc_data.external_dependencies}\n\n"

    # Design decisions - why it's built this way
    md += f"{SECTION_KEY_DESIGN_DECISIONS}\n\n{doc_data.key_design_decisions}\n\n"

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
    md += f"{SECTION_USAGE}\n\n{doc_data.usage_examples}\n\n"

    # Installation - how to get started
    md += f"{SECTION_INSTALLATION}\n\n{doc_data.installation}\n\n"

    # Key features - what this project offers
    md += f"{SECTION_KEY_FEATURES}\n\n{doc_data.key_features}\n\n"

    # Purpose - why this project exists
    md += f"{SECTION_PURPOSE}\n\n{doc_data.project_purpose}\n\n"

    # Project structure - where to find things
    md += f"{SECTION_PROJECT_STRUCTURE}\n\n{doc_data.project_structure}\n\n"

    # Development setup - for contributors
    md += f"{SECTION_DEVELOPMENT}\n\n{doc_data.development_setup}\n\n"

    # Contributing guidelines if present
    if doc_data.contributing:
        md += f"{SECTION_CONTRIBUTING}\n\n{doc_data.contributing}\n\n"

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
    md += f"{SECTION_LANGUAGES_TOOLS}\n\n{', '.join(doc_data.languages)}\n\n"

    # Code style - most frequently referenced section
    md += f"{SECTION_CODE_STYLE}\n\n{doc_data.code_style_patterns}\n\n"

    # Testing - critical for contributors
    md += f"{SECTION_TESTING_CONVENTIONS}\n\n{doc_data.testing_conventions}\n\n"

    # Architecture - design patterns and structure
    md += f"{SECTION_ARCHITECTURE_PATTERNS}\n\n{doc_data.architectural_patterns}\n\n"

    # Module organization - where things go
    md += f"{SECTION_MODULE_ORGANIZATION}\n\n{doc_data.module_organization}\n\n"

    # Git workflow - branching and commits
    md += f"{SECTION_GIT_WORKFLOW}\n\n{doc_data.git_workflow}\n\n"

    # Dependencies - package management
    md += f"{SECTION_DEPENDENCIES}\n\n{doc_data.dependencies_management}\n\n"

    return md
