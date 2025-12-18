"""Configuration loading for Dokken exclusion rules."""

import tomllib
from pathlib import Path

from pydantic import BaseModel, Field


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


class DokkenConfig(BaseModel):
    """Root configuration for Dokken."""

    exclusions: ExclusionConfig = Field(default_factory=ExclusionConfig)


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
    config_data = {"exclusions": {"files": [], "symbols": []}}

    # Load global config from repo root if it exists
    repo_root = _find_repo_root(module_path)
    if repo_root:
        _load_and_merge_config(Path(repo_root) / ".dokken.toml", config_data)

    # Load module-specific config if it exists (extends global)
    _load_and_merge_config(Path(module_path) / ".dokken.toml", config_data)

    return DokkenConfig(**config_data)


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


def _find_repo_root(start_path: str) -> str | None:
    """
    Find the repository root by searching for .git directory.

    Args:
        start_path: Path to start searching from.

    Returns:
        Path to repository root, or None if not found.
    """
    current = Path(start_path).resolve()

    # Search up the directory tree
    while current != current.parent:
        if (current / ".git").exists():
            return str(current)
        current = current.parent

    return None


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
