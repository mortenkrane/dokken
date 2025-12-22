"""Configuration loading for Dokken exclusion rules."""

import tomllib
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from src.utils import find_repo_root


class ExclusionConfig(BaseModel):
    """Configuration for excluding files and symbols from documentation."""

    files: list[str] = Field(
        default_factory=list,
        description="List of file patterns to exclude (supports glob patterns)",
    )
    symbols: list[str] = Field(
        default_factory=list,
        description="List of symbol names to exclude (supports wildcards)",
    )


class CustomPrompts(BaseModel):
    """Custom prompts for documentation generation."""

    global_prompt: str | None = Field(
        default=None,
        description="Global custom prompt applied to all doc types",
        max_length=5000,
    )
    module_readme: str | None = Field(
        default=None,
        description="Custom prompt for module README documentation",
        max_length=5000,
    )
    project_readme: str | None = Field(
        default=None,
        description="Custom prompt for project README documentation",
        max_length=5000,
    )
    style_guide: str | None = Field(
        default=None,
        description="Custom prompt for style guide documentation",
        max_length=5000,
    )


class DokkenConfig(BaseModel):
    """Root configuration for Dokken."""

    exclusions: ExclusionConfig = Field(default_factory=ExclusionConfig)
    custom_prompts: CustomPrompts = Field(default_factory=CustomPrompts)
    modules: list[str] = Field(
        default_factory=list,
        description="List of module paths to check for drift (relative to repo root)",
    )


def load_config(*, module_path: str) -> DokkenConfig:
    """
    Load Dokken configuration from .dokken.toml files.

    Searches for config files in this order (later configs override earlier):
    1. Repository root .dokken.toml (global)
    2. Module directory .dokken.toml (module-specific)

    Args:
        module_path: Path to the module directory being documented.

    Returns:
        DokkenConfig with merged configuration from all sources.
    """
    config_data = {
        "exclusions": {"files": [], "symbols": []},
        "custom_prompts": {
            "global_prompt": None,
            "module_readme": None,
            "project_readme": None,
            "style_guide": None,
        },
        "modules": [],
    }

    # Load global config from repo root if it exists
    repo_root = find_repo_root(module_path)
    if repo_root:
        _load_and_merge_config(Path(repo_root) / ".dokken.toml", config_data)

    # Load module-specific config if it exists (extends global)
    _load_and_merge_config(Path(module_path) / ".dokken.toml", config_data)

    # Construct ExclusionConfig and CustomPrompts from the merged dictionary
    try:
        exclusion_config = ExclusionConfig(**config_data["exclusions"])  # type: ignore
    except ValidationError as e:
        raise ValueError(f"Invalid exclusions configuration: {e}") from e

    try:
        custom_prompts = CustomPrompts(**config_data["custom_prompts"])  # type: ignore
    except ValidationError as e:
        raise ValueError(f"Invalid custom prompts configuration: {e}") from e

    return DokkenConfig(
        exclusions=exclusion_config,
        custom_prompts=custom_prompts,
        modules=config_data["modules"],
    )


def _load_and_merge_config(config_path: Path, base_config: dict) -> None:
    """
    Load a TOML config file and merge it into the base config.

    Args:
        config_path: Path to the .dokken.toml file to load.
        base_config: Base configuration dictionary (modified in-place).
    """
    if config_path.exists():
        with open(config_path, "rb") as f:
            config_data = tomllib.load(f)
            _merge_config(base_config, config_data)


def _merge_config(base: dict, override: dict) -> None:
    """
    Merge override config into base config (in-place).

    For lists, extends the base list with override items.
    For dicts, recursively merges.

    Args:
        base: Base configuration dictionary (modified in-place).
        override: Override configuration to merge in.
    """
    for key, value in override.items():
        if key not in base:
            base[key] = value
        elif isinstance(value, dict) and isinstance(base[key], dict):
            _merge_config(base[key], value)
        elif isinstance(value, list) and isinstance(base[key], list):
            # Extend lists (avoid duplicates)
            for item in value:
                if item not in base[key]:
                    base[key].append(item)
        else:
            base[key] = value
