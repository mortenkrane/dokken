"""Output formatting and document manipulation utilities.

This module handles all output generation and transformation:
- Formatters: Convert structured data to markdown
- Merger: Parse and transform existing markdown documents
"""

from src.output.formatters import (
    format_module_documentation,
    format_project_documentation,
    format_style_guide,
)
from src.output.merger import apply_incremental_fixes, parse_sections

__all__ = [
    "apply_incremental_fixes",
    "format_module_documentation",
    "format_project_documentation",
    "format_style_guide",
    "parse_sections",
]
