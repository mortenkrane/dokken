"""Documentation type definitions."""

from enum import Enum


class DocType(str, Enum):
    """Types of documentation that can be generated."""

    MODULE_README = "module-readme"
    PROJECT_README = "project-readme"
    STYLE_GUIDE = "style-guide"
