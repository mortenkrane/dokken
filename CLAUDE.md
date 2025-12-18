# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**For detailed architecture, code style, and testing guidelines, see [docs/style-guide.md](docs/style-guide.md).**

## Project Overview

Dokken is an AI-powered documentation generation and drift detection tool. It supports multiple LLM providers (Claude, OpenAI, and Google Gemini) to automatically keep codebase documentation synchronized with source code changes by detecting drift and generating updated documentation.

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

ALWAYS run these commands and make sure they pass, after making changes.

```bash
# Format code
ruff format

# Check linting
ruff check

# Auto-fix linting issues
ruff check --fix

# Type checking
uvx ty check

# Format markdown
uvx mdformat *.md docs/ src/

# Check markdown formatting
uvx mdformat --check *.md docs/ src/
```

### Git Workflow and Conventional Commits

**IMPORTANT: All commits to `main` MUST use [Conventional Commits](https://www.conventionalcommits.org/) format.**

Dokken uses release-please for automated releases and PyPI publishing. Commit messages drive version bumping and changelog generation.

**Common commit types:**
- `feat:` - New features (bumps minor version)
- `fix:` - Bug fixes (bumps patch version)
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Test changes
- `chore:` - Maintenance tasks

**Examples:**
```bash
git commit -m "feat: add PDF export support"
git commit -m "fix: correct drift detection edge case"
git commit -m "docs: update API examples"
```

**Breaking changes** (bumps major version):
```bash
git commit -m "feat!: remove deprecated CLI flags"
# or
git commit -m "feat: change API format

BREAKING CHANGE: Response now returns JSON instead of XML"
```

**See [docs/style-guide.md](docs/style-guide.md#git-workflow) and [docs/releasing-to-pypi.md](docs/releasing-to-pypi.md) for complete details.**

## Key Design Patterns

1. **Structured Output**: All LLM operations return validated Pydantic models
1. **Prompt-as-Constants**: Prompts stored in `prompts.py` for easy experimentation
1. **Dependency Injection**: Functions receive dependencies as parameters (e.g., `llm` client)
1. **Pure Functions**: Most business logic is in pure, testable functions
1. **Deterministic LLM**: Temperature=0.0 for reproducible documentation

### Workflow Flow

**Check Command:**

1. Validate module path exists
1. Initialize LLM (requires one of: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or `GOOGLE_API_KEY`)
1. Extract code context (Python files + git diff vs main)
1. Read existing README.md
1. Call LLM to detect drift
1. Raise `DocumentationDriftError` if drift detected (exit code 1)

**Generate Command:**

1. Git setup: checkout main, pull, create branch `dokken/docs-YYYY-MM-DD`
1. Initialize LLM
1. Extract code context
1. Check for drift
1. If no drift + doc exists: return early (optimization)
1. If drift detected: generate structured docs via LLM
1. Format to Markdown
1. Write/overwrite README.md

## Environment Setup

**Required:**

- Python 3.13.7+ (managed via mise - see `.mise.toml`)
- uv 0.9.18+ (managed via mise)
- One of the following API keys (checked in priority order):
  - `ANTHROPIC_API_KEY` - For Claude (claude-3-5-haiku-20241022)
  - `OPENAI_API_KEY` - For OpenAI (gpt-4o-mini)
  - `GOOGLE_API_KEY` - For Google Gemini (gemini-2.5-flash)

**Package Manager:** uv with lock file
**Version Manager:** mise with automatic venv activation

**LLM Configuration:**

- All providers use Temperature: 0.0 (deterministic, reproducible output)
- Priority: Claude > OpenAI > Google Gemini (if multiple API keys are set)
- Default models selected for balance of speed, cost, and quality

## Exclusion Configuration

Dokken supports excluding specific files and symbols from documentation using `.dokken.toml` configuration files.

### Configuration File Location

Config files can be placed in two locations (module-level overrides repo-level):

1. **Repository root**: `.dokken.toml` - Global exclusions for all modules
1. **Module directory**: `<module>/.dokken.toml` - Module-specific exclusions

### Configuration Format

```toml
[exclusions]
# Exclude entire files (supports glob patterns)
files = [
    "__init__.py",      # Exact filename
    "*_test.py",        # All test files
    "conftest.py"
]

# Exclude specific symbols (functions/classes) by name
# Supports wildcards
symbols = [
    "_private_*",       # All symbols starting with _private_
    "setup_fixtures",   # Specific function name
    "Temporary*"        # All classes starting with Temporary
]
```

### Use Cases

- **Exclude test utilities**: Keep test helpers out of module documentation
- **Hide private functions**: Exclude internal implementation details (e.g., `_private_*`)
- **Filter boilerplate**: Skip `__init__.py` or other boilerplate files
- **Temporary code**: Exclude experimental or temporary code from docs

### How It Works

1. `code_analyzer.py` loads config from both repo root and module directory
1. Module-level config extends (not replaces) repo-level config
1. Files are filtered using glob pattern matching (via `fnmatch`)
1. Symbols are filtered using AST parsing - only top-level functions/classes are excluded
1. Nested functions and class methods are preserved even if they match exclusion patterns

## Important Implementation Details

- **Shallow Code Analysis**: `code_analyzer.py` only scans top-level Python files (non-recursive by design)
- **Git Base Branch**: Configurable via `GIT_BASE_BRANCH = "main"` in `git.py`
- **Alphabetically Sorted Decisions**: Formatters sort design decisions alphabetically to prevent diff noise
- **Drift-Based Generation**: Only generates docs when drift detected or no doc exists (saves LLM calls)
- **Stabilized Drift Detection**: Uses criteria-based checklist (see `DRIFT_CHECK_PROMPT` in `src/prompts.py`) to improve consistency. The prompt explicitly defines what constitutes drift vs. minor changes that shouldn't trigger updates, making detection more deterministic across runs.
- **Exclusion Rules**: Respects `.dokken.toml` config for filtering files and symbols from documentation
