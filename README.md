# Dokken

AI-powered documentation generation and drift detection tool that keeps your codebase documentation synchronized with source code changes.

## Features

- **Drift Detection**: Automatically detect when documentation is out of sync with code
- **Smart Generation**: Generate comprehensive documentation using Google's Gemini LLM
- **Git Integration**: Automatic branch creation and management for documentation updates
- **CI/CD Ready**: Exit codes designed for pipeline integration

## Installation

### Prerequisites

- [mise](https://mise.jdx.dev/getting-started.html) - Version manager
- Google API key for Gemini access

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/dokken.git
   cd dokken
   ```

2. **Install mise** (if not already installed)
   ```bash
   # macOS
   brew install mise

   # Linux/WSL
   curl https://mise.run | sh
   ```

3. **Activate mise in your shell**

   Add to your `~/.zshrc` or `~/.bashrc`:
   ```bash
   eval "$(mise activate zsh)"  # or bash/fish
   ```

   Then reload your shell:
   ```bash
   source ~/.zshrc  # or ~/.bashrc
   ```

4. **Install Python and uv**
   ```bash
   mise install
   ```

   mise will automatically:
   - Install Python 3.13.7 and uv 0.9.18
   - Create and activate the `.venv` virtual environment

5. **Install dependencies**
   ```bash
   uv sync
   ```

6. **Set up your Google API key**
   ```bash
   export GOOGLE_API_KEY="your-api-key-here"
   ```

   Or add to `.env` file:
   ```bash
   echo "GOOGLE_API_KEY=your-api-key-here" > .env
   ```

## Usage

### Check for Documentation Drift

Detect if documentation is out of sync with code (useful in CI/CD):

```bash
dokken check src/module_name
```

Exit code 1 indicates drift detected, 0 means documentation is current.

### Generate Documentation

Generate or update documentation with automatic git branching:

```bash
dokken generate src/module_name
```

This will:
- Create a new branch `dokken/docs-YYYY-MM-DD`
- Analyze your code and detect drift
- Generate updated documentation
- Write to `README.md` in the module directory

## Development

### Running Tests

```bash
# Run all tests
pytest src/tests/

# Run with coverage (99% minimum required)
pytest src/tests/ --cov=src --cov-report=term-missing
```

**Coverage Requirements:**
- Minimum test coverage: **99%** (enforced in CI)
- Tests will fail if coverage drops below this threshold
- Current coverage target aligns with production quality standards

### Code Quality

```bash
# Format code
ruff format

# Lint
ruff check --fix

# Type checking (using ty)
uvx ty check
```

### Continuous Integration

The project uses GitHub Actions for automated quality checks on all pull requests and pushes to main:

**Automated Checks:**
- **Tests**: Full test suite with 99% coverage requirement
- **Formatting**: Ruff format validation
- **Linting**: Ruff linting rules (see `pyproject.toml`)
- **Type Checking**: Static type analysis using `ty`

All checks run in parallel for fast feedback. CI must pass before merging.

## Documentation

See [CLAUDE.md](CLAUDE.md) for detailed architecture, code style, and testing guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please ensure:
- All tests pass with **99% minimum coverage**
- Code follows the style guide in `docs/style-guide.md`
- Function-based tests with proper mocking
- All CI checks pass (formatting, linting, type checking)
