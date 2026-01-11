"""TOML configuration loading logic for Dokken."""

import sys
from pathlib import Path
from typing import Any, TypeVar, cast

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[import-not-found]

from pydantic import BaseModel, ValidationError
from rich.console import Console

from src.config.merger import merge_config
from src.config.models import CacheConfig, CustomPrompts, DokkenConfig, ExclusionConfig
from src.config.types import ConfigDataDict
from src.file_utils import find_repo_root
from src.security.input_validation import validate_custom_prompt

# Console for error/warning output
error_console = Console(stderr=True)

# Type variable for config validation helper
T = TypeVar("T", bound=BaseModel)


def _validate_config_section(
    config_data: ConfigDataDict,
    section_name: str,
    model_class: type[T],
) -> T:
    """
    Validate and construct a config section with clear error messages.

    Args:
        config_data: The full configuration dictionary.
        section_name: The name of the section being validated (for error messages).
        model_class: The Pydantic model class to validate against.

    Returns:
        Validated config section instance.

    Raises:
        ValueError: If the configuration fails validation.
    """
    try:
        return model_class(**config_data.get(section_name, {}))
    except ValidationError as e:
        raise ValueError(f"Invalid {section_name} configuration: {e}") from e


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
        "exclusions": {"files": []},
        "custom_prompts": {
            "global_prompt": None,
            "module_readme": None,
            "project_readme": None,
            "style_guide": None,
        },
        "cache": {},
        "modules": [],
        "file_types": [".py"],
        "file_depth": None,
    }

    # Load global config from repo root if it exists
    repo_root = find_repo_root(module_path)
    if repo_root:
        _load_and_merge_config(Path(repo_root) / ".dokken.toml", config_data)

    # Load module-specific config if it exists (extends global)
    _load_and_merge_config(Path(module_path) / ".dokken.toml", config_data)

    # Construct ExclusionConfig, CustomPrompts, and CacheConfig from merged dictionary
    exclusion_config = _validate_config_section(
        config_data, "exclusions", ExclusionConfig
    )

    custom_prompts = _validate_config_section(
        config_data, "custom_prompts", CustomPrompts
    )

    # Validate custom prompts for suspicious patterns
    _validate_custom_prompts(custom_prompts)

    cache_config = _validate_config_section(config_data, "cache", CacheConfig)

    return DokkenConfig(
        exclusions=exclusion_config,
        custom_prompts=custom_prompts,
        cache=cache_config,
        modules=config_data.get("modules", []),
        file_types=config_data.get("file_types", [".py"]),
        file_depth=config_data.get("file_depth"),
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


def _validate_custom_prompts(custom_prompts: CustomPrompts) -> None:
    """
    Validate custom prompts for suspicious patterns indicating prompt injection.

    Prints warnings to stderr if suspicious patterns are detected, but does not
    prevent the prompts from being used (warning system, not a hard block).

    Args:
        custom_prompts: The custom prompts configuration to validate.
    """
    prompt_fields = [
        ("global_prompt", custom_prompts.global_prompt),
        ("module_readme", custom_prompts.module_readme),
        ("project_readme", custom_prompts.project_readme),
        ("style_guide", custom_prompts.style_guide),
    ]

    for prompt_type, prompt_text in prompt_fields:
        if prompt_text:
            result = validate_custom_prompt(prompt_text)
            if result.is_suspicious:
                error_console.print(
                    f"\n⚠️  WARNING: Suspicious pattern detected in "
                    f"custom_prompts.{prompt_type}"
                )
                for warning in result.warnings:
                    error_console.print(f"   - {warning}")
                if result.severity == "high":
                    error_console.print(f"   Severity: {result.severity.upper()}")
                    error_console.print(
                        "   This prompt may attempt to manipulate "
                        "documentation generation."
                    )
                    error_console.print("   Review .dokken.toml carefully.\n")
