# Dokken - Style Guide

Clean separation of concerns architecture. Each module has a single, well-defined responsibility.

## Quick Reference

**Common commands:**

```bash
# Code quality
uv run ruff format              # Format code
uv run ruff check --fix         # Lint and auto-fix
uvx ty check                    # Type checking

# Testing
uv run pytest tests/ --cov=src --cov-report=term-missing

# Commits (must use Conventional Commits)
git commit -m "feat: add new feature"
git commit -m "fix: correct bug"
git commit -m "docs: update documentation"
```

**Key patterns:**

- Function-based tests (never class-based)
- Dependency injection (pass dependencies as parameters)
- Mock all external dependencies (LLM, git, file I/O)
- Conventional Commits for all commits to `main`

## File Structure

```
src/
├── main.py              # CLI entry points (Click) - thin UI layer
├── workflows.py         # High-level orchestration - business logic
├── llm.py               # LLM client and operations - structured output
├── prompts.py           # LLM prompt templates - constants for easy iteration
├── config.py            # Configuration loading - .dokken.toml
├── records.py           # Pydantic models - structured data validation
├── exceptions.py        # Custom exceptions
├── git.py               # Git operations - subprocess wrapper
├── input/               # Input gathering for documentation generation
│   ├── code_analyzer.py # Code context extraction - pure functions
│   └── human_in_the_loop.py # Interactive questionnaires - questionary
├── doctypes/            # Documentation type system
│   ├── types.py         # DocType enum definitions
│   └── configs.py       # DocType configuration registry
└── output/              # Output formatting and transformation
    ├── formatters.py    # Structured data → markdown conversion
    └── merger.py        # Markdown parsing and incremental updates
```

## Module Responsibilities

**`main.py` - CLI Entry Points**

- Click-based CLI interface only
- Delegates to `workflows.py` (no business logic here)
- Rich console for user-facing output

**`workflows.py` - Orchestration**

- High-level business logic
- Coordinates: input → LLM → output
- Importable without CLI for scripting

**`input/` - Input Gathering**

- `code_analyzer.py`: Code context extraction with pure functions, no LLM calls
- `human_in_the_loop.py`: Interactive questionnaires for capturing human intent
- Configurable depth traversal (`depth` parameter)
- Respects `.dokken.toml` exclusions

**`llm.py` - LLM Operations**

- LLM initialization and interaction
- Uses prompts from `prompts.py`
- Returns structured Pydantic objects (from `records.py`)

**`prompts.py` - Prompt Templates**

- All LLM prompts as module-level constants
- Easy iteration without touching logic
- Git diffs show prompt changes clearly
- Example: `DRIFT_CHECK_PROMPT`, `MODULE_GENERATION_PROMPT`

**`doctypes/` - Documentation Type System**

- `types.py`: `DocType` enum defining documentation types (MODULE_README, PROJECT_README, STYLE_GUIDE)
- `configs.py`: Registry mapping each DocType to its configuration (prompt, formatter, intent model, questions)
- Centralizes doc type configuration for easy extension

**`output/` - Output Formatting and Transformation**

- `formatters.py`: Pure functions converting structured Pydantic models to markdown
- `merger.py`: Markdown parsing and incremental update application
- All output generation and document manipulation

**`config.py` - Configuration**

- Loads `.dokken.toml` exclusion rules
- Repo-level and module-level configs
- Module config overrides repo config

**`records.py` - Data Models**

- Pydantic models for type-safe validation
- Used by LLM for structured output

## Dependency Flow

```
main.py (CLI) → workflows.py (Orchestration) → input/, llm.py, output/
                                                 ↓      ↓        ↓
                                                 config.py   prompts.py  doctypes/
                                                             records.py  records.py
                                                             doctypes/
```

## Code Style

**Formatting & Linting:**

- `uv run ruff format` - Format code (PEP 8)
- `uv run ruff check --fix` - Lint and auto-fix
- `uvx ty check` - Type checking

**Conventions:**

- Type hints everywhere
- Absolute imports
- Double quotes for strings
- Imports at top (unless breaking circular imports)

**Function/File Size:**

- Keep functions simple (if Ruff says "too complex", refactor)
- Consider splitting files at 300-500 lines

**Common Patterns:**

- Dependency injection (pass dependencies as parameters)
- Pure functions (no side effects in business logic)
- Structured output (Pydantic models for LLM responses)

## How to Add Features

**Add new prompt:**

1. Add constant to `prompts.py`
1. Use it in `llm.py`

**Add new LLM operation:**

1. Add prompt to `prompts.py`
1. Add function to `llm.py`
1. Use it in `workflows.py`

**Add new output format:**

1. Add formatter to `src/output/formatters.py`
1. Call from `workflows.py`

**Add new CLI command:**

1. Add `@cli.command()` to `main.py`
1. Add workflow to `workflows.py` (if needed)

## Git Workflow

**REQUIRED: Conventional Commits for all commits to `main`**

Uses [release-please](https://github.com/googleapis/release-please) for automated versioning and PyPI publishing.

**Format:**

```
<type>: <description>

[optional body]
[optional footer]
```

**Commit Types:**

| Type | Version Bump | Changelog | Example |
| ----------- | --------------------- | --------- | -------------------------------------------- |
| `feat:` | Minor (0.1.0 → 0.2.0) | ✅ | `feat: add PDF export` |
| `fix:` | Patch (0.1.0 → 0.1.1) | ✅ | `fix: correct drift detection logic` |
| `docs:` | None | ✅ | `docs: update API documentation` |
| `refactor:` | None | ✅ | `refactor: simplify code analyzer` |
| `perf:` | None | ✅ | `perf: optimize LLM token usage` |
| `test:` | None | ❌ | `test: add coverage for formatters` |
| `chore:` | None | ❌ | `chore: update dependencies` |
| `ci:` | None | ❌ | `ci: add GitHub Actions workflow` |
| `build:` | None | ❌ | `build: configure pyproject.toml` |
| `style:` | None | ❌ | `style: format code with ruff` |

**Breaking Changes (triggers major version 0.1.0 → 1.0.0):**

- Add `!` after type: `feat!: remove deprecated API`
- Or use footer: `BREAKING CHANGE: API now returns JSON`

**Examples:**

```bash
# Feature
git commit -m "feat: add support for markdown export"

# Bug fix
git commit -m "fix: correct drift detection logic for nested functions"

# Breaking change
git commit -m "feat!: change CLI argument names

BREAKING CHANGE: Renamed --module to --path"

# Multiple changes - separate commits
git commit -m "feat: add PDF export"
git commit -m "fix: handle edge case"
git commit -m "docs: add PDF guide"
```

**Pre-Commit Checklist:**

- ✅ Conventional commit format
- ✅ `uv run pytest tests/ --cov=src`
- ✅ `uv run ruff format && uv run ruff check`
- ✅ `uvx ty check`

See [docs/releasing-to-pypi.md](releasing-to-pypi.md) for release workflow.

## Testing

**Target: 99% coverage minimum** (enforced in `pyproject.toml`)

**Framework:**

- pytest + pytest-cov (coverage) + pytest-mock (mocking)
- Click's CliRunner for CLI testing

**Test Structure:**

```
tests/
├── conftest.py         # Shared fixtures
├── test_*.py           # Mirror src/ structure
```

### Running Tests

```bash
# All tests with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing

# Specific test file
uv run pytest tests/test_git.py

# Specific test function
uv run pytest tests/test_git.py::test_setup_git_checks_out_main

# HTML coverage report
uv run pytest tests/ --cov=src --cov-report=html
# Then open htmlcov/index.html
```

### Core Testing Principles

**1. Function-Based Tests (NEVER class-based)**

```python
# ✅ Good
def test_generate_markdown_includes_title(sample_doc: ComponentDocumentation) -> None:
    markdown = generate_markdown(doc_data=sample_doc)
    assert "# Component Overview" in markdown

# ❌ Bad
class TestGenerateMarkdown:
    def test_includes_title(self) -> None: ...
```

**2. Mock All External Dependencies**

- LLM API calls
- Git subprocess calls
- File I/O operations
- Console output

```python
def test_check_drift(mocker: MockerFixture, mock_llm_client: Gemini) -> None:
    mock_program = mocker.patch("src.llm.LLMTextCompletionProgram")
    expected = DocumentationDriftCheck(drift_detected=False, rationale="OK")
    mock_program.from_defaults.return_value.return_value = expected

    result = check_drift(llm=mock_llm_client, context="...", current_doc="...")
    assert result == expected
```

**3. Use Parametrization**

```python
@pytest.mark.parametrize("input_value,expected", [
    ("value1", "result1"),
    ("value2", "result2"),
])
def test_function(input_value: str, expected: str) -> None:
    assert function_under_test(input_value) == expected
```

**4. Shared Fixtures in conftest.py**

```python
# conftest.py
@pytest.fixture
def sample_doc() -> ComponentDocumentation:
    return ComponentDocumentation(component_name="Sample", ...)

# test_*.py
def test_something(sample_doc: ComponentDocumentation) -> None:
    ...
```

**5. Test Units in Isolation**

- One function per test
- Mock dependencies at module boundaries
- Avoid end-to-end tests in unit tests

### Best Practices

**Descriptive test names:**

```python
# ✅ Good
def test_generate_markdown_sorts_decisions_alphabetically() -> None: ...

# ❌ Bad
def test_markdown() -> None: ...
```

**Test both happy and sad paths:**

```python
def test_success(mocker: MockerFixture) -> None:
    mocker.patch.dict(os.environ, {"API_KEY": "test"})
    result = function()
    assert result is not None

def test_missing_key(mocker: MockerFixture) -> None:
    mocker.patch.dict(os.environ, {}, clear=True)
    with pytest.raises(ValueError, match="API_KEY"):
        function()
```

**Use tmp_path for file operations:**

```python
def test_writes_file(tmp_path: Path) -> None:
    output = tmp_path / "output.txt"
    write_function(str(output))
    assert output.read_text() == "expected"
```

**When to write tests:**

- ✅ All new functions/classes
- ✅ Bug fixes (test first, then fix)
- ✅ Edge cases and error handling
- ❌ Temporary debugging code

## Key Design Decisions

**Configurable Depth Analysis:**

- `input/code_analyzer.py` supports depth parameter (0=root only, 1=root+1 level, -1=infinite)

**Alphabetically Sorted Decisions:**

- Formatters sort design decisions alphabetically to prevent diff noise

**Drift-Based Generation:**

- Only generates docs when drift detected or no doc exists (saves LLM calls)
- Criteria in `DRIFT_CHECK_PROMPT` (`src/prompts.py:6`)

**Human-in-the-Loop:**

- Interactive questionnaire captures intent AI can't infer from code
- See `input/human_in_the_loop.py`
