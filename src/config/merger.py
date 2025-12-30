"""Configuration merging logic for Dokken."""

from typing import Any


def merge_config(base: dict[str, Any], override: dict[str, Any]) -> None:
    """
    Merge override config into base config (in-place).

    For lists, extends the base list with override items (except file_types).
    For dicts, recursively merges.
    For file_types, overrides completely instead of extending.

    Args:
        base: Base configuration dictionary (modified in-place).
        override: Override configuration to merge in.
    """
    for key, value in override.items():
        if key not in base:
            base[key] = value
        elif isinstance(value, dict) and isinstance(base[key], dict):
            merge_config(base[key], value)
        elif isinstance(value, list) and isinstance(base[key], list):
            # file_types should override, not extend
            if key == "file_types":
                base[key] = value
            else:
                # Extend lists (avoid duplicates)
                for item in value:
                    if item not in base[key]:
                        base[key].append(item)
        else:
            base[key] = value
