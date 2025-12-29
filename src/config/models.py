"""Pydantic models for Dokken configuration."""

from pydantic import BaseModel, Field

from src.constants import DEFAULT_CACHE_FILE, DRIFT_CACHE_SIZE


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


class CacheConfig(BaseModel):
    """Configuration for drift detection caching."""

    file: str = Field(
        default=DEFAULT_CACHE_FILE,
        description="Path to the cache file for persisting drift detection results",
    )
    max_size: int = Field(
        default=DRIFT_CACHE_SIZE,
        description="Maximum number of entries to keep in the cache",
        gt=0,
    )


class DokkenConfig(BaseModel):
    """Root configuration for Dokken."""

    exclusions: ExclusionConfig = Field(default_factory=ExclusionConfig)
    custom_prompts: CustomPrompts = Field(default_factory=CustomPrompts)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    modules: list[str] = Field(
        default_factory=list,
        description="List of module paths to check for drift (relative to repo root)",
    )
