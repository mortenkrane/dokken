"""Tests for src/input/code_analyzer.py"""

import time
from pathlib import Path

from pytest_mock import MockerFixture

from src.input.code_analyzer import (
    _filter_excluded_files,
    _find_source_files,
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

    mocker.patch("src.input.code_analyzer.console")

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

    mock_console = mocker.patch("src.input.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir))

    assert context == ""
    mock_console.print.assert_called_once()
    assert "No source files" in str(mock_console.print.call_args)


def test_get_module_context_includes_file_content(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Test that get_module_context includes actual file content."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    file_content = "def hello():\n    return 'world'"
    (module_dir / "test.py").write_text(file_content)

    mocker.patch("src.input.code_analyzer.console")

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

    mocker.patch("src.input.code_analyzer.console")

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
    mock_console = mocker.patch("src.input.code_analyzer.console")
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

    mocker.patch("src.input.code_analyzer.console")

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

    mocker.patch("src.input.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir))

    # Only main.py should be included
    assert "main.py" in context
    assert "# main" in context
    assert "__init__.py" not in context
    assert "test_utils.py" not in context


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

    mock_console = mocker.patch("src.input.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir))

    assert context == ""
    # Should print warning about all files excluded
    assert any(
        "All source files" in str(call) and "are excluded" in str(call)
        for call in mock_console.print.call_args_list
    )


# Tests for depth functionality


def test_find_python_files_depth_zero(tmp_path: Path) -> None:
    """Test _find_source_files with depth=0 finds only root level files."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    (module_dir / "root.py").write_text("root")

    # Create nested directory
    subdir = module_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested.py").write_text("nested")

    files = _find_source_files(
        module_path=str(module_dir), depth=0, file_types=[".py"], excluded_dirs=[]
    )

    assert len(files) == 1
    assert any("root.py" in f for f in files)
    assert not any("nested.py" in f for f in files)


def test_find_python_files_depth_one(tmp_path: Path) -> None:
    """Test _find_source_files with depth=1 finds root and one level deep."""
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

    files = _find_source_files(
        module_path=str(module_dir), depth=1, file_types=[".py"], excluded_dirs=[]
    )

    assert len(files) == 2
    assert any("root.py" in f for f in files)
    assert any("level1.py" in f for f in files)
    assert not any("level2.py" in f for f in files)


def test_find_python_files_depth_infinite(tmp_path: Path) -> None:
    """Test _find_source_files with depth=-1 finds all files recursively."""
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

    files = _find_source_files(
        module_path=str(module_dir), depth=-1, file_types=[".py"], excluded_dirs=[]
    )

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

    mocker.patch("src.input.code_analyzer.console")

    # depth=0 should only find root
    context = get_module_context(module_path=str(module_dir), depth=0)
    assert "root content" in context
    assert "nested content" not in context

    # depth=-1 should find all
    context = get_module_context(module_path=str(module_dir), depth=-1)
    assert "root content" in context
    assert "nested content" in context


# Tests for directory exclusion functionality


def test_find_source_files_excludes_single_directory(tmp_path: Path) -> None:
    """Test _find_source_files excludes specified directories."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    (module_dir / "root.py").write_text("root")

    # Create directories to exclude
    venv_dir = module_dir / ".venv"
    venv_dir.mkdir()
    (venv_dir / "lib.py").write_text("venv lib")

    # Create directory to include
    src_dir = module_dir / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("main")

    files = _find_source_files(
        module_path=str(module_dir),
        depth=-1,
        file_types=[".py"],
        excluded_dirs=[".venv"],
    )

    assert len(files) == 2
    assert any("root.py" in f for f in files)
    assert any("main.py" in f for f in files)
    assert not any("lib.py" in f for f in files)


def test_find_source_files_excludes_multiple_directories(tmp_path: Path) -> None:
    """Test _find_source_files excludes multiple directories."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    (module_dir / "root.py").write_text("root")

    # Create excluded directories
    for dirname in [".venv", "node_modules", "build", "__pycache__"]:
        dir_path = module_dir / dirname
        dir_path.mkdir()
        (dir_path / "file.py").write_text(f"{dirname} file")

    # Create included directory
    src_dir = module_dir / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("main")

    files = _find_source_files(
        module_path=str(module_dir),
        depth=-1,
        file_types=[".py"],
        excluded_dirs=[".venv", "node_modules", "build", "__pycache__"],
    )

    assert len(files) == 2
    assert any("root.py" in f for f in files)
    assert any("main.py" in f for f in files)
    # None of the excluded directories should be present
    for dirname in [".venv", "node_modules", "build", "__pycache__"]:
        assert not any(dirname in f for f in files)


def test_find_source_files_excludes_nested_directories(tmp_path: Path) -> None:
    """Test _find_source_files excludes directories at any depth."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    # Create nested structure with excluded dirs at different levels
    src = module_dir / "src"
    src.mkdir()
    (src / "main.py").write_text("main")

    # Excluded dir at level 1
    cache1 = module_dir / "__pycache__"
    cache1.mkdir()
    (cache1 / "compiled.py").write_text("compiled1")

    # Excluded dir at level 2
    cache2 = src / "__pycache__"
    cache2.mkdir()
    (cache2 / "compiled.py").write_text("compiled2")

    files = _find_source_files(
        module_path=str(module_dir),
        depth=-1,
        file_types=[".py"],
        excluded_dirs=["__pycache__"],
    )

    assert len(files) == 1
    assert any("main.py" in f for f in files)
    assert not any("compiled.py" in f for f in files)


def test_find_source_files_directory_exclusion_with_glob_pattern(
    tmp_path: Path,
) -> None:
    """Test _find_source_files supports glob patterns for directory exclusion."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    (module_dir / "main.py").write_text("main")

    # Create directories matching pattern
    for dirname in ["test.egg-info", "mylib.egg-info", "another.egg-info"]:
        dir_path = module_dir / dirname
        dir_path.mkdir()
        (dir_path / "file.py").write_text(f"{dirname} file")

    # Create regular directory
    src = module_dir / "src"
    src.mkdir()
    (src / "code.py").write_text("code")

    files = _find_source_files(
        module_path=str(module_dir),
        depth=-1,
        file_types=[".py"],
        excluded_dirs=["*.egg-info"],
    )

    assert len(files) == 2
    assert any("main.py" in f for f in files)
    assert any("code.py" in f for f in files)
    # None of the .egg-info directories should be present
    assert not any(".egg-info" in f for f in files)


def test_get_module_context_with_directory_exclusions(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Test get_module_context respects directory exclusions from config."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    (module_dir / "main.py").write_text("# main")

    # Create excluded directories
    venv = module_dir / ".venv"
    venv.mkdir()
    (venv / "lib.py").write_text("# venv lib")

    build = module_dir / "build"
    build.mkdir()
    (build / "output.py").write_text("# build output")

    # Create included directory
    src = module_dir / "src"
    src.mkdir()
    (src / "code.py").write_text("# source code")

    # Create config with directory exclusions
    config_content = """
[exclusions]
dirs = [".venv", "build"]
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    mocker.patch("src.input.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir), depth=-1)

    # Should include main.py and src/code.py
    assert "main.py" in context
    assert "# main" in context
    assert "code.py" in context
    assert "# source code" in context

    # Should not include files from excluded directories
    assert "lib.py" not in context
    assert "# venv lib" not in context
    assert "output.py" not in context
    assert "# build output" not in context


def test_get_module_context_default_directory_exclusions(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Test get_module_context applies sensible default directory exclusions."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    (module_dir / "main.py").write_text("# main")

    # Create directories that should be excluded by default
    for dirname in [".venv", "node_modules", "__pycache__", "dist", ".git"]:
        dir_path = module_dir / dirname
        dir_path.mkdir()
        (dir_path / "file.py").write_text(f"# {dirname} file")

    # Create included directory
    src = module_dir / "src"
    src.mkdir()
    (src / "code.py").write_text("# source code")

    # No config file - should use defaults
    mocker.patch("src.input.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir), depth=-1)

    # Should include only main.py and src/code.py
    assert "main.py" in context
    assert "code.py" in context
    assert "# source code" in context

    # None of the default excluded directories should be present
    for dirname in [".venv", "node_modules", "__pycache__", "dist", ".git"]:
        assert f"# {dirname} file" not in context


def test_get_module_context_oserror_on_module_path(mocker: MockerFixture) -> None:
    """Test get_module_context handles OSError when accessing module path."""
    mock_console = mocker.patch("src.input.code_analyzer.console")
    # Mock load_config to raise OSError (simulating permission denied on module path)
    mocker.patch(
        "src.input.code_analyzer.load_config", side_effect=OSError("Permission denied")
    )

    context = get_module_context(module_path="/some/path")

    # Should return empty string
    assert context == ""
    # Should log the error
    assert any(
        "Error accessing module path" in str(call)
        for call in mock_console.print.call_args_list
    )


# Tests for multi-language file type support


def test_find_source_files_multiple_extensions(tmp_path: Path) -> None:
    """Test _find_source_files finds multiple file types."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    (module_dir / "file1.py").write_text("python")
    (module_dir / "file2.js").write_text("javascript")
    (module_dir / "file3.ts").write_text("typescript")
    (module_dir / "file4.txt").write_text("text")

    files = _find_source_files(
        module_path=str(module_dir),
        depth=0,
        file_types=[".py", ".js", ".ts"],
        excluded_dirs=[],
    )

    assert len(files) == 3
    assert any("file1.py" in f for f in files)
    assert any("file2.js" in f for f in files)
    assert any("file3.ts" in f for f in files)
    assert not any("file4.txt" in f for f in files)


def test_find_source_files_extension_normalization(tmp_path: Path) -> None:
    """Test _find_source_files normalizes extensions with/without dots."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    (module_dir / "file1.py").write_text("python")
    (module_dir / "file2.js").write_text("javascript")

    # Test with and without leading dots
    files = _find_source_files(
        module_path=str(module_dir), depth=0, file_types=["py", ".js"], excluded_dirs=[]
    )

    assert len(files) == 2
    assert any("file1.py" in f for f in files)
    assert any("file2.js" in f for f in files)


def test_get_module_context_with_custom_file_types(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Test get_module_context respects custom file types from config."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    # Create files of different types
    (module_dir / "script.py").write_text("# Python")
    (module_dir / "app.js").write_text("// JavaScript")
    (module_dir / "component.ts").write_text("// TypeScript")

    # Create config with custom file types
    config_content = """
file_types = [".js", ".ts"]
"""
    (module_dir / ".dokken.toml").write_text(config_content)

    mocker.patch("src.input.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir))

    # Should include JS and TS files
    assert "app.js" in context
    assert "component.ts" in context
    assert "// JavaScript" in context
    assert "// TypeScript" in context
    # Should not include Python file
    assert "script.py" not in context
    assert "# Python" not in context


def test_get_module_context_default_file_types(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Test get_module_context defaults to .py files when no config."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    (module_dir / "script.py").write_text("# Python")
    (module_dir / "app.js").write_text("// JavaScript")

    mocker.patch("src.input.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir))

    # Should only include Python files by default
    assert "script.py" in context
    assert "# Python" in context
    assert "app.js" not in context
    assert "// JavaScript" not in context


# Tests for concurrency and parallel file reading


def test_get_module_context_concurrent_file_reading(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Test get_module_context reads multiple files concurrently."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    # Create many files to trigger concurrent reading
    num_files = 20
    for i in range(num_files):
        (module_dir / f"file_{i:02d}.py").write_text(f"# File {i}")

    mocker.patch("src.input.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir))

    # All files should be included
    for i in range(num_files):
        assert f"file_{i:02d}.py" in context
        assert f"# File {i}" in context


def test_get_module_context_concurrent_errors_dont_block(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Test that errors in some files don't block reading other files."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    # Create multiple files
    (module_dir / "good1.py").write_text("# Good 1")
    (module_dir / "bad.py").write_text("# Bad")
    (module_dir / "good2.py").write_text("# Good 2")

    mock_console = mocker.patch("src.input.code_analyzer.console")

    # Mock open to fail for bad.py but work for others
    original_open = open

    def selective_open(path, *args, **kwargs):
        if "bad.py" in str(path):
            raise OSError("Simulated read error")
        return original_open(path, *args, **kwargs)

    mocker.patch("builtins.open", side_effect=selective_open)

    context = get_module_context(module_path=str(module_dir))

    # Good files should still be readable
    assert "good1.py" in context
    assert "good2.py" in context
    assert "# Good 1" in context
    assert "# Good 2" in context

    # Should have logged the error for bad.py
    assert any(
        "bad.py" in str(call) and "Could not read" in str(call)
        for call in mock_console.print.call_args_list
    )


def test_get_module_context_parallel_reading_maintains_order(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Test that parallel file reading still maintains sorted file order."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    # Create files in non-alphabetical order
    files = ["zebra.py", "apple.py", "middle.py", "banana.py"]
    for filename in files:
        (module_dir / filename).write_text(f"# {filename}")

    mocker.patch("src.input.code_analyzer.console")

    context = get_module_context(module_path=str(module_dir))

    # Files should appear in alphabetical order despite concurrent reading
    apple_pos = context.find("apple.py")
    banana_pos = context.find("banana.py")
    middle_pos = context.find("middle.py")
    zebra_pos = context.find("zebra.py")

    assert apple_pos < banana_pos < middle_pos < zebra_pos


def test_get_module_context_large_codebase_performance(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Test get_module_context handles large codebases efficiently."""
    module_dir = tmp_path / "large_module"
    module_dir.mkdir()

    # Create a moderately large codebase
    num_files = 50
    for i in range(num_files):
        # Create files with realistic content
        content = f"""
def function_{i}_a():
    '''Function {i}a documentation.'''
    return {i}

def function_{i}_b():
    '''Function {i}b documentation.'''
    return {i} * 2

class Class{i}:
    '''Class {i} documentation.'''
    def method(self):
        return {i}
"""
        (module_dir / f"module_{i:03d}.py").write_text(content)

    mocker.patch("src.input.code_analyzer.console")

    # This should complete without timing out
    start = time.time()
    context = get_module_context(module_path=str(module_dir))
    elapsed = time.time() - start

    # Should complete reasonably quickly (parallel reading should help)
    # Allow generous time for CI environments
    assert elapsed < 10.0, f"Took {elapsed}s, expected < 10s"

    # Verify content is present
    assert len(context) > 0
    assert "module_000.py" in context
    assert f"module_{num_files - 1:03d}.py" in context


def test_get_module_context_mixed_success_and_failure(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Test concurrent reading handles mix of successful and failed reads."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    # Create multiple files
    for i in range(10):
        (module_dir / f"file_{i}.py").write_text(f"# File {i}")

    mock_console = mocker.patch("src.input.code_analyzer.console")

    # Simulate failures on files 3, 5, and 7
    original_open = open
    failing_files = {"file_3.py", "file_5.py", "file_7.py"}

    def selective_open(path, *args, **kwargs):
        if any(fail_name in str(path) for fail_name in failing_files):
            raise OSError("Simulated error")
        return original_open(path, *args, **kwargs)

    mocker.patch("builtins.open", side_effect=selective_open)

    context = get_module_context(module_path=str(module_dir))

    # Successful files should be present
    for i in [0, 1, 2, 4, 6, 8, 9]:
        assert f"file_{i}.py" in context
        assert f"# File {i}" in context

    # Failed files should not be present
    for i in [3, 5, 7]:
        # The file name appears in the error message, but not content
        assert f"# File {i}" not in context

    # Should have 3 error messages
    error_calls = [
        call
        for call in mock_console.print.call_args_list
        if "Could not read" in str(call)
    ]
    assert len(error_calls) == 3
