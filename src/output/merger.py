"""Document merging utilities for applying incremental fixes.

This module provides functions for parsing markdown documentation into sections
and applying targeted, incremental changes without regenerating entire documents.
Used by the drift-fixing workflow to preserve existing documentation structure
while updating only what changed.

Key functions:
- parse_sections(): Parse markdown into section dictionary
- apply_incremental_fixes(): Apply targeted changes to existing documentation
"""

from src.records import IncrementalDocumentationFix


def _save_section(
    sections: dict[str, str | list[str]], section_name: str, content: list[str]
) -> None:
    """Save a section's content to the sections dictionary."""
    sections[section_name] = "\n".join(content)


def _add_to_preamble(sections: dict[str, str | list[str]], line: str) -> None:
    """Add a line to the preamble section."""
    if "_preamble" not in sections:
        sections["_preamble"] = []
    preamble = sections["_preamble"]
    if isinstance(preamble, list):
        preamble.append(line)


def parse_sections(markdown: str) -> dict[str, str]:
    """
    Parse a markdown document into sections keyed by header.

    Args:
        markdown: The markdown document to parse.

    Returns:
        Dictionary mapping section headers to their content (including header).
    """
    sections: dict[str, str | list[str]] = {}
    current_section = None
    current_content = []

    for line in markdown.split("\n"):
        if line.startswith("## "):
            # Save previous section before starting new one
            if current_section is not None:
                _save_section(sections, current_section, current_content)

            # Start new section
            current_section = line[3:].strip()
            current_content = [line]
        elif current_section is not None:
            # Add to current section
            current_content.append(line)
        else:
            # Add to preamble
            _add_to_preamble(sections, line)

    # Save last section
    if current_section is not None:
        _save_section(sections, current_section, current_content)

    # Type checker knows all values are now str after finalization
    return _flatten_values(sections)


def _flatten_values(sections: dict[str, str | list[str]]) -> dict[str, str]:
    # Finalize preamble and other values - convert list to string
    new_sections: dict[str, str] = {}
    for key, value in sections.items():
        if isinstance(value, list):
            new_sections[key] = "\n".join(value)
        else:
            new_sections[key] = value
    return new_sections


def _apply_change(
    sections: dict[str, str], section_header: str, change_type: str, content: str
) -> None:
    """Apply a single change to the sections dictionary."""
    if change_type in {"update", "add"}:
        # Clean up content: remove header if LLM included it, strip trailing whitespace
        cleaned_content = content.strip()
        header_line = f"## {section_header}"

        # Remove duplicate header if LLM included it in the content
        if cleaned_content.startswith(header_line):
            cleaned_content = cleaned_content[len(header_line) :].lstrip()

        sections[section_header] = f"{header_line}\n\n{cleaned_content}"
    elif change_type == "remove":
        sections.pop(section_header, None)


def _reconstruct_document(sections: dict[str, str], original_doc: str) -> str:
    """Reconstruct document maintaining original section order."""
    result_parts = []

    # Start with preamble
    if "_preamble" in sections:
        result_parts.append(sections["_preamble"])

    # Get original section order
    original_sections = parse_sections(original_doc)
    original_order = [k for k in original_sections if k != "_preamble"]

    # Add original sections (skipping removed ones)
    added_sections = set()
    for section_header in original_order:
        if section_header in sections:
            result_parts.append(sections[section_header])
            added_sections.add(section_header)

    # Add new sections at the end
    for section_header, content in sections.items():
        if section_header != "_preamble" and section_header not in added_sections:
            result_parts.append(content)

    return "\n\n".join(result_parts) + "\n"


def apply_incremental_fixes(
    *,
    current_doc: str,
    fixes: IncrementalDocumentationFix,
) -> str:
    """
    Apply incremental fixes to existing documentation.

    Merges targeted changes back into the original documentation,
    preserving sections that weren't modified and maintaining the
    overall structure and formatting.

    Args:
        current_doc: The existing documentation content.
        fixes: The incremental fixes to apply.

    Returns:
        The updated documentation with fixes applied.
    """
    sections = parse_sections(current_doc)

    # Apply each change
    for change in fixes.changes:
        _apply_change(
            sections, change.section, change.change_type, change.updated_content
        )

    # Reconstruct document
    return _reconstruct_document(sections, current_doc)
