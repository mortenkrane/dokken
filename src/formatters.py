"""Documentation formatting utilities."""

from src.records import ComponentDocumentation


def generate_markdown(*, doc_data: ComponentDocumentation) -> str:
    """
    Converts the structured Pydantic data into a human-readable Markdown string.

    NOTE: This templating step is CRITICAL for output stability!

    Args:
        doc_data: The structured documentation data.

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
