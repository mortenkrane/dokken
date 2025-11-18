"""Tests for src/main.py (CLI)"""

import pytest
from click.testing import CliRunner

from src.exceptions import DocumentationDriftError
from src.main import check, cli, generate


@pytest.fixture
def runner():
    """Create a Click test runner."""
    return CliRunner()


def test_cli_help(runner):
    """Test that CLI shows help message."""
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "Dokken" in result.output
    assert "check" in result.output
    assert "generate" in result.output


def test_cli_version(runner):
    """Test that CLI shows version."""
    result = runner.invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_check_command_help(runner):
    """Test that check command shows help."""
    result = runner.invoke(cli, ["check", "--help"])

    assert result.exit_code == 0
    assert "Check for documentation drift" in result.output
    assert "CI/CD" in result.output


def test_generate_command_help(runner):
    """Test that generate command shows help."""
    result = runner.invoke(cli, ["generate", "--help"])

    assert result.exit_code == 0
    assert "Generate fresh documentation" in result.output


def test_check_command_with_valid_path(runner, mocker, temp_module_dir):
    """Test check command with valid module path."""
    mock_check = mocker.patch("src.main.check_documentation_drift")
    mocker.patch("src.main.console")

    result = runner.invoke(cli, ["check", str(temp_module_dir)])

    assert result.exit_code == 0
    mock_check.assert_called_once_with(target_module_path=str(temp_module_dir))


def test_check_command_with_invalid_path(runner):
    """Test check command with non-existent path."""
    result = runner.invoke(cli, ["check", "/nonexistent/path"])

    assert result.exit_code != 0


def test_check_command_drift_detected(runner, mocker, temp_module_dir):
    """Test check command when drift is detected."""
    mock_check = mocker.patch(
        "src.main.check_documentation_drift",
        side_effect=DocumentationDriftError(
            rationale="Drift detected",
            module_path=str(temp_module_dir),
        ),
    )
    mocker.patch("src.main.console")

    result = runner.invoke(cli, ["check", str(temp_module_dir)])

    assert result.exit_code == 1
    mock_check.assert_called_once()


def test_check_command_no_drift(runner, mocker, temp_module_dir):
    """Test check command when no drift is detected."""
    mock_check = mocker.patch("src.main.check_documentation_drift")
    mocker.patch("src.main.console")

    result = runner.invoke(cli, ["check", str(temp_module_dir)])

    assert result.exit_code == 0
    mock_check.assert_called_once()


def test_check_command_value_error(runner, mocker, temp_module_dir):
    """Test check command handles ValueError."""
    mock_check = mocker.patch(
        "src.main.check_documentation_drift",
        side_effect=ValueError("Configuration error"),
    )
    mocker.patch("src.main.console")

    result = runner.invoke(cli, ["check", str(temp_module_dir)])

    assert result.exit_code == 1
    mock_check.assert_called_once()


def test_generate_command_with_valid_path(runner, mocker, temp_module_dir):
    """Test generate command with valid module path."""
    mock_generate = mocker.patch("src.main.generate_documentation", return_value=None)
    mocker.patch("src.main.console")

    result = runner.invoke(cli, ["generate", str(temp_module_dir)])

    assert result.exit_code == 0
    mock_generate.assert_called_once_with(target_module_path=str(temp_module_dir))


def test_generate_command_with_invalid_path(runner):
    """Test generate command with non-existent path."""
    result = runner.invoke(cli, ["generate", "/nonexistent/path"])

    assert result.exit_code != 0


def test_generate_command_success(runner, mocker, temp_module_dir):
    """Test generate command successful execution."""
    markdown = "# Generated Documentation"
    mock_generate = mocker.patch(
        "src.main.generate_documentation", return_value=markdown
    )
    mocker.patch("src.main.console")

    result = runner.invoke(cli, ["generate", str(temp_module_dir)])

    assert result.exit_code == 0
    mock_generate.assert_called_once()


def test_generate_command_no_output(runner, mocker, temp_module_dir):
    """Test generate command when workflow returns None."""
    mock_generate = mocker.patch("src.main.generate_documentation", return_value=None)
    mocker.patch("src.main.console")

    result = runner.invoke(cli, ["generate", str(temp_module_dir)])

    assert result.exit_code == 0
    mock_generate.assert_called_once()


def test_generate_command_value_error(runner, mocker, temp_module_dir):
    """Test generate command handles ValueError."""
    mock_generate = mocker.patch(
        "src.main.generate_documentation",
        side_effect=ValueError("API key missing"),
    )
    mocker.patch("src.main.console")

    result = runner.invoke(cli, ["generate", str(temp_module_dir)])

    assert result.exit_code == 1
    mock_generate.assert_called_once()


def test_generate_command_drift_error(runner, mocker, temp_module_dir):
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
def test_commands_require_module_path(runner, command_name, command_func):
    """Test that commands require module_path argument."""
    result = runner.invoke(cli, [command_name])

    assert result.exit_code != 0
    assert "Missing argument" in result.output or "Error" in result.output


def test_check_command_uses_console(runner, mocker, temp_module_dir):
    """Test check command uses Rich console for output."""
    mocker.patch("src.main.check_documentation_drift")
    mock_console = mocker.patch("src.main.console")

    runner.invoke(cli, ["check", str(temp_module_dir)])

    # Console should be used for printing
    assert mock_console.print.call_count > 0


def test_generate_command_uses_console(runner, mocker, temp_module_dir):
    """Test generate command uses Rich console for output."""
    mocker.patch("src.main.generate_documentation", return_value="# Docs")
    mock_console = mocker.patch("src.main.console")

    runner.invoke(cli, ["generate", str(temp_module_dir)])

    # Console should be used for printing
    assert mock_console.print.call_count > 0


def test_cli_commands_registered():
    """Test that check and generate commands are registered."""
    assert "check" in cli.commands
    assert "generate" in cli.commands


def test_check_command_path_validation(runner, tmp_path):
    """Test check command validates that path is a directory."""
    # Create a file instead of directory
    file_path = tmp_path / "not_a_dir.txt"
    file_path.write_text("test")

    result = runner.invoke(cli, ["check", str(file_path)])

    assert result.exit_code != 0


def test_generate_command_path_validation(runner, tmp_path):
    """Test generate command validates that path is a directory."""
    # Create a file instead of directory
    file_path = tmp_path / "not_a_dir.txt"
    file_path.write_text("test")

    result = runner.invoke(cli, ["generate", str(file_path)])

    assert result.exit_code != 0
