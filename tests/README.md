# Testing Conventions

This document describes the testing patterns, conventions, and best practices used in the Dokken test suite.

## Table of Contents

1. [Running Tests](#running-tests)
1. [Test Structure](#test-structure)
1. [Mocking Guidelines](#mocking-guidelines)
1. [Coverage Requirements](#coverage-requirements)
1. [Fixtures](#fixtures)
1. [Parametrization](#parametrization)
1. [Integration Testing](#integration-testing)
1. [Error Handling Tests](#error-handling-tests)

## Running Tests

### Basic Commands

```bash
# Run all tests with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_llm.py

# Run specific test function
uv run pytest tests/test_llm.py::test_check_drift_detects_drift_when_functions_removed

# Generate HTML coverage report
uv run pytest tests/ --cov=src --cov-report=html
```

### Coverage Threshold

Coverage is enforced at **99% minimum** via `pyproject.toml`:

```toml
[tool.coverage.report]
fail_under = 99
```

All new code must include tests. Tests must cover both happy paths and error cases.

## Test Structure

### Function-Based Tests Only

**✅ ALWAYS use function-based tests:**

```python
def test_generate_doc_returns_structured_documentation(
    mocker: MockerFixture,
    mock_llm_client: LLM,
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test generate_doc returns structured ModuleDocumentation."""
    # Test implementation
```

**❌ NEVER use class-based tests:**

```python
# WRONG - Do not do this
class TestGenerateDoc:
    def test_returns_structured_documentation(self) -> None:
        # Test implementation
```

### Naming Convention

Use descriptive test names following this pattern:

```
test_<function>_<scenario>_<expected_result>
```

**Examples:**

```python
def test_check_drift_detects_drift_when_functions_removed() -> None:
    """Test check_drift detects drift when documented functions are removed."""
    pass

def test_initialize_llm_with_anthropic_key() -> None:
    """Test initialize_llm creates Anthropic client when ANTHROPIC_API_KEY is set."""
    pass

def test_generate_documentation_writes_readme() -> None:
    """Test generate_documentation writes README.md file."""
    pass
```

### Docstrings

Every test must have a docstring describing what it tests:

```python
def test_check_drift_cache_hit(
    mocker: MockerFixture,
    mock_llm_client: LLM,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test check_drift returns cached result on cache hit."""
    # Test implementation
```

### One Assertion Per Test (When Possible)

Prefer focused tests with a single logical assertion:

```python
def test_find_repo_root_with_git(git_repo: Path) -> None:
    """Test find_repo_root finds .git directory."""
    nested = git_repo / "src" / "module"
    nested.mkdir(parents=True)

    result = find_repo_root(str(nested))

    assert result == str(git_repo)
```

## Mocking Guidelines

### LLM Operations: Mock at Function Level

**Always mock LLMTextCompletionProgram for LLM operations:**

```python
def test_check_drift_detects_drift_when_functions_removed(
    mocker: MockerFixture,
    mock_llm_client: LLM,
) -> None:
    """Test check_drift detects drift when documented functions are removed."""
    # Mock the LLM program to return drift detected
    drift_result = DocumentationDriftCheck(
        drift_detected=True,
        rationale="Function 'create_session()' is documented but no longer exists in code.",
    )

    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = drift_result
    mock_program_class.from_defaults.return_value = mock_program

    # Test code
    result = check_drift(llm=mock_llm_client, context=code, current_doc=doc)

    assert result.drift_detected is True
```

**Use the `mock_llm_client` fixture from conftest.py:**

```python
@pytest.fixture
def mock_llm_client(mocker: MockerFixture) -> LLM:
    """Mock LLM client with proper typing."""
    mock_client = mocker.MagicMock(spec=["model", "temperature"])
    mock_client.model = "gemini-2.5-flash"
    mock_client.temperature = 0.0
    return cast(LLM, mock_client)
```

### Console Output: Use Fixtures from conftest.py

**For console mocking, use pre-configured fixtures:**

```python
def test_check_documentation_drift_invalid_directory(
    mock_workflows_console, tmp_path: Path
) -> None:
    """Test check_documentation_drift exits when given invalid directory."""
    invalid_path = str(tmp_path / "nonexistent")

    with pytest.raises(SystemExit) as exc_info:
        check_documentation_drift(target_module_path=invalid_path)

    assert exc_info.value.code == 1
```

**Available console fixtures:**

- `mock_console` - Mocks all console instances
- `mock_workflows_console` - Mocks `src.workflows.console`
- `mock_main_console` - Mocks `src.main.console`
- `mock_code_analyzer_console` - Mocks `src.code_analyzer.console`
- `mock_hitl_console` - Mocks `src.human_in_the_loop.console`
- `mock_all_consoles` - Returns dict of all mocked consoles

### File I/O: Use tmp_path, Avoid Mocking

**✅ Use pytest's `tmp_path` fixture for file operations:**

```python
def test_ensure_output_directory_creates_directory(tmp_path: Path) -> None:
    """Test ensure_output_directory creates parent directory."""
    output_path = tmp_path / "new_dir" / "subdir" / "file.md"

    ensure_output_directory(str(output_path))

    # Parent directory should be created
    assert (tmp_path / "new_dir" / "subdir").exists()
```

**❌ Avoid mocking file operations unless testing error handling:**

```python
# Only mock file operations for error scenarios
def test_write_permission_errors(mocker: MockerFixture, tmp_path: Path) -> None:
    """Test generate_documentation handles write permission errors correctly."""
    # ... setup code ...

    # Mock file write to fail with permission error
    mocker.patch("builtins.open", side_effect=PermissionError("Permission denied"))

    with pytest.raises(PermissionError, match="Permission denied"):
        generate_documentation(target_module_path=str(module_dir))
```

### External APIs: Mock at API Client Level

**Mock at the API initialization level, not individual methods:**

```python
def test_initialize_llm_with_anthropic_key(mocker: MockerFixture) -> None:
    """Test initialize_llm creates Anthropic client when ANTHROPIC_API_KEY is set."""
    mocker.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_api_key"}, clear=True)
    mock_anthropic = mocker.patch("src.llm.llm.Anthropic")

    llm = initialize_llm()

    mock_anthropic.assert_called_once_with(
        model="claude-3-5-haiku-20241022", temperature=TEMPERATURE, max_tokens=8192
    )
    assert llm == mock_anthropic.return_value
```

## Coverage Requirements

### Minimum Coverage: 99%

All code must maintain at least 99% test coverage. This is enforced in CI via:

```toml
[tool.coverage.report]
fail_under = 99
```

### What to Test

**✅ Always test:**

- Happy paths (expected behavior)
- Error cases (exceptions, edge cases)
- Boundary conditions
- State transitions
- Integration points

**Example - Testing both paths:**

```python
def test_check_drift_no_drift_when_code_matches_docs(
    mocker: MockerFixture,
    mock_llm_client: LLM,
) -> None:
    """Test check_drift returns no drift when code matches documentation."""
    # ... test happy path ...

def test_check_drift_detects_new_functions_added(
    mocker: MockerFixture,
    mock_llm_client: LLM,
) -> None:
    """Test check_drift detects when new functions are added to code."""
    # ... test error/drift case ...
```

### Coverage for Error Handling

Test all error scenarios thoroughly:

```python
def test_llm_api_failure_handling(mocker: MockerFixture, mock_llm_client: LLM) -> None:
    """Test that LLM API failures propagate correctly for caller to handle."""
    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.side_effect = RuntimeError("API connection failed")
    mock_program_class.from_defaults.return_value = mock_program

    with pytest.raises(RuntimeError, match="API connection failed"):
        check_drift(
            llm=mock_llm_client,
            context="def func(): pass",
            current_doc="# Documentation",
        )
```

## Fixtures

### Using Fixtures from conftest.py

Dokken provides shared fixtures in `tests/conftest.py`. Import them in test function signatures:

```python
def test_check_drift_no_drift_when_code_matches_docs(
    mocker: MockerFixture,
    mock_llm_client: LLM,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test check_drift returns no drift when code matches documentation."""
    # Use fixtures directly
    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = sample_drift_check_no_drift
    # ...
```

### Available Fixtures

#### LLM Fixtures

- `mock_llm_client` - Mock LLM client with proper typing

#### Data Fixtures

- `sample_drift_check_no_drift` - DocumentationDriftCheck with drift_detected=False
- `sample_drift_check_with_drift` - DocumentationDriftCheck with drift_detected=True
- `sample_component_documentation` - Sample ModuleDocumentation

#### Directory Fixtures

- `temp_module_dir` - Temporary module directory with Python files
- `git_repo` - Temporary git repository (with `.git` directory)
- `git_repo_with_module` - Git repo with a Python module inside

#### Console Fixtures

- `mock_console` - Mocks all console instances
- `mock_workflows_console` - Mocks `src.workflows.console`
- `mock_main_console` - Mocks `src.main.console`
- `mock_code_analyzer_console` - Mocks `src.code_analyzer.console`
- `mock_hitl_console` - Mocks `src.human_in_the_loop.console`
- `mock_all_consoles` - Returns dict of all mocked consoles

### tmp_path Fixture (pytest built-in)

Use `tmp_path` for temporary file/directory operations:

```python
def test_generate_documentation_writes_readme(
    mocker: MockerFixture,
    tmp_path: Path,
    sample_drift_check_with_drift: DocumentationDriftCheck,
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test generate_documentation writes README.md file."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    readme = module_dir / "README.md"
    readme.write_text("# Old Docs")

    # ... test implementation ...

    # Verify README was written
    assert readme.read_text() == "# New Markdown Content"
```

### Autouse Fixtures

The test suite includes an autouse fixture that clears the drift cache before each test:

```python
@pytest.fixture(autouse=True)
def clear_drift_cache_before_each_test() -> None:
    """Clear drift detection cache before each test to ensure isolation."""
    clear_drift_cache()
```

This ensures test isolation without manual cache management.

## Parametrization

### Using pytest.mark.parametrize

For testing multiple inputs, use parametrization instead of writing separate tests:

```python
@pytest.mark.parametrize(
    "env_var,api_key",
    [
        ("ANTHROPIC_API_KEY", "sk-ant-api03-test"),
        ("OPENAI_API_KEY", "sk-test123"),
        ("GOOGLE_API_KEY", "AIzaSyABC123"),
    ],
)
def test_initialize_llm_with_various_key_formats(
    mocker: MockerFixture, env_var: str, api_key: str
) -> None:
    """Test initialize_llm works with various API key formats."""
    mocker.patch.dict(os.environ, {env_var: api_key}, clear=True)

    if env_var == "ANTHROPIC_API_KEY":
        mocker.patch("src.llm.llm.Anthropic")
    elif env_var == "OPENAI_API_KEY":
        mocker.patch("src.llm.llm.OpenAI")
    else:
        mocker.patch("src.llm.llm.GoogleGenAI")

    llm = initialize_llm()
    assert llm is not None
```

### Complex Parametrization

You can parametrize with complex data structures:

```python
@pytest.mark.parametrize(
    "context,current_doc",
    [
        ("short context", "short doc"),
        ("a" * 1000, "b" * 1000),
        ("context with\nnewlines", "doc with\nnewlines"),
    ],
)
def test_check_drift_handles_various_inputs(
    mocker: MockerFixture,
    mock_llm_client: LLM,
    sample_drift_check_no_drift: DocumentationDriftCheck,
    context: str,
    current_doc: str,
) -> None:
    """Test check_drift handles various context and documentation inputs."""
    # Test implementation
```

## Integration Testing

### Integration Test Principles

Integration tests exercise the full command flow with **only the LLM mocked**. All other modules (code analyzer, config, formatters, etc.) are kept intact.

```python
def test_integration_generate_documentation(
    tmp_path: Path,
    mocker: MockerFixture,
    payment_service_drift_check: DocumentationDriftCheck,
    payment_service_generated_doc: ModuleDocumentation,
) -> None:
    """
    Integration test for doc generation command.

    Tests the full flow of 'dokken generate' with a realistic module structure.
    Only the LLM is mocked; all other components are used as-is.
    """
    # Create a realistic module structure
    module_dir = tmp_path / "payment_service"
    module_dir.mkdir()
    (module_dir / "__init__.py").write_text('"""Payment service module."""\n')
    (module_dir / "processor.py").write_text(PAYMENT_PROCESSOR_CODE)

    # Mock ONLY the LLM
    mock_llm_client = mocker.MagicMock()
    mocker.patch("src.workflows.initialize_llm", return_value=mock_llm_client)
    mocker.patch("src.llm.llm.initialize_llm", return_value=mock_llm_client)

    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.side_effect = [
        payment_service_drift_check,
        payment_service_generated_doc,
    ]
    mock_program_class.from_defaults.return_value = mock_program

    # Mock console and human intent
    mocker.patch("src.main.console")
    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.ask_human_intent", return_value=None)

    # Run the actual CLI command
    runner = CliRunner()
    result = runner.invoke(cli, ["generate", str(module_dir)])

    # Assert command succeeded
    assert result.exit_code == 0

    # Verify real file system changes
    readme_path = module_dir / "README.md"
    assert readme_path.exists()
```

### CLI Testing with CliRunner

Use Click's `CliRunner` for testing CLI commands:

```python
from click.testing import CliRunner
from src.main import cli

def test_cli_command() -> None:
    """Test CLI command execution."""
    runner = CliRunner()
    result = runner.invoke(cli, ["check", "src/module"])

    assert result.exit_code == 0
    assert "No drift detected" in result.output
```

## Error Handling Tests

### Testing Exceptions with pytest.raises

Use `pytest.raises` context manager to test exception handling:

```python
def test_initialize_llm_missing_all_api_keys(mocker: MockerFixture) -> None:
    """Test initialize_llm raises ValueError when no API keys are set."""
    mocker.patch.dict(os.environ, {}, clear=True)

    with pytest.raises(
        ValueError,
        match=r"No API key found\.",
    ):
        initialize_llm()
```

### Testing Multiple Error Scenarios

Create separate tests for each error scenario:

```python
def test_llm_api_failure_handling(mocker: MockerFixture, mock_llm_client: LLM) -> None:
    """Test that LLM API failures propagate correctly for caller to handle."""
    # Test API connection failure
    # ...

def test_llm_rate_limit_error(mocker: MockerFixture, mock_llm_client: LLM) -> None:
    """Test that LLM rate limit errors propagate correctly."""
    # Test rate limiting
    # ...

def test_llm_authentication_error(mocker: MockerFixture, mock_llm_client: LLM) -> None:
    """Test that LLM authentication errors propagate correctly."""
    # Test authentication failure
    # ...
```

### Testing SystemExit

For functions that call `sys.exit()`, use `pytest.raises(SystemExit)`:

```python
def test_check_documentation_drift_invalid_directory(
    mock_workflows_console, tmp_path: Path
) -> None:
    """Test check_documentation_drift exits when given invalid directory."""
    invalid_path = str(tmp_path / "nonexistent")

    with pytest.raises(SystemExit) as exc_info:
        check_documentation_drift(target_module_path=invalid_path)

    assert exc_info.value.code == 1
```

### Testing Cache Corruption and Recovery

Test resilience to corrupted data:

```python
def test_cache_corruption_recovery(tmp_path: Path) -> None:
    """Test load_drift_cache_from_disk recovers from corrupted cache files."""
    cache_file = tmp_path / "corrupted.json"

    # Test 1: Invalid JSON syntax
    cache_file.write_text("{invalid json syntax")
    load_drift_cache_from_disk(str(cache_file))  # Should not raise

    # Test 2: Valid JSON but wrong structure
    cache_file.write_text('{"wrong": "structure"}')
    load_drift_cache_from_disk(str(cache_file))  # Should not raise
```

### Testing Partial Failures in Multi-Module Operations

Test behavior when some operations succeed and others fail:

```python
def test_partial_failure_in_multi_module_check(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    """Test check_multiple_modules_drift handles partial failures correctly."""
    # Create multiple modules
    # ...

    # Simulate LLM failure on second module
    def check_side_effect(*args, **kwargs):
        module_path = kwargs["target_module_path"]
        if "module2" in module_path:
            raise RuntimeError("LLM API unavailable")
        # Other modules would succeed

    mocker.patch(
        "src.workflows.check_documentation_drift", side_effect=check_side_effect
    )

    # Should fail fast and propagate the error
    with pytest.raises(RuntimeError, match="LLM API unavailable"):
        check_multiple_modules_drift()
```

## Summary

**Key Testing Principles:**

1. ✅ Function-based tests only (never class-based)
1. ✅ Descriptive names: `test_<function>_<scenario>_<expected_result>`
1. ✅ Every test has a docstring
1. ✅ Mock at the right level (LLM program, not individual calls)
1. ✅ Use `tmp_path` for file operations
1. ✅ Use fixtures from `conftest.py`
1. ✅ Test both happy paths and error cases
1. ✅ Maintain 99% coverage minimum
1. ✅ Integration tests mock only the LLM
1. ✅ Use parametrization for multiple similar test cases

**Before Committing:**

```bash
# Run formatters
uv run ruff format
uv run ruff check --fix
uvx ty check
uv run mdformat CLAUDE.md CONTRIBUTING.md README.md docs/ src/

# Run tests with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing
```

All tests must pass with 99% coverage before committing changes.
