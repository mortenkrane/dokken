"""Tests for src/main.py (CLI)"""

from pathlib import Path

import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from src.constants import DEFAULT_CACHE_FILE
from src.doctypes import DocType
from src.exceptions import DocumentationDriftError
from src.main import _get_cache_file_path, _get_cache_module_path, check, cli, generate


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click test runner."""
    return CliRunner()


def test_cli_version(runner: CliRunner) -> None:
    """Test that CLI shows version."""
    result = runner.invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_check_command_with_valid_path(
    runner: CliRunner, mock_main_console, mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test check command with valid module path."""
    mock_check = mocker.patch("src.main.check_documentation_drift")

    result = runner.invoke(cli, ["check", str(temp_module_dir)])

    assert result.exit_code == 0
    mock_check.assert_called_once_with(
        target_module_path=str(temp_module_dir),
        fix=False,
        depth=None,
        doc_type=DocType.MODULE_README,
    )


def test_check_command_with_invalid_path(runner: CliRunner) -> None:
    """Test check command with non-existent path."""
    result = runner.invoke(cli, ["check", "/nonexistent/path"])

    assert result.exit_code != 0


def test_check_command_drift_detected(
    runner: CliRunner, mock_main_console, mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test check command when drift is detected."""
    mock_check = mocker.patch(
        "src.main.check_documentation_drift",
        side_effect=DocumentationDriftError(
            rationale="Drift detected",
            module_path=str(temp_module_dir),
        ),
    )

    result = runner.invoke(cli, ["check", str(temp_module_dir)])

    assert result.exit_code == 1
    mock_check.assert_called_once()


def test_check_command_no_drift(
    runner: CliRunner, mock_main_console, mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test check command when no drift is detected."""
    mock_check = mocker.patch("src.main.check_documentation_drift")

    result = runner.invoke(cli, ["check", str(temp_module_dir)])

    assert result.exit_code == 0
    mock_check.assert_called_once()


def test_check_command_value_error(
    runner: CliRunner, mock_main_console, mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test check command handles ValueError."""
    mock_check = mocker.patch(
        "src.main.check_documentation_drift",
        side_effect=ValueError("Configuration error"),
    )

    result = runner.invoke(cli, ["check", str(temp_module_dir)])

    assert result.exit_code == 1
    mock_check.assert_called_once()


def test_generate_command_with_valid_path(
    runner: CliRunner, mock_main_console, mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test generate command with valid module path."""
    mock_generate = mocker.patch("src.main.generate_documentation", return_value=None)

    result = runner.invoke(cli, ["generate", str(temp_module_dir)])

    assert result.exit_code == 0
    mock_generate.assert_called_once_with(
        target_module_path=str(temp_module_dir),
        depth=None,
        doc_type=DocType.MODULE_README,
    )


def test_generate_command_with_invalid_path(runner: CliRunner) -> None:
    """Test generate command with non-existent path."""
    result = runner.invoke(cli, ["generate", "/nonexistent/path"])

    assert result.exit_code != 0


def test_generate_command_success(
    runner: CliRunner, mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test generate command successful execution."""
    markdown = "# Generated Documentation"
    mock_generate = mocker.patch(
        "src.main.generate_documentation", return_value=markdown
    )
    mocker.patch("src.main.console")

    result = runner.invoke(cli, ["generate", str(temp_module_dir)])

    assert result.exit_code == 0
    mock_generate.assert_called_once()


def test_generate_command_no_output(
    runner: CliRunner, mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test generate command when workflow returns None."""
    mock_generate = mocker.patch("src.main.generate_documentation", return_value=None)
    mocker.patch("src.main.console")

    result = runner.invoke(cli, ["generate", str(temp_module_dir)])

    assert result.exit_code == 0
    mock_generate.assert_called_once()


def test_generate_command_value_error(
    runner: CliRunner, mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test generate command handles ValueError."""
    mock_generate = mocker.patch(
        "src.main.generate_documentation",
        side_effect=ValueError("API key missing"),
    )
    mocker.patch("src.main.console")

    result = runner.invoke(cli, ["generate", str(temp_module_dir)])

    assert result.exit_code == 1
    mock_generate.assert_called_once()


def test_generate_command_drift_error(
    runner: CliRunner, mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test generate command handles DocumentationDriftError."""
    mock_generate = mocker.patch(
        "src.main.generate_documentation",
        side_effect=DocumentationDriftError(
            rationale="Unexpected drift",
            module_path=str(temp_module_dir),
        ),
    )
    mocker.patch("src.main.console")

    result = runner.invoke(cli, ["generate", str(temp_module_dir)])

    assert result.exit_code == 1
    mock_generate.assert_called_once()


@pytest.mark.parametrize(
    "command_name,command_func",
    [
        ("check", check),
        ("generate", generate),
    ],
)
def test_commands_require_module_path(
    runner: CliRunner, command_name: str, command_func: object
) -> None:
    """Test that commands require module_path argument."""
    result = runner.invoke(cli, [command_name])

    assert result.exit_code != 0
    assert "Missing argument" in result.output or "Error" in result.output


def test_check_command_uses_console(
    runner: CliRunner, mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test check command uses Rich console for output."""
    mocker.patch("src.main.check_documentation_drift")
    mock_console = mocker.patch("src.main.console")

    runner.invoke(cli, ["check", str(temp_module_dir)])

    # Console should be used for printing
    assert mock_console.print.call_count > 0


def test_generate_command_uses_console(
    runner: CliRunner, mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test generate command uses Rich console for output."""
    mocker.patch("src.main.generate_documentation", return_value="# Docs")
    mock_console = mocker.patch("src.main.console")

    runner.invoke(cli, ["generate", str(temp_module_dir)])

    # Console should be used for printing
    assert mock_console.print.call_count > 0


def test_check_command_path_validation(runner: CliRunner, tmp_path: Path) -> None:
    """Test check command validates that path is a directory."""
    # Create a file instead of directory
    file_path = tmp_path / "not_a_dir.txt"
    file_path.write_text("test")

    result = runner.invoke(cli, ["check", str(file_path)])

    assert result.exit_code != 0


def test_generate_command_path_validation(runner: CliRunner, tmp_path: Path) -> None:
    """Test generate command validates that path is a directory."""
    # Create a file instead of directory
    file_path = tmp_path / "not_a_dir.txt"
    file_path.write_text("test")

    result = runner.invoke(cli, ["generate", str(file_path)])

    assert result.exit_code != 0


def test_check_command_with_fix_flag(
    runner: CliRunner, mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test check command with --fix flag."""
    mock_check = mocker.patch("src.main.check_documentation_drift")
    mocker.patch("src.main.console")

    result = runner.invoke(cli, ["check", str(temp_module_dir), "--fix"])

    assert result.exit_code == 0
    mock_check.assert_called_once_with(
        target_module_path=str(temp_module_dir),
        fix=True,
        depth=None,
        doc_type=DocType.MODULE_README,
    )


def test_check_command_with_depth_flag(
    runner: CliRunner, mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test check command with --depth flag."""
    mock_check = mocker.patch("src.main.check_documentation_drift")
    mocker.patch("src.main.console")

    result = runner.invoke(cli, ["check", str(temp_module_dir), "--depth", "2"])

    assert result.exit_code == 0
    mock_check.assert_called_once_with(
        target_module_path=str(temp_module_dir),
        fix=False,
        depth=2,
        doc_type=DocType.MODULE_README,
    )


def test_generate_command_with_depth_flag(
    runner: CliRunner, mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test generate command with --depth flag."""
    mock_generate = mocker.patch("src.main.generate_documentation", return_value=None)
    mocker.patch("src.main.console")

    result = runner.invoke(cli, ["generate", str(temp_module_dir), "--depth", "-1"])

    assert result.exit_code == 0
    mock_generate.assert_called_once_with(
        target_module_path=str(temp_module_dir),
        depth=-1,
        doc_type=DocType.MODULE_README,
    )


def test_check_command_all_flag_with_module_path(
    runner: CliRunner, temp_module_dir: Path
) -> None:
    """Test check command rejects --all with module path."""
    result = runner.invoke(cli, ["check", str(temp_module_dir), "--all"])

    assert result.exit_code == 1
    assert "Cannot use --all with a module path" in result.output


def test_check_command_all_flag_without_module_path(
    runner: CliRunner, mocker: MockerFixture
) -> None:
    """Test check command with --all flag and no module path."""
    mock_check_multiple = mocker.patch("src.main.check_multiple_modules_drift")
    mocker.patch("src.main.console")

    result = runner.invoke(cli, ["check", "--all"])

    assert result.exit_code == 0
    mock_check_multiple.assert_called_once_with(
        fix=False, depth=None, doc_type=DocType.MODULE_README
    )


def test_check_command_without_module_path_or_all_flag(runner: CliRunner) -> None:
    """Test check command requires either module path or --all flag."""
    result = runner.invoke(cli, ["check"])

    assert result.exit_code == 1
    assert "Must specify either a module path or --all flag" in result.output


def test_get_cache_file_path_with_config_error(mocker: MockerFixture) -> None:
    """Test _get_cache_file_path falls back to default on config error."""
    # Mock load_config to raise an error
    mocker.patch("src.main.load_config", side_effect=ValueError("Config error"))

    # Should return default cache file
    result = _get_cache_file_path("some/path")

    assert result == DEFAULT_CACHE_FILE


def test_get_cache_module_path_with_check_all_no_repo_root(
    mocker: MockerFixture,
) -> None:
    """Test _get_cache_module_path returns '.' when --all is used outside git repo."""
    # Mock find_repo_root to return None (not in a git repo)
    mocker.patch("src.main.find_repo_root", return_value=None)

    # Should return "." as fallback
    result = _get_cache_module_path(module_path=None, check_all=True)

    assert result == "."
