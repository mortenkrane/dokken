"""Tests for src/code_analyzer.py"""

from pathlib import Path

from pytest_mock import MockerFixture

from src.code_analyzer import get_module_context


def test_get_module_context_with_python_files(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Test get_module_context returns context when Python files exist."""
    # Create temp module with Python files
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    (module_dir / "file1.py").write_text("print('hello')")
    (module_dir / "file2.py").write_text("print('world')")

    mocker.patch("src.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir))

    assert context
    assert f"--- MODULE PATH: {module_dir} ---" in context
    assert "file1.py" in context
    assert "file2.py" in context
    assert "print('hello')" in context
    assert "print('world')" in context


def test_get_module_context_no_python_files(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Test get_module_context returns empty string when no Python files exist."""
    # Create temp module without Python files
    module_dir = tmp_path / "empty_module"
    module_dir.mkdir()

    mock_console = mocker.patch("src.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir))

    assert context == ""
    mock_console.print.assert_called_once()
    assert "No Python files found" in str(mock_console.print.call_args)


def test_get_module_context_includes_file_content(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Test that get_module_context includes actual file content."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    file_content = "def hello():\n    return 'world'"
    (module_dir / "test.py").write_text(file_content)

    mocker.patch("src.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir))

    assert file_content in context
    assert "--- FILE:" in context


def test_get_module_context_sorts_files(tmp_path: Path, mocker: MockerFixture) -> None:
    """Test that get_module_context processes files in sorted order."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    (module_dir / "c_file.py").write_text("c")
    (module_dir / "a_file.py").write_text("a")
    (module_dir / "b_file.py").write_text("b")

    mocker.patch("src.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir))

    # Check that files appear in sorted order
    a_pos = context.find("a_file.py")
    b_pos = context.find("b_file.py")
    c_pos = context.find("c_file.py")

    assert a_pos < b_pos < c_pos


def test_get_module_context_handles_exception(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Test that get_module_context handles exceptions gracefully."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    (module_dir / "test.py").write_text("code")

    # Make file reading raise an exception
    mock_console = mocker.patch("src.code_analyzer.console")
    mocker.patch("builtins.open", side_effect=OSError("File read error"))

    context = get_module_context(module_path=str(module_dir))

    assert context == ""
    mock_console.print.assert_called_once()
    assert "Error getting module context" in str(mock_console.print.call_args)


def test_get_module_context_multiple_files(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Test get_module_context handles multiple Python files correctly."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    # Create multiple files
    files = ["file1.py", "file2.py", "file3.py"]
    for filename in files:
        (module_dir / filename).write_text(f"# {filename}")

    mocker.patch("src.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir))

    # Each file should appear in the context
    for filename in files:
        assert filename in context
        assert f"# {filename}" in context
