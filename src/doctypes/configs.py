"""Doc type configuration registry.

This module defines the configuration for each documentation type,
keeping generation config separate from path resolution logic.
"""

from collections.abc import Callable
from dataclasses import dataclass

from pydantic import BaseModel

from src.constants import (
    DEFAULT_DEPTH_MODULE,
    DEFAULT_DEPTH_PROJECT,
    DEFAULT_DEPTH_STYLE_GUIDE,
)
from src.doctypes.types import DocType
from src.llm import prompts
from src.output import formatters
from src.records import (
    ModuleDocumentation,
    ModuleIntent,
    ProjectDocumentation,
    ProjectIntent,
    StyleGuideDocumentation,
    StyleGuideIntent,
)


@dataclass
class DocConfig:
    """Configuration for documentation generation (NOT path resolution).

    This class contains all the configuration needed for generating documentation
    for a specific doc type (MODULE_README, PROJECT_README, STYLE_GUIDE).
    """

    model: type[BaseModel]  # Pydantic model for structured output
    prompt: str  # Prompt template
    formatter: Callable[..., str]  # Formatter function (keyword-only args)
    intent_model: type[BaseModel]  # Intent model for human-in-the-loop
    intent_questions: list[dict[str, str]]  # Questions for intent capture
    default_depth: int  # Default code analysis depth
    analyze_entire_repo: bool  # Whether to analyze entire repo vs module


# Registry mapping doc types to their configurations
DOC_CONFIGS: dict[DocType, DocConfig] = {
    DocType.MODULE_README: DocConfig(
        model=ModuleDocumentation,
        prompt=prompts.MODULE_GENERATION_PROMPT,
        formatter=formatters.format_module_documentation,
        intent_model=ModuleIntent,
        intent_questions=[
            {
                "key": "problems_solved",
                "question": "What problems does this module solve?",
            },
            {
                "key": "core_responsibilities",
                "question": "What are the module's core responsibilities?",
            },
            {
                "key": "non_responsibilities",
                "question": "What is NOT this module's responsibility?",
            },
            {
                "key": "system_context",
                "question": "How does the module fit into the larger system?",
            },
        ],
        default_depth=DEFAULT_DEPTH_MODULE,
        analyze_entire_repo=False,
    ),
    DocType.PROJECT_README: DocConfig(
        model=ProjectDocumentation,
        prompt=prompts.PROJECT_README_GENERATION_PROMPT,
        formatter=formatters.format_project_documentation,
        intent_model=ProjectIntent,
        intent_questions=[
            {
                "key": "project_type",
                "question": "Is this a library/tool/application/framework?",
            },
            {
                "key": "target_audience",
                "question": "Who is the primary audience?",
            },
            {
                "key": "key_problem",
                "question": "What problem does this project solve?",
            },
            {
                "key": "setup_notes",
                "question": "Any special setup considerations?",
            },
        ],
        default_depth=DEFAULT_DEPTH_PROJECT,
        analyze_entire_repo=True,
    ),
    DocType.STYLE_GUIDE: DocConfig(
        model=StyleGuideDocumentation,
        prompt=prompts.STYLE_GUIDE_GENERATION_PROMPT,
        formatter=formatters.format_style_guide,
        intent_model=StyleGuideIntent,
        intent_questions=[
            {
                "key": "unique_conventions",
                "question": "Are there any unique conventions in this codebase?",
            },
            {
                "key": "organization_notes",
                "question": (
                    "What should new contributors know about code organization?"
                ),
            },
            {
                "key": "patterns",
                "question": "Are there specific patterns to follow or avoid?",
            },
        ],
        default_depth=DEFAULT_DEPTH_STYLE_GUIDE,
        analyze_entire_repo=True,
    ),
}
