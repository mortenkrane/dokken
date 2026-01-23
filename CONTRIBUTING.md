# Contributing to Dokken

Thank you for your interest in contributing to Dokken! We welcome contributions of all kinds.

## Getting Started

1. Fork the repository and clone your fork
1. Install dependencies: `mise install && uv sync --all-groups`
1. Set up pre-commit hooks (optional but recommended):
   ```bash
   uv run pre-commit install
   uv run pre-commit install --hook-type pre-push
   ```

## Development Guidelines

### Code Style

Follow the [style guide](docs/style-guide.md) for comprehensive architecture, code style, testing guidelines, and git workflow.

**Key requirements:**

- **Test Coverage**: Ensure 99% test coverage for all new code
- **Type Safety**: All code must pass `uvx ty check`
- **Formatting**: Use `ruff format` and `ruff check --fix`
- **Commit Messages**: Use [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `feat:`, `fix:`, `docs:`)

### Running Code Quality Checks

**With pre-commit hooks (recommended):**

Pre-commit hooks automatically run on changed files:

- On commit: `ruff format`, `ruff check --fix`, `mdformat`, and `ty check`
- On push: full test suite with coverage

Manual run: `uv run pre-commit run --all-files`

**Without pre-commit hooks:**

```bash
# Format and lint
uv run ruff format && uv run ruff check --fix

# Type checking
uvx ty check

# Format markdown
uvx mdformat CLAUDE.md CONTRIBUTING.md README.md docs/ src/

# Run tests with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing
```

### Running Tests

```bash
# Run all tests with coverage
uv run pytest tests/ --cov=src

# Run specific test file
uv run pytest tests/test_module.py

# Run with verbose output
uv run pytest tests/ -v
```

## Pull Request Process

1. Create a feature branch from `main`
1. Make your changes following the style guide
1. Ensure all tests pass and coverage is maintained at 99%
1. Run all code quality checks (formatting, linting, type checking)
1. Commit using [Conventional Commits](https://www.conventionalcommits.org/) format
1. Push your branch and open a pull request
1. Wait for CI checks to pass and address any feedback

### CI Requirements

All pull requests must pass:

- ✅ Tests with 99% coverage
- ✅ Linting (ruff)
- ✅ Formatting (ruff format)
- ✅ Type checking (ty check)
- ✅ Markdown formatting (mdformat)

## Questions?

If you have questions about contributing, feel free to open an issue for discussion.
