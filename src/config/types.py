"""Type definitions for Dokken configuration."""

from typing import TypedDict


class ExclusionsDict(TypedDict, total=False):
    """Structure of the exclusions section in .dokken.toml."""

    files: list[str]
    symbols: list[str]


class CustomPromptsDict(TypedDict, total=False):
    """Structure of the custom_prompts section in .dokken.toml."""

    global_prompt: str | None
    module_readme: str | None
    project_readme: str | None
    style_guide: str | None


class ConfigDataDict(TypedDict, total=False):
    """Structure of .dokken.toml file."""

    exclusions: ExclusionsDict
    custom_prompts: CustomPromptsDict
    modules: list[str]
