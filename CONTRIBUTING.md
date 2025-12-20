# Contributing to Dokken

Thank you for your interest in contributing to Dokken! We welcome contributions of all kinds.

## Getting Started

1. Fork the repository and clone your fork
2. Install dependencies: `mise install && uv sync`
3. Set up pre-commit hooks (optional but recommended):
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
ruff format && ruff check --fix

# Type checking
uvx ty check

# Format markdown
uvx mdformat *.md docs/ src/

# Run tests with coverage
pytest src/tests/ --cov=src --cov-report=term-missing
```

### Running Tests

```bash
# Run all tests with coverage
pytest src/tests/ --cov=src

# Run specific test file
pytest src/tests/test_module.py

# Run with verbose output
pytest src/tests/ -v
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes following the style guide
3. Ensure all tests pass and coverage is maintained at 99%
4. Run all code quality checks (formatting, linting, type checking)
5. Commit using [Conventional Commits](https://www.conventionalcommits.org/) format
6. Push your branch and open a pull request
7. Wait for CI checks to pass and address any feedback

### CI Requirements

All pull requests must pass:
- ✅ Tests with 99% coverage
- ✅ Linting (ruff)
- ✅ Formatting (ruff format)
- ✅ Type checking (ty check)
- ✅ Markdown formatting (mdformat)

## Questions?

If you have questions about contributing, feel free to open an issue for discussion.
