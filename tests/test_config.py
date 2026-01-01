"""Tests for src/config.py"""

from pathlib import Path

import pytest

from src.config import CustomPrompts, DokkenConfig, ExclusionConfig, load_config


def test_exclusion_config_defaults() -> None:
    """Test ExclusionConfig has correct defaults."""
    config = ExclusionConfig()

    assert config.files == []
    assert config.symbols == []


def test_dokken_config_defaults() -> None:
    """Test DokkenConfig has correct defaults."""
    config = DokkenConfig()

    assert isinstance(config.exclusions, ExclusionConfig)
    assert config.exclusions.files == []
    assert config.exclusions.symbols == []
    assert config.file_types == [".py"]
    assert config.file_depth is None


def test_load_config_no_config_file(tmp_path: Path) -> None:
    """Test load_config returns default config when no .dokken.toml exists."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    config = load_config(module_path=str(module_dir))

    assert config.exclusions.files == []
    assert config.exclusions.symbols == []


def test_load_config_module_level_config(tmp_path: Path) -> None:
    """Test load_config loads module-level .dokken.toml."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    config_content = """
[exclusions]
files = ["__init__.py", "*_test.py"]
symbols = ["_private_*", "setup"]
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    config = load_config(module_path=str(module_dir))

    assert config.exclusions.files == ["__init__.py", "*_test.py"]
    assert config.exclusions.symbols == ["_private_*", "setup"]


def test_load_config_repo_level_config(tmp_path: Path) -> None:
    """Test load_config loads repo-level .dokken.toml."""
    # Create repo structure with .git
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    module_dir = repo_root / "src" / "module"
    module_dir.mkdir(parents=True)

    # Create repo-level config
    repo_config = """
[exclusions]
files = ["conftest.py"]
symbols = ["test_*"]
"""
    (repo_root / ".dokken.toml").write_text(repo_config)

    config = load_config(module_path=str(module_dir))

    assert config.exclusions.files == ["conftest.py"]
    assert config.exclusions.symbols == ["test_*"]


def test_load_config_merge_module_and_repo(tmp_path: Path) -> None:
    """Test module-level config extends repo-level config."""
    # Create repo structure
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    module_dir = repo_root / "src" / "module"
    module_dir.mkdir(parents=True)

    # Create repo-level config
    repo_config = """
[exclusions]
files = ["conftest.py"]
symbols = ["test_*"]
"""
    (repo_root / ".dokken.toml").write_text(repo_config)

    # Create module-level config
    module_config = """
[exclusions]
files = ["__init__.py"]
symbols = ["_private_*"]
"""
    (module_dir / ".dokken.toml").write_text(module_config)

    config = load_config(module_path=str(module_dir))

    # Both configs should be merged (no duplicates)
    assert set(config.exclusions.files) == {"conftest.py", "__init__.py"}
    assert set(config.exclusions.symbols) == {"test_*", "_private_*"}


def test_load_config_no_duplicates(tmp_path: Path) -> None:
    """Test that merged configs don't create duplicates."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    module_dir = repo_root / "src" / "module"
    module_dir.mkdir(parents=True)

    # Both configs have overlapping exclusions
    repo_config = """
[exclusions]
files = ["__init__.py", "conftest.py"]
symbols = ["test_*"]
"""
    (repo_root / ".dokken.toml").write_text(repo_config)

    module_config = """
[exclusions]
files = ["__init__.py"]
symbols = ["test_*", "_private_*"]
"""
    (module_dir / ".dokken.toml").write_text(module_config)

    config = load_config(module_path=str(module_dir))

    # Check no duplicates
    assert config.exclusions.files.count("__init__.py") == 1
    assert config.exclusions.symbols.count("test_*") == 1
    assert set(config.exclusions.files) == {"__init__.py", "conftest.py"}
    assert set(config.exclusions.symbols) == {"test_*", "_private_*"}


def test_load_config_empty_exclusions(tmp_path: Path) -> None:
    """Test load_config handles empty exclusions sections."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    config_content = """
[exclusions]
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    config = load_config(module_path=str(module_dir))

    assert config.exclusions.files == []
    assert config.exclusions.symbols == []


def test_load_config_no_exclusions_section(tmp_path: Path) -> None:
    """Test load_config handles missing [exclusions] section."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    # Config file with no exclusions section
    config_content = """
[other_section]
key = "value"
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    config = load_config(module_path=str(module_dir))

    # Should use defaults
    assert config.exclusions.files == []
    assert config.exclusions.symbols == []


# --- Tests for CustomPrompts ---


def test_custom_prompts_defaults() -> None:
    """Test CustomPrompts has correct defaults."""
    prompts = CustomPrompts()

    assert prompts.global_prompt is None
    assert prompts.module_readme is None
    assert prompts.project_readme is None
    assert prompts.style_guide is None


def test_dokken_config_includes_custom_prompts() -> None:
    """Test DokkenConfig includes custom_prompts field."""
    config = DokkenConfig()

    assert isinstance(config.custom_prompts, CustomPrompts)
    assert config.custom_prompts.global_prompt is None


def test_load_config_with_global_custom_prompt(tmp_path: Path) -> None:
    """Test load_config loads global custom prompt."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    config_content = """
[custom_prompts]
global_prompt = "Always use British spelling."
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    config = load_config(module_path=str(module_dir))

    assert config.custom_prompts.global_prompt == "Always use British spelling."
    assert config.custom_prompts.module_readme is None
    assert config.custom_prompts.project_readme is None
    assert config.custom_prompts.style_guide is None


def test_load_config_with_doc_type_specific_prompts(tmp_path: Path) -> None:
    """Test load_config loads doc-type-specific custom prompts."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    config_content = """
[custom_prompts]
module_readme = "Focus on implementation details."
project_readme = "Keep it concise for newcomers."
style_guide = "Include specific code examples."
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    config = load_config(module_path=str(module_dir))

    assert config.custom_prompts.global_prompt is None
    assert config.custom_prompts.module_readme == "Focus on implementation details."
    assert config.custom_prompts.project_readme == "Keep it concise for newcomers."
    assert config.custom_prompts.style_guide == "Include specific code examples."


def test_load_config_with_all_custom_prompts(tmp_path: Path) -> None:
    """Test load_config loads both global and doc-type-specific prompts."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    config_content = """
[custom_prompts]
global_prompt = "Use clear, simple language."
module_readme = "Focus on architecture."
project_readme = "Include quick-start guide."
style_guide = "Reference existing code patterns."
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    config = load_config(module_path=str(module_dir))

    assert config.custom_prompts.global_prompt == "Use clear, simple language."
    assert config.custom_prompts.module_readme == "Focus on architecture."
    assert config.custom_prompts.project_readme == "Include quick-start guide."
    assert config.custom_prompts.style_guide == "Reference existing code patterns."


def test_load_config_merge_custom_prompts(tmp_path: Path) -> None:
    """Test custom prompts are merged from repo and module configs."""
    # Create repo structure
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    module_dir = repo_root / "src" / "module"
    module_dir.mkdir(parents=True)

    # Create repo-level config with global prompt
    repo_config = """
[custom_prompts]
global_prompt = "Use American spelling."
module_readme = "Include diagrams."
"""
    (repo_root / ".dokken.toml").write_text(repo_config)

    # Create module-level config that overrides module_readme
    module_config = """
[custom_prompts]
module_readme = "Focus on implementation details."
project_readme = "Keep it brief."
"""
    (module_dir / ".dokken.toml").write_text(module_config)

    config = load_config(module_path=str(module_dir))

    # Global prompt from repo should be preserved
    assert config.custom_prompts.global_prompt == "Use American spelling."
    # module_readme should be overridden by module config
    assert config.custom_prompts.module_readme == "Focus on implementation details."
    # project_readme from module should be added
    assert config.custom_prompts.project_readme == "Keep it brief."
    assert config.custom_prompts.style_guide is None


def test_load_config_custom_prompts_and_exclusions(tmp_path: Path) -> None:
    """Test load_config handles both custom_prompts and exclusions."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    config_content = """
[exclusions]
files = ["__init__.py"]
symbols = ["test_*"]

[custom_prompts]
global_prompt = "Be concise."
module_readme = "Focus on patterns."
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    config = load_config(module_path=str(module_dir))

    # Check exclusions
    assert config.exclusions.files == ["__init__.py"]
    assert config.exclusions.symbols == ["test_*"]

    # Check custom prompts
    assert config.custom_prompts.global_prompt == "Be concise."
    assert config.custom_prompts.module_readme == "Focus on patterns."


def test_custom_prompts_max_length_validation(tmp_path: Path) -> None:
    """Test CustomPrompts rejects prompts exceeding max length."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    # Create a prompt that exceeds 5000 characters
    very_long_prompt = "x" * 5001

    config_content = f"""
[custom_prompts]
global_prompt = "{very_long_prompt}"
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    # Should raise ValueError with helpful message
    with pytest.raises(ValueError, match="Invalid custom prompts configuration"):
        load_config(module_path=str(module_dir))


# --- Tests for Modules ---


def test_dokken_config_with_modules() -> None:
    """Test DokkenConfig with modules list."""
    config = DokkenConfig(modules=["src/module1", "src/module2"])

    assert config.modules == ["src/module1", "src/module2"]
    assert isinstance(config.exclusions, ExclusionConfig)


def test_load_config_with_modules(tmp_path: Path) -> None:
    """Test load_config loads modules from .dokken.toml."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    config_content = """
modules = ["src/auth", "src/api", "src/database"]

[exclusions]
files = ["__init__.py"]
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    config = load_config(module_path=str(module_dir))

    assert config.modules == ["src/auth", "src/api", "src/database"]
    assert config.exclusions.files == ["__init__.py"]


def test_load_config_merge_modules(tmp_path: Path) -> None:
    """Test module-level modules extend repo-level modules."""
    # Create repo structure
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    module_dir = repo_root / "src" / "module"
    module_dir.mkdir(parents=True)

    # Create repo-level config
    repo_config = """
modules = ["src/core", "src/utils"]
"""
    (repo_root / ".dokken.toml").write_text(repo_config)

    # Create module-level config
    module_config = """
modules = ["src/auth"]
"""
    (module_dir / ".dokken.toml").write_text(module_config)

    config = load_config(module_path=str(module_dir))

    # Both configs should be merged
    assert set(config.modules) == {"src/core", "src/utils", "src/auth"}


def test_load_config_modules_no_duplicates(tmp_path: Path) -> None:
    """Test that merged module configs don't create duplicates."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    module_dir = repo_root / "src" / "module"
    module_dir.mkdir(parents=True)

    # Both configs have overlapping modules
    repo_config = """
modules = ["src/auth", "src/api"]
"""
    (repo_root / ".dokken.toml").write_text(repo_config)

    module_config = """
modules = ["src/auth", "src/database"]
"""
    (module_dir / ".dokken.toml").write_text(module_config)

    config = load_config(module_path=str(module_dir))

    # Check no duplicates
    assert config.modules.count("src/auth") == 1
    assert set(config.modules) == {"src/auth", "src/api", "src/database"}


def test_load_config_invalid_exclusions_validation(tmp_path: Path) -> None:
    """Test load_config raises ValueError for invalid exclusions configuration."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    # Create config with invalid exclusions (wrong type - should be list)
    config_content = """
[exclusions]
files = "not_a_list"
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    # Should raise ValueError with helpful message
    with pytest.raises(ValueError, match="Invalid exclusions configuration"):
        load_config(module_path=str(module_dir))


def test_load_config_invalid_cache_validation(tmp_path: Path) -> None:
    """Test load_config raises ValueError for invalid cache configuration."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    # Create config with invalid cache (max_size must be > 0)
    config_content = """
[cache]
max_size = 0
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    # Should raise ValueError with helpful message
    with pytest.raises(ValueError, match="Invalid cache configuration"):
        load_config(module_path=str(module_dir))


# --- Tests for File Types ---


def test_load_config_with_file_types(tmp_path: Path) -> None:
    """Test load_config loads file_types from .dokken.toml."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    config_content = """
file_types = [".js", ".ts", ".jsx"]
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    config = load_config(module_path=str(module_dir))

    assert config.file_types == [".js", ".ts", ".jsx"]


def test_load_config_file_types_default(tmp_path: Path) -> None:
    """Test load_config defaults to ['.py'] when file_types not specified."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    config_content = """
[exclusions]
files = ["__init__.py"]
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    config = load_config(module_path=str(module_dir))

    assert config.file_types == [".py"]


def test_load_config_merge_file_types(tmp_path: Path) -> None:
    """Test module-level file_types override repo-level file_types."""
    # Create repo structure
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    module_dir = repo_root / "src" / "module"
    module_dir.mkdir(parents=True)

    # Create repo-level config
    repo_config = """
file_types = [".py"]
"""
    (repo_root / ".dokken.toml").write_text(repo_config)

    # Create module-level config that overrides file_types
    module_config = """
file_types = [".js", ".ts"]
"""
    (module_dir / ".dokken.toml").write_text(module_config)

    config = load_config(module_path=str(module_dir))

    # Module config should override (not extend) repo config for file_types
    assert set(config.file_types) == {".js", ".ts"}


def test_load_config_file_types_and_exclusions(tmp_path: Path) -> None:
    """Test load_config handles both file_types and exclusions."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    config_content = """
file_types = [".js", ".ts"]

[exclusions]
files = ["*.test.js", "*.spec.ts"]
symbols = ["test_*"]
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    config = load_config(module_path=str(module_dir))

    # Check file_types
    assert config.file_types == [".js", ".ts"]

    # Check exclusions
    assert config.exclusions.files == ["*.test.js", "*.spec.ts"]
    assert config.exclusions.symbols == ["test_*"]


# --- Tests for File Depth ---


def test_load_config_with_file_depth(tmp_path: Path) -> None:
    """Test load_config loads file_depth from .dokken.toml."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    config_content = """
file_depth = 2
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    config = load_config(module_path=str(module_dir))

    assert config.file_depth == 2


def test_load_config_file_depth_default(tmp_path: Path) -> None:
    """Test load_config defaults to None when file_depth not specified."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    config_content = """
[exclusions]
files = ["__init__.py"]
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    config = load_config(module_path=str(module_dir))

    assert config.file_depth is None


def test_load_config_file_depth_zero(tmp_path: Path) -> None:
    """Test load_config accepts file_depth of 0 (root only)."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    config_content = """
file_depth = 0
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    config = load_config(module_path=str(module_dir))

    assert config.file_depth == 0


def test_load_config_file_depth_infinite(tmp_path: Path) -> None:
    """Test load_config accepts file_depth of -1 (infinite recursion)."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    config_content = """
file_depth = -1
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    config = load_config(module_path=str(module_dir))

    assert config.file_depth == -1


def test_load_config_file_depth_invalid(tmp_path: Path) -> None:
    """Test load_config rejects invalid file_depth values (< -1)."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    config_content = """
file_depth = -2
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    # Should raise ValueError for invalid depth
    with pytest.raises(ValueError):
        load_config(module_path=str(module_dir))


def test_load_config_merge_file_depth(tmp_path: Path) -> None:
    """Test module-level file_depth overrides repo-level file_depth."""
    # Create repo structure
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    module_dir = repo_root / "src" / "module"
    module_dir.mkdir(parents=True)

    # Create repo-level config
    repo_config = """
file_depth = 1
"""
    (repo_root / ".dokken.toml").write_text(repo_config)

    # Create module-level config that overrides file_depth
    module_config = """
file_depth = 2
"""
    (module_dir / ".dokken.toml").write_text(module_config)

    config = load_config(module_path=str(module_dir))

    # Module config should override repo config for file_depth
    assert config.file_depth == 2


def test_load_config_file_depth_with_other_settings(tmp_path: Path) -> None:
    """Test load_config handles file_depth with other configuration options."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    config_content = """
file_depth = 2
file_types = [".js", ".ts"]

[exclusions]
files = ["*.test.js"]
symbols = ["test_*"]
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    config = load_config(module_path=str(module_dir))

    # Check all settings
    assert config.file_depth == 2
    assert config.file_types == [".js", ".ts"]
    assert config.exclusions.files == ["*.test.js"]
    assert config.exclusions.symbols == ["test_*"]
