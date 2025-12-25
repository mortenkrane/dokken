"""Configuration loading for Dokken exclusion rules."""

from src.config.loader import load_config
from src.config.models import CustomPrompts, DokkenConfig, ExclusionConfig

__all__ = [
    "CustomPrompts",
    "DokkenConfig",
    "ExclusionConfig",
    "load_config",
]
