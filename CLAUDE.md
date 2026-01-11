# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

**For comprehensive architecture, code style, testing, and git workflow details, see [docs/style-guide.md](docs/style-guide.md).**

## Project Overview

Dokken is an AI-powered documentation generation and drift detection tool. Commands:

- `dokken check <module>` - Detects documentation drift
- `dokken check --all` - Check all modules configured in `.dokken.toml`
- `dokken generate <module>` - Generates/updates documentation

## CRITICAL: Pre-Commit Requirements

**BEFORE EVERY COMMIT, you MUST run:**

```bash
uv run ruff format
uv run ruff check --fix
uvx ty check
uvx mdformat *.md docs/ src/
```

**Then run tests:**

```bash
uv run pytest tests/ --cov=src --cov-report=term-missing
```

These checks ensure code quality and will be automatically verified by pre-commit hooks. If hooks make changes, stage them and amend your commit.

## Git Commits

**All commits to `main` MUST use [Conventional Commits](https://www.conventionalcommits.org/)** (e.g., `feat:`, `fix:`, `docs:`). See [docs/style-guide.md](docs/style-guide.md#git-workflow) for details

## Key Design Patterns

1. **Structured Output**: All LLM operations return validated Pydantic models
1. **Prompt-as-Constants**: Prompts stored in `prompts.py` for easy experimentation
1. **Dependency Injection**: Functions receive dependencies as parameters
1. **Pure Functions**: Most business logic is in pure, testable functions
1. **Deterministic LLM**: Temperature=0.0 for reproducible documentation

## Important Implementation Details

Key design decisions to keep in mind:

- **Module Structure**: See [docs/style-guide.md](docs/style-guide.md#module-responsibilities) for separation of concerns
- **File Type Overrides**: Module-level `file_types` replace (not extend) repo-level settings in `.dokken.toml`
- **Drift-Based Generation**: Only generates docs when drift detected or no doc exists
- **Search-Optimized Docs**: Templates optimized for grep/search (see `src/output/formatters.py` and `src/prompts.py`)
- **Testing**: Use function-based tests, mock external dependencies, use fixtures from `conftest.py`
