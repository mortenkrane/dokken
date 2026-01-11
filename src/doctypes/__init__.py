"""Documentation type system.

This module defines the types of documentation that can be generated
and their associated configuration (prompts, formatters, intent models).
"""

from src.doctypes.configs import DOC_CONFIGS, AnyDocConfig, DocConfig
from src.doctypes.types import DocType

__all__ = [
    "DOC_CONFIGS",
    "AnyDocConfig",
    "DocConfig",
    "DocType",
]
