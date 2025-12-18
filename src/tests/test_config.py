"""Tests for src/config.py"""

from pathlib import Path

from src.config import DokkenConfig, ExclusionConfig, load_config


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
