# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**For detailed architecture, code style, and testing guidelines, see [docs/style-guide.md](docs/style-guide.md).**

## Project Overview

Dokken is an AI-powered documentation generation and drift detection tool. It uses Google's Gemini LLM (gemini-2.5-flash) to automatically keep codebase documentation synchronized with source code changes by detecting drift and generating updated documentation.

**Key Capabilities:**
- `dokken check <module>` - Detects documentation drift (for CI/CD pipelines)
- `dokken generate <module>` - Generates/updates documentation with automatic git branching

## Development Commands

### Environment Setup with mise
```bash
# Install mise if not already installed: https://mise.jdx.dev/getting-started.html

# Install Python and uv versions (defined in .mise.toml)
mise install

# The .venv will be automatically created and activated when you cd into the directory
# mise will use uv to create the venv automatically
```

### Running the CLI
```bash
# Install dependencies (uses uv)
# Note: mise will auto-activate .venv when you're in the project directory
uv sync

# Run dokken CLI
dokken --help
dokken check src/module_name
dokken generate src/module_name
```

### Testing
```bash
# Run all tests
pytest src/tests/

# Run with coverage
pytest src/tests/ --cov=src --cov-report=term-missing

# Run specific test file
pytest src/tests/test_workflows.py

# Run single test
pytest src/tests/test_git.py::test_setup_git_checks_out_main
```

**Testing Requirements:**
- Always use function-based tests (never class-based)
- Mock all external dependencies (subprocess, LLM calls, file I/O, console output)
- Use shared fixtures from `conftest.py`
- Target close to 100% test coverage

### Code Quality
```bash
# Format code
ruff format

# Check linting
ruff check

# Auto-fix linting issues
ruff check --fix

# Type checking
uvx ty check
```

## Key Design Patterns

1. **Structured Output**: All LLM operations return validated Pydantic models
2. **Prompt-as-Constants**: Prompts stored in `prompts.py` for easy experimentation
3. **Dependency Injection**: Functions receive dependencies as parameters (e.g., `llm` client)
4. **Pure Functions**: Most business logic is in pure, testable functions
5. **Deterministic LLM**: Temperature=0.0 for reproducible documentation

### Workflow Flow

**Check Command:**
1. Validate module path exists
2. Initialize LLM (requires `GOOGLE_API_KEY` env var)
3. Extract code context (Python files + git diff vs main)
4. Read existing README.md
5. Call LLM to detect drift
6. Raise `DocumentationDriftError` if drift detected (exit code 1)

**Generate Command:**
1. Git setup: checkout main, pull, create branch `dokken/docs-YYYY-MM-DD`
2. Initialize LLM
3. Extract code context
4. Check for drift
5. If no drift + doc exists: return early (optimization)
6. If drift detected: generate structured docs via LLM
7. Format to Markdown
8. Write/overwrite README.md

## Environment Setup

**Required:**
- Python 3.13.7+ (managed via mise - see `.mise.toml`)
- uv 0.9.18+ (managed via mise)
- `GOOGLE_API_KEY` environment variable (for Gemini API)

**Package Manager:** uv with lock file
**Version Manager:** mise with automatic venv activation

**LLM Configuration:**
- Model: `gemini-2.5-flash` (balance of speed/cost/quality)
- Temperature: 0.0 (deterministic, reproducible output)

## Important Implementation Details

- **Shallow Code Analysis**: `code_analyzer.py` only scans top-level Python files (non-recursive by design)
- **Git Base Branch**: Configurable via `GIT_BASE_BRANCH = "main"` in `git.py`
- **Alphabetically Sorted Decisions**: Formatters sort design decisions alphabetically to prevent diff noise
- **Drift-Based Generation**: Only generates docs when drift detected or no doc exists (saves LLM calls)
- **Stabilized Drift Detection**: Uses criteria-based checklist (see `DRIFT_CHECK_PROMPT` in `src/prompts.py`) to improve consistency. The prompt explicitly defines what constitutes drift vs. minor changes that shouldn't trigger updates, making detection more deterministic across runs.
