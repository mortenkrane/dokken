"""Type definitions for Dokken configuration."""

from typing import TypedDict


class ExclusionsDict(TypedDict, total=False):
    """Structure of the exclusions section in .dokken.toml."""

    files: list[str]


class CustomPromptsDict(TypedDict, total=False):
    """Structure of the custom_prompts section in .dokken.toml."""

    global_prompt: str | None
    module_readme: str | None
    project_readme: str | None
    style_guide: str | None


class CacheDict(TypedDict, total=False):
    """Structure of the cache section in .dokken.toml."""

    file: str
    max_size: int


class ConfigDataDict(TypedDict, total=False):
    """Structure of .dokken.toml file."""

    exclusions: ExclusionsDict
    custom_prompts: CustomPromptsDict
    cache: CacheDict
    modules: list[str]
    file_types: list[str]
    file_depth: int | None
