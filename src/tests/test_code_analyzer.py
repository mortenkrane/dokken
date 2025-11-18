"""Tests for src/code_analyzer.py"""

import subprocess
from unittest.mock import MagicMock

import pytest

from src.code_analyzer import get_module_context


def test_get_module_context_with_python_files(tmp_path, mocker):
    """Test get_module_context returns context when Python files exist."""
    # Create temp module with Python files
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    (module_dir / "file1.py").write_text("print('hello')")
    (module_dir / "file2.py").write_text("print('world')")

    # Mock subprocess for git diff
    mock_subprocess = mocker.patch("src.code_analyzer.subprocess.run")
    mock_result = MagicMock()
    mock_result.stdout = "diff --git a/file1.py b/file1.py\n+print('hello')"
    mock_subprocess.return_value = mock_result

    mocker.patch("src.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir))

    assert context
    assert f"--- MODULE PATH: {module_dir} ---" in context
    assert "file1.py" in context
    assert "file2.py" in context
    assert "print('hello')" in context
    assert "print('world')" in context


def test_get_module_context_no_python_files(tmp_path, mocker):
    """Test get_module_context returns empty string when no Python files exist."""
    # Create temp module without Python files
    module_dir = tmp_path / "empty_module"
    module_dir.mkdir()

    mock_console = mocker.patch("src.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir))

    assert context == ""
    mock_console.print.assert_called_once()
    assert "No Python files found" in str(mock_console.print.call_args)


def test_get_module_context_calls_git_diff(tmp_path, mocker):
    """Test that get_module_context calls git diff for each Python file."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    file_path = module_dir / "test.py"
    file_path.write_text("def test(): pass")

    mock_subprocess = mocker.patch("src.code_analyzer.subprocess.run")
    mock_result = MagicMock()
    mock_result.stdout = "sample diff"
    mock_subprocess.return_value = mock_result

    mocker.patch("src.code_analyzer.console")

    get_module_context(module_path=str(module_dir))

    # Verify git diff was called with correct arguments
    mock_subprocess.assert_called_once()
    call_args = mock_subprocess.call_args[0][0]
    assert call_args[0] == "git"
    assert call_args[1] == "diff"
    assert call_args[2] == "main"
    assert str(file_path) in call_args


@pytest.mark.parametrize(
    "base_branch",
    ["main", "develop", "master"],
)
def test_get_module_context_with_different_base_branches(tmp_path, mocker, base_branch):
    """Test get_module_context uses the specified base branch."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    (module_dir / "test.py").write_text("code")

    mock_subprocess = mocker.patch("src.code_analyzer.subprocess.run")
    mock_result = MagicMock()
    mock_result.stdout = "diff"
    mock_subprocess.return_value = mock_result

    mocker.patch("src.code_analyzer.console")

    get_module_context(module_path=str(module_dir), base_branch=base_branch)

    # Verify the base branch was used in git diff
    call_args = mock_subprocess.call_args[0][0]
    assert base_branch in call_args


def test_get_module_context_includes_file_content(tmp_path, mocker):
    """Test that get_module_context includes actual file content."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    file_content = "def hello():\n    return 'world'"
    (module_dir / "test.py").write_text(file_content)

    mock_subprocess = mocker.patch("src.code_analyzer.subprocess.run")
    mock_result = MagicMock()
    mock_result.stdout = "diff output"
    mock_subprocess.return_value = mock_result

    mocker.patch("src.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir))

    assert file_content in context
    assert "--- CURRENT CODE CONTENT ---" in context


def test_get_module_context_includes_git_diff(tmp_path, mocker):
    """Test that get_module_context includes git diff output."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    (module_dir / "test.py").write_text("code")

    diff_output = "diff --git a/test.py b/test.py\n+new line"
    mock_subprocess = mocker.patch("src.code_analyzer.subprocess.run")
    mock_result = MagicMock()
    mock_result.stdout = diff_output
    mock_subprocess.return_value = mock_result

    mocker.patch("src.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir))

    assert diff_output in context
    assert "--- CODE CHANGES (GIT DIFF vs. main) ---" in context


def test_get_module_context_sorts_files(tmp_path, mocker):
    """Test that get_module_context processes files in sorted order."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    (module_dir / "c_file.py").write_text("c")
    (module_dir / "a_file.py").write_text("a")
    (module_dir / "b_file.py").write_text("b")

    mock_subprocess = mocker.patch("src.code_analyzer.subprocess.run")
    mock_result = MagicMock()
    mock_result.stdout = "diff"
    mock_subprocess.return_value = mock_result

    mocker.patch("src.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir))

    # Check that files appear in sorted order
    a_pos = context.find("a_file.py")
    b_pos = context.find("b_file.py")
    c_pos = context.find("c_file.py")

    assert a_pos < b_pos < c_pos


def test_get_module_context_handles_exception(tmp_path, mocker):
    """Test that get_module_context handles exceptions gracefully."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    (module_dir / "test.py").write_text("code")

    # Make subprocess raise an exception
    mock_subprocess = mocker.patch("src.code_analyzer.subprocess.run")
    mock_subprocess.side_effect = subprocess.CalledProcessError(1, "git diff")

    mock_console = mocker.patch("src.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir))

    assert context == ""
    mock_console.print.assert_called_once()
    assert "Error getting module context" in str(mock_console.print.call_args)


def test_get_module_context_multiple_files(tmp_path, mocker):
    """Test get_module_context handles multiple Python files correctly."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    # Create multiple files
    files = ["file1.py", "file2.py", "file3.py"]
    for filename in files:
        (module_dir / filename).write_text(f"# {filename}")

    mock_subprocess = mocker.patch("src.code_analyzer.subprocess.run")
    mock_result = MagicMock()
    mock_result.stdout = "diff"
    mock_subprocess.return_value = mock_result

    mocker.patch("src.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir))

    # Each file should appear in the context
    for filename in files:
        assert filename in context
        assert f"# {filename}" in context

    # Should have made git diff call for each file
    assert mock_subprocess.call_count == len(files)
