"""TOML configuration loading logic for Dokken."""

import sys
from pathlib import Path
from typing import Any, cast

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[import-not-found]

from pydantic import ValidationError

from src.config.merger import merge_config
from src.config.models import CacheConfig, CustomPrompts, DokkenConfig, ExclusionConfig
from src.config.types import ConfigDataDict
from src.file_utils import find_repo_root


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
    config_data: ConfigDataDict = {
        "exclusions": {"files": [], "symbols": []},
        "custom_prompts": {
            "global_prompt": None,
            "module_readme": None,
            "project_readme": None,
            "style_guide": None,
        },
        "cache": {},
        "modules": [],
        "file_types": [".py"],
    }

    # Load global config from repo root if it exists
    repo_root = find_repo_root(module_path)
    if repo_root:
        _load_and_merge_config(Path(repo_root) / ".dokken.toml", config_data)

    # Load module-specific config if it exists (extends global)
    _load_and_merge_config(Path(module_path) / ".dokken.toml", config_data)

    # Construct ExclusionConfig, CustomPrompts, and CacheConfig from merged dictionary
    try:
        exclusion_config = ExclusionConfig(**config_data.get("exclusions", {}))
    except ValidationError as e:
        raise ValueError(f"Invalid exclusions configuration: {e}") from e

    try:
        custom_prompts = CustomPrompts(**config_data.get("custom_prompts", {}))
    except ValidationError as e:
        raise ValueError(f"Invalid custom prompts configuration: {e}") from e

    try:
        cache_config = CacheConfig(**config_data.get("cache", {}))
    except ValidationError as e:
        raise ValueError(f"Invalid cache configuration: {e}") from e

    return DokkenConfig(
        exclusions=exclusion_config,
        custom_prompts=custom_prompts,
        cache=cache_config,
        modules=config_data.get("modules", []),
        file_types=config_data.get("file_types", [".py"]),
    )


def _load_and_merge_config(config_path: Path, base_config: ConfigDataDict) -> None:
    """
    Load a TOML config file and merge it into the base config.

    Args:
        config_path: Path to the .dokken.toml file to load.
        base_config: Base configuration dictionary (modified in-place).
    """
    if config_path.exists():
        with open(config_path, "rb") as f:
            config_data = tomllib.load(f)
            # TypedDict is compatible with dict[str, Any] at runtime
            # Cast for type checker compatibility
            merge_config(cast(dict[str, Any], base_config), config_data)
