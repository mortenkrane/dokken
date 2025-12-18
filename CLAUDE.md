# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

**For comprehensive architecture, code style, testing, and git workflow details, see [docs/style-guide.md](docs/style-guide.md).**

## Project Overview

Dokken is an AI-powered documentation generation and drift detection tool. Commands:

- `dokken check <module>` - Detects documentation drift
- `dokken generate <module>` - Generates/updates documentation

## Code Quality Commands

**ALWAYS run these commands after making changes:**

```bash
# Format and lint
ruff format
ruff check --fix

# Type checking
uvx ty check

# Format markdown
uvx mdformat *.md docs/ src/

# Run tests with coverage
pytest src/tests/ --cov=src --cov-report=term-missing
```

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
- **Exclusion Rules**: Respects `.dokken.toml` config (see [docs/style-guide.md](docs/style-guide.md#exclusion-configuration))
- **Testing**: Always use function-based tests (never class-based), mock all external dependencies, use fixtures from `conftest.py`
