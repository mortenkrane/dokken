# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

**For comprehensive architecture, code style, testing, and git workflow details, see [docs/style-guide.md](docs/style-guide.md).**

## Project Overview

Dokken is an AI-powered documentation generation and drift detection tool. Commands:

- `dokken check <module>` - Detects documentation drift
- `dokken generate <module>` - Generates/updates documentation

## Code Quality Commands

**Automated checks via pre-commit hooks:**

Pre-commit hooks are configured to automatically run checks on changed files:

- On commit: `ruff format`, `ruff check --fix`, `mdformat`, and `ty check`
- On push: full test suite with coverage

To install hooks (already done if you ran `uv sync --all-groups`):

```bash
uv run pre-commit install
uv run pre-commit install --hook-type pre-push
```

To run hooks manually on all files:

```bash
uv run pre-commit run --all-files
```

**Manual commands (if needed):**

```bash
# Format and lint
uv run ruff format
uv run ruff check --fix

# Type checking
uvx ty check

# Format markdown
uvx mdformat *.md docs/ src/

# Run tests with coverage
uv run pytest src/tests/ --cov=src --cov-report=term-missing
```

**Claude Code hooks (automated for AI sessions):**

Claude Code hooks are configured in `.claude/settings.json` to automatically run quality checks:

- **After file changes** (PostToolUse): Runs `ruff format`, `ruff check --fix`, `mdformat`, and `ty check` on changed files only
- **At session end** (SessionEnd): Runs full test suite with coverage

Hook scripts are in `.claude/hooks/`:

- `format-and-lint.sh` - Code quality checks on changed files
- `run-tests.sh` - Full test suite

These hooks run automatically when Claude Code edits files. No setup required!

## Git Commits

**All commits to `main` MUST use [Conventional Commits](https://www.conventionalcommits.org/)** (e.g., `feat:`, `fix:`, `docs:`). See [docs/style-guide.md](docs/style-guide.md#git-workflow) for details

## Key Design Patterns

1. **Structured Output**: All LLM operations return validated Pydantic models
1. **Prompt-as-Constants**: Prompts stored in `prompts.py` for easy experimentation
1. **Dependency Injection**: Functions receive dependencies as parameters
1. **Pure Functions**: Most business logic is in pure, testable functions
1. **Deterministic LLM**: Temperature=0.0 for reproducible documentation

## Important Implementation Details

When working with this codebase, be aware of these key design decisions:

- **Module Structure**: See [docs/style-guide.md](docs/style-guide.md#module-responsibilities) for separation of concerns
- **Shallow Code Analysis**: `code_analyzer.py` only scans top-level Python files (non-recursive by design)
- **Git Base Branch**: Configurable via `GIT_BASE_BRANCH = "main"` in `git.py`
- **Alphabetically Sorted Decisions**: Formatters sort design decisions alphabetically to prevent diff noise
- **Drift-Based Generation**: Only generates docs when drift detected or no doc exists (saves LLM calls)
- **Stabilized Drift Detection**: Uses criteria-based checklist (see `DRIFT_CHECK_PROMPT` in `src/prompts.py`) - the prompt explicitly defines what constitutes drift vs. minor changes
- **Exclusion Rules**: Respects `.dokken.toml` config (see README.md for user config details, [docs/style-guide.md](docs/style-guide.md#implementation-notes) for implementation)
- **Testing**: Always use function-based tests (never class-based), mock all external dependencies, use fixtures from `conftest.py`
