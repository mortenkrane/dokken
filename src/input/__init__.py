"""Input handling for documentation generation.

This submodule contains components for gathering input from different sources:
- Code analysis and context extraction
- Interactive human intent questionnaires
"""

from src.input.code_analyzer import get_module_context
from src.input.human_in_the_loop import ask_human_intent

__all__ = ["ask_human_intent", "get_module_context"]
