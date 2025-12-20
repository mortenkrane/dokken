# Style guide for Dokken

## Project structure

Dokken follows a clean separation of concerns architecture, with each module having a single, well-defined responsibility.

### Overview

```
src/
├── __init__.py          # Package initialization
├── main.py              # CLI entry points (Click commands)
├── exceptions.py        # Custom exceptions
├── prompts.py          # LLM prompt templates as constants
├── config.py           # Configuration loading (.dokken.toml)
├── code_analyzer.py    # Code context extraction
├── llm.py              # LLM client initialization and operations
├── formatters.py       # Documentation formatting (Markdown, etc.)
├── workflows.py        # High-level orchestration logic
├── human_in_the_loop.py # Interactive user questionnaires
└── records.py          # Pydantic models for structured data
```

### Module Responsibilities

#### `main.py` - CLI Entry Points

- Contains **only** the Click-based CLI interface
- Delegates all business logic to `workflows.py`
- Handles user-facing output with Rich console
- Should remain thin - just UI concerns

**Example:**

```python
@cli.command()
def check(module_path: str):
    # Just CLI glue - delegates to workflows
    check_documentation_drift(target_module_path=module_path)
```

#### `exceptions.py` - Custom Exceptions

- All custom exception classes
- Add new exceptions here as needed

#### `prompts.py` - LLM Prompt Templates

- **All LLM prompts as module-level constants**
- Easy to iterate on prompts without touching logic
- Version control tracks prompt changes clearly
- Makes A/B testing prompts straightforward

**Example:**

```python
DRIFT_CHECK_PROMPT = """You are a Documentation Drift Detector..."""
```

**Why separate prompts?**

- Prompts are the most frequently tweaked part of LLM applications
- Keeping them as constants makes experimentation faster
- Changes are visible in git diffs
- Can add prompt variants easily

#### `config.py` - Configuration Loading

- Loads exclusion rules from `.dokken.toml` files
- Supports both repo-level and module-level configs
- Uses Pydantic for config validation
- Handles config merging (module overrides repo)

#### `code_analyzer.py` - Code Context Extraction

- Analyzes code to create context for LLM
- Reads Python files from module directories
- Respects exclusion rules from `.dokken.toml`
- Supports configurable directory depth traversal (`depth` parameter)
- Pure extraction logic, no LLM calls
- Could be extended to support other languages

#### `llm.py` - LLM Client and Operations

- LLM initialization and configuration
- Direct LLM interaction functions
- Uses prompts from `prompts.py`
- Returns structured Pydantic objects

#### `formatters.py` - Output Formatting

- Pure data transformation, no I/O
- Converts structured data to various formats
- Currently: Markdown formatting
- Future: Could add HTML, PDF, etc.

#### `workflows.py` - Orchestration Logic

- **High-level business logic**
- Coordinates analyzer → LLM → formatter → human-in-the-loop
- Contains the full flow of operations
- Can be imported and used without CLI

**Why separate workflows?**

- Reusable - can be imported by other scripts
- Testable - can be tested without CLI
- Clear business logic separated from UI

#### `human_in_the_loop.py` - Interactive Questionnaires

- Interactive questionnaire system using `questionary`
- Captures human intent that AI cannot infer from code
- Asks about problems solved, responsibilities, system context
- Returns structured `HumanIntent` Pydantic model
- Graceful skip handling (Ctrl+C on first question skips all)

#### `records.py` - Data Models

- Pydantic models for structured data
- Defines the "shape" of our data
- Used by LLM for structured output
- Type-safe data validation

### Dependency Flow

```
main.py (CLI)
    └── workflows.py (Orchestration)
            ├── code_analyzer.py
            │   └── config.py
            ├── llm.py
            │   ├── prompts.py
            │   └── records.py
            ├── formatters.py
            │   └── records.py
            ├── human_in_the_loop.py
            │   └── records.py
            └── exceptions.py
```

### Adding New Features

**Adding a new prompt:**

1. Add constant to `prompts.py`
1. Use it in `llm.py`

**Adding a new LLM operation:**

1. Add prompt to `prompts.py`
1. Add function to `llm.py`
1. Use it in `workflows.py`

**Adding a new output format:**

1. Add formatter function to `formatters.py`
1. Call it from `workflows.py`

**Adding a new CLI command:**

1. Add `@cli.command()` to `main.py`
1. Optionally add new workflow to `workflows.py`

## Code Style

### General Python Style

- Follow PEP 8 guidelines
- Use Ruff for code formatting and linting
  - Run `ruff format` to format code
  - Run `ruff check` to check for linting issues
  - Run `ruff check --fix` to automatically fix linting issues
- Use type hints consistently throughout the codebase
  - Run `uvx ty check` for type checking
- Use absolute imports
- Keep imports at the top of the file, unless we need to break circular imports
- Use double quotes for strings
- Keep functions simple and bite-sized
  - If Ruff says your function is "too complex", it probably is, and should be refactored
- Keep files from growing indefinitely
  - We define no max limit, but it's recommended to start looking for potential dividers when files reach 300-500 lines
  - Typically, the solution will be to convert a big file into a directory with subfiles

## Git Workflow

### Conventional Commits

**All commits to the `main` branch MUST follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.**

Dokken uses [release-please](https://github.com/googleapis/release-please) for automated versioning, changelog generation, and PyPI publishing. This automation is driven entirely by commit messages.

#### Commit Format

```
<type>: <description>

[optional body]

[optional footer(s)]
```

#### Required Commit Types

| Type | Description | Version Bump | In Changelog |
|------|-------------|--------------|--------------|
| `feat:` | New feature | Minor (0.1.0 → 0.2.0) | ✅ Yes |
| `fix:` | Bug fix | Patch (0.1.0 → 0.1.1) | ✅ Yes |
| `docs:` | Documentation changes | None | ✅ Yes |
| `refactor:` | Code refactoring | None | ✅ Yes |
| `perf:` | Performance improvements | None | ✅ Yes |
| `test:` | Test changes | None | ❌ No |
| `chore:` | Maintenance tasks | None | ❌ No |
| `ci:` | CI/CD changes | None | ❌ No |
| `build:` | Build system changes | None | ❌ No |
| `style:` | Code style changes (formatting) | None | ❌ No |

#### Breaking Changes

To trigger a major version bump (0.1.0 → 1.0.0), use one of:

1. Add `!` after the type: `feat!: remove deprecated API`
1. Add `BREAKING CHANGE:` in the footer:
   ```
   feat: change response format

   BREAKING CHANGE: API now returns JSON instead of XML
   ```

#### Examples

**Feature addition:**

```bash
git commit -m "feat: add support for markdown export"
```

**Bug fix:**

```bash
git commit -m "fix: correct drift detection logic for nested functions"
```

**Documentation:**

```bash
git commit -m "docs: update API documentation with examples"
```

**Refactoring:**

```bash
git commit -m "refactor: simplify code analyzer extraction logic"
```

**Breaking change:**

```bash
git commit -m "feat!: change CLI argument names

BREAKING CHANGE: Renamed --module to --path for consistency"
```

**Multiple changes:**

```bash
# Make separate commits for each type
git commit -m "feat: add PDF export"
git commit -m "fix: handle edge case in git detection"
git commit -m "docs: add PDF export guide"
```

#### Why This Matters

- **Automated releases**: Commits trigger version bumps automatically
- **Clean changelogs**: Users see clear, categorized changes
- **No manual version management**: release-please handles everything
- **PyPI publishing**: Releases are automatically published when PRs merge

#### Pre-Commit Checklist

Before committing to `main`, ensure:

1. ✅ Commit message follows conventional format
1. ✅ Tests pass (`pytest src/tests/ --cov=src`)
1. ✅ Code is formatted (`ruff format`)
1. ✅ Linting passes (`ruff check`)
1. ✅ Type checking passes (`uvx ty check`)

**See [docs/releasing-to-pypi.md](releasing-to-pypi.md) for detailed release workflow documentation.**

## Testing

Dokken uses pytest with comprehensive unit tests, aiming for close to 100% coverage.

### Testing Framework

- **pytest** - Primary testing framework
- **pytest-cov** - Coverage reporting
- **pytest-mock** - Mocking and patching
- **Click's CliRunner** - CLI testing

### Test Structure

Tests mirror the source structure in `src/tests/`:

```
src/tests/
├── conftest.py              # Shared fixtures
├── test_exceptions.py       # Tests for src/exceptions.py
├── test_prompts.py         # Tests for src/prompts.py
└── test_main.py            # Tests for src/main.py (CLI)
(etc)
```

### Core Testing Principles

#### 1. Function-Based Tests

**Always use function-based tests, never class-based tests.**

```python
# ✅ Good - function-based
def test_generate_markdown_includes_title(sample_doc):
    markdown = generate_markdown(doc_data=sample_doc)
    assert "# Component Overview" in markdown

# ❌ Bad - class-based
class TestGenerateMarkdown:
    def test_includes_title(self):
        ...
```

#### 2. Use Parametrization to Avoid Duplication

Parametrize tests to test multiple scenarios without code duplication:

```python
@pytest.mark.parametrize(
    "input_value,expected",
    [
        ("value1", "result1"),
        ("value2", "result2"),
        ("value3", "result3"),
    ],
)
def test_function_with_various_inputs(input_value, expected):
    result = function_under_test(input_value)
    assert result == expected
```

#### 3. Comprehensive Mocking

**Mock all external dependencies** to keep tests fast and isolated:

- Mock subprocess calls (git commands)
- Mock LLM API calls
- Mock file I/O operations
- Mock console output

```python
def test_check_drift(mocker, mock_llm_client):
    # Mock the LLM program to avoid actual API calls
    mock_program = mocker.patch("src.llm.LLMTextCompletionProgram")
    expected_result = DocumentationDriftCheck(drift_detected=False, rationale="Up to date")
    mock_program.from_defaults.return_value.return_value = expected_result

    result = check_drift(llm=mock_llm_client, context="...", current_doc="...")

    # Verify the result
    assert result == expected_result
```

#### 4. Use Shared Fixtures

Define reusable test data in `conftest.py`:

```python
# In conftest.py
@pytest.fixture
def sample_component_documentation():
    return ComponentDocumentation(
        component_name="Sample",
        purpose_and_scope="Test purpose",
        design_decisions={"KEY": "Value"},
    )

# In test files
def test_something(sample_component_documentation):
    # Use the fixture
    ...
```

#### 5. Test the Unit in Isolation

Each test should focus on a single unit:

```python
# ✅ Good - tests only check_drift function
def test_check_drift_returns_correct_object(mocker, mock_llm_client):
    mock_program = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program.from_defaults.return_value.return_value = expected_result

    result = check_drift(llm=mock_llm_client, context="...", current_doc="...")

    assert result == expected_result

# ❌ Bad - tests multiple units together
def test_entire_workflow_end_to_end():
    # This tests too much at once
    ...
```

### Running Tests

```bash
# Run all tests
pytest src/tests/

# Run with verbose output
pytest src/tests/ -v

# Run specific test file
pytest src/tests/test_git.py

# Run specific test
pytest src/tests/test_git.py::test_setup_git_checks_out_main

# Run with coverage
pytest src/tests/ --cov=src --cov-report=term-missing

# Generate HTML coverage report
pytest src/tests/ --cov=src --cov-report=html
# Open htmlcov/index.html to view
```

### Coverage Expectations

- **Target: 99% coverage minimum** (enforced in `pyproject.toml`)
- Tests will fail if coverage drops below 99%
- Acceptable untested code:
  - `if __name__ == "__main__"` blocks
  - Abstract methods meant to be overridden
  - Defensive code for truly unreachable edge cases

### Testing Best Practices

#### Test Names Should Be Descriptive

```python
# ✅ Good - clear what is being tested
def test_generate_markdown_sorts_design_decisions_alphabetically():
    ...

# ❌ Bad - unclear what is being tested
def test_markdown():
    ...
```

#### One Assertion Per Concept

Keep tests focused, but don't artificially limit assertions:

```python
# ✅ Good - multiple related assertions
def test_generate_markdown_includes_all_sections(sample_doc):
    markdown = generate_markdown(doc_data=sample_doc)
    assert "## Purpose & Scope" in markdown
    assert "## Key Design Decisions" in markdown
    assert sample_doc.purpose_and_scope in markdown

# ❌ Bad - testing unrelated things
def test_everything(sample_doc):
    assert generate_markdown(...)  # markdown generation
    assert check_drift(...)         # drift checking (unrelated!)
```

#### Test Both Happy and Sad Paths

```python
def test_initialize_llm_success(mocker):
    mocker.patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    llm = initialize_llm()
    assert llm is not None

def test_initialize_llm_missing_api_key(mocker):
    mocker.patch.dict(os.environ, {}, clear=True)
    with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
        initialize_llm()
```

#### Use Temporary Directories for File Operations

```python
def test_function_writes_file(tmp_path):
    # tmp_path is a pytest fixture that creates a temp directory
    output_file = tmp_path / "output.txt"

    write_function(str(output_file))

    assert output_file.exists()
    assert output_file.read_text() == "expected content"
```

#### Mock at the Right Level

Mock at the boundary of your module, not deep inside dependencies:

```python
# ✅ Good - mock at the module boundary
def test_check_drift(mocker, mock_llm_client):
    mock_program = mocker.patch("src.llm.LLMTextCompletionProgram")
    check_drift(llm=mock_llm_client, context="...", current_doc="...")
    mock_program.from_defaults.assert_called()

# ❌ Bad - mocking too deep in dependencies
def test_check_drift(mocker, mock_llm_client):
    mocker.patch("llama_index.core.program.base.BaseLLMProgram")  # Too low-level
    ...
```

### CLI Testing

Use Click's `CliRunner` for testing CLI commands:

```python
from click.testing import CliRunner

def test_check_command_success(runner, mocker):
    runner = CliRunner()
    mocker.patch("src.main.check_documentation_drift")

    result = runner.invoke(cli, ["check", "src/module"])

    assert result.exit_code == 0
    assert "up-to-date" in result.output
```

### When to Write Tests

**Write tests for:**

- All new functions and classes
- Bug fixes (add a failing test first, then fix)
- Edge cases and error handling
- Integration points between modules

**You may skip tests for:**

- Temporary debugging code
- Code that will be deleted soon
- Generated code (like migrations)

### Continuous Integration

Tests should:

- Run on every commit
- Pass before merging to main
- Complete in under 10 seconds for fast feedback
- Not require external services (use mocks!)

### Key Design Decisions

- **Configurable Depth Analysis**: `code_analyzer.py` supports configurable directory traversal depth (0=root only, 1=root+1 level, -1=infinite recursion)
- **Alphabetically Sorted Decisions**: Formatters sort design decisions alphabetically to prevent diff noise
- **Drift-Based Generation**: Only generates docs when drift detected or no doc exists (saves LLM calls)
- **Stabilized Drift Detection**: Uses criteria-based checklist in `DRIFT_CHECK_PROMPT` - explicitly defines what constitutes drift vs. minor changes
- **Human-in-the-Loop**: Interactive questionnaire captures developer intent that AI cannot infer from code alone

