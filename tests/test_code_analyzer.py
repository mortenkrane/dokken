"""Tests for src/code_analyzer.py"""

from pathlib import Path

from pytest_mock import MockerFixture

from src.code_analyzer import (
    _filter_excluded_files,
    _filter_excluded_symbols,
    _find_python_files,
    get_module_context,
)


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
    """Test that get_module_context handles file read exceptions gracefully."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    (module_dir / "test.py").write_text("code")

    # Make file reading raise an exception
    mock_console = mocker.patch("src.code_analyzer.console")
    mocker.patch("builtins.open", side_effect=OSError("File read error"))

    context = get_module_context(module_path=str(module_dir))

    # Should still return module header even if individual files fail
    assert f"--- MODULE PATH: {module_dir} ---" in context
    # Should have logged the file read error
    mock_console.print.assert_called()
    assert any(
        "Could not read" in str(call) for call in mock_console.print.call_args_list
    )


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


# Tests for exclusion functionality


def test_filter_excluded_files_no_patterns() -> None:
    """Test _filter_excluded_files returns all files when no patterns."""
    files = ["/path/to/file1.py", "/path/to/file2.py"]
    result = _filter_excluded_files(files, "/path/to", [])

    assert result == files


def test_filter_excluded_files_exact_match() -> None:
    """Test _filter_excluded_files excludes exact filename matches."""
    files = [
        "/path/to/__init__.py",
        "/path/to/main.py",
        "/path/to/conftest.py",
    ]
    patterns = ["__init__.py", "conftest.py"]

    result = _filter_excluded_files(files, "/path/to", patterns)

    assert result == ["/path/to/main.py"]


def test_filter_excluded_files_glob_pattern() -> None:
    """Test _filter_excluded_files handles glob patterns."""
    files = [
        "/path/to/test_one.py",
        "/path/to/test_two.py",
        "/path/to/main.py",
    ]
    patterns = ["test_*.py"]

    result = _filter_excluded_files(files, "/path/to", patterns)

    assert result == ["/path/to/main.py"]


def test_filter_excluded_files_multiple_patterns() -> None:
    """Test _filter_excluded_files handles multiple patterns."""
    files = [
        "/path/to/__init__.py",
        "/path/to/test_utils.py",
        "/path/to/main.py",
        "/path/to/helper.py",
    ]
    patterns = ["__init__.py", "test_*.py", "*_utils.py"]

    result = _filter_excluded_files(files, "/path/to", patterns)

    # Only main.py and helper.py should remain
    assert set(result) == {"/path/to/main.py", "/path/to/helper.py"}


def test_filter_excluded_symbols_no_patterns() -> None:
    """Test _filter_excluded_symbols returns original code when no patterns."""
    code = """
def public_function():
    pass

class PublicClass:
    pass
"""

    result = _filter_excluded_symbols(code, [])

    assert result == code


def test_filter_excluded_symbols_exact_match() -> None:
    """Test _filter_excluded_symbols excludes exact symbol matches."""
    code = """def public_function():
    pass

def _private_helper():
    pass

class MyClass:
    pass
"""

    result = _filter_excluded_symbols(code, ["_private_helper"])

    assert "public_function" in result
    assert "MyClass" in result
    assert "_private_helper" not in result


def test_filter_excluded_symbols_wildcard_pattern() -> None:
    """Test _filter_excluded_symbols handles wildcard patterns."""
    code = """def _private_one():
    pass

def _private_two():
    pass

def public_function():
    pass
"""

    result = _filter_excluded_symbols(code, ["_private_*"])

    assert "public_function" in result
    assert "_private_one" not in result
    assert "_private_two" not in result


def test_filter_excluded_symbols_class_exclusion() -> None:
    """Test _filter_excluded_symbols can exclude classes."""
    code = """class PublicClass:
    def method(self):
        pass

class _PrivateClass:
    def method(self):
        pass
"""

    result = _filter_excluded_symbols(code, ["_Private*"])

    assert "PublicClass" in result
    assert "_PrivateClass" not in result
    assert "def method" in result  # PublicClass method should remain


def test_filter_excluded_symbols_preserves_non_toplevel() -> None:
    """Test _filter_excluded_symbols only excludes top-level symbols."""
    code = """def outer():
    def _private_inner():
        pass
    return _private_inner

class MyClass:
    def _private_method(self):
        pass
"""

    # Even though pattern matches _private_*, only top-level should be excluded
    result = _filter_excluded_symbols(code, ["_private_*"])

    # outer() and MyClass should remain with their inner _private_* symbols
    assert "def outer():" in result
    assert "def _private_inner():" in result
    assert "class MyClass:" in result
    assert "def _private_method(self):" in result


def test_filter_excluded_symbols_invalid_syntax() -> None:
    """Test _filter_excluded_symbols returns original code if syntax invalid."""
    invalid_code = "def incomplete("

    result = _filter_excluded_symbols(invalid_code, ["test_*"])

    # Should return original code without crashing
    assert result == invalid_code


def test_filter_excluded_symbols_async_functions() -> None:
    """Test _filter_excluded_symbols handles async functions."""
    code = """async def async_public():
    pass

async def _async_private():
    pass
"""

    result = _filter_excluded_symbols(code, ["_async_*"])

    assert "async_public" in result
    assert "_async_private" not in result


def test_get_module_context_with_file_exclusions(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Test get_module_context respects file exclusions from config."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    # Create files
    (module_dir / "__init__.py").write_text("# init")
    (module_dir / "main.py").write_text("# main")
    (module_dir / "test_utils.py").write_text("# test")

    # Create config excluding __init__.py and test_*.py
    config_content = """
[exclusions]
files = ["__init__.py", "test_*.py"]
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    mocker.patch("src.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir))

    # Only main.py should be included
    assert "main.py" in context
    assert "# main" in context
    assert "__init__.py" not in context
    assert "test_utils.py" not in context


def test_get_module_context_with_symbol_exclusions(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Test get_module_context respects symbol exclusions from config."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    # Create file with mixed symbols
    code = """def public_api():
    '''Public API function.'''
    pass

def _private_helper():
    '''Private helper.'''
    pass

class MyClass:
    pass
"""
    (module_dir / "module.py").write_text(code)

    # Create config excluding _private_*
    config_content = """
[exclusions]
symbols = ["_private_*"]
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    mocker.patch("src.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir))

    # public_api and MyClass should be included
    assert "def public_api():" in context
    assert "class MyClass:" in context
    # _private_helper should be excluded
    assert "_private_helper" not in context


def test_get_module_context_all_files_excluded(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Test get_module_context handles case when all files are excluded."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    (module_dir / "test_one.py").write_text("# test")
    (module_dir / "test_two.py").write_text("# test")

    # Exclude all test files
    config_content = """
[exclusions]
files = ["test_*.py"]
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    mock_console = mocker.patch("src.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir))

    assert context == ""
    # Should print warning about all files excluded
    assert any(
        "All Python files" in str(call) and "are excluded" in str(call)
        for call in mock_console.print.call_args_list
    )


# Tests for depth functionality


def test_find_python_files_depth_zero(tmp_path: Path) -> None:
    """Test _find_python_files with depth=0 finds only root level files."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    (module_dir / "root.py").write_text("root")

    # Create nested directory
    subdir = module_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested.py").write_text("nested")

    files = _find_python_files(module_path=str(module_dir), depth=0)

    assert len(files) == 1
    assert any("root.py" in f for f in files)
    assert not any("nested.py" in f for f in files)


def test_find_python_files_depth_one(tmp_path: Path) -> None:
    """Test _find_python_files with depth=1 finds root and one level deep."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    (module_dir / "root.py").write_text("root")

    # Create nested directory (level 1)
    subdir = module_dir / "subdir"
    subdir.mkdir()
    (subdir / "level1.py").write_text("level1")

    # Create deeper nested directory (level 2)
    subsubdir = subdir / "subsubdir"
    subsubdir.mkdir()
    (subsubdir / "level2.py").write_text("level2")

    files = _find_python_files(module_path=str(module_dir), depth=1)

    assert len(files) == 2
    assert any("root.py" in f for f in files)
    assert any("level1.py" in f for f in files)
    assert not any("level2.py" in f for f in files)


def test_find_python_files_depth_infinite(tmp_path: Path) -> None:
    """Test _find_python_files with depth=-1 finds all files recursively."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    (module_dir / "root.py").write_text("root")

    # Create nested directories
    subdir = module_dir / "subdir"
    subdir.mkdir()
    (subdir / "level1.py").write_text("level1")

    subsubdir = subdir / "subsubdir"
    subsubdir.mkdir()
    (subsubdir / "level2.py").write_text("level2")

    files = _find_python_files(module_path=str(module_dir), depth=-1)

    assert len(files) == 3
    assert any("root.py" in f for f in files)
    assert any("level1.py" in f for f in files)
    assert any("level2.py" in f for f in files)


def test_get_module_context_with_depth(tmp_path: Path, mocker: MockerFixture) -> None:
    """Test get_module_context respects depth parameter."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    (module_dir / "root.py").write_text("root content")

    subdir = module_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested.py").write_text("nested content")

    mocker.patch("src.code_analyzer.console")

    # depth=0 should only find root
    context = get_module_context(module_path=str(module_dir), depth=0)
    assert "root content" in context
    assert "nested content" not in context

    # depth=-1 should find all
    context = get_module_context(module_path=str(module_dir), depth=-1)
    assert "root content" in context
    assert "nested content" in context


def test_get_module_context_oserror_on_module_path(mocker: MockerFixture) -> None:
    """Test get_module_context handles OSError when accessing module path."""
    mock_console = mocker.patch("src.code_analyzer.console")
    # Mock load_config to raise OSError (simulating permission denied on module path)
    mocker.patch("src.code_analyzer.load_config", side_effect=OSError("Permission denied"))

    context = get_module_context(module_path="/some/path")

    # Should return empty string
    assert context == ""
    # Should log the error
    assert any(
        "Error accessing module path" in str(call)
        for call in mock_console.print.call_args_list
    )
