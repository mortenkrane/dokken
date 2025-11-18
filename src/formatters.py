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
    md = f"# {doc_data.component_name} Overview\n\n"
    md += f"## Purpose & Scope\n\n{doc_data.purpose_and_scope}\n\n"

    if doc_data.external_dependencies:
        md += f"## External Dependencies\n\n{doc_data.external_dependencies}\n\n"

    md += "## Key Design Decisions (The 'Why')\n\n"

    # Sort keys for deterministic output to prevent diff noise
    sorted_decisions = sorted(doc_data.design_decisions.items())

    for key, decision_text in sorted_decisions:
        md += f"### Decision: {key}\n\n"
        md += f"{decision_text}\n\n"

    return md
