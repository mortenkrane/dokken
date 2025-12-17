# Dokken

AI-powered documentation generation and drift detection tool that keeps your codebase documentation synchronized with source code changes.

## Features

- **Drift Detection**: Automatically detect when documentation is out of sync with code
- **Multi-Provider LLM Support**: Use Claude, OpenAI, or Google Gemini for documentation generation
- **Cost-Optimized**: Uses fast, budget-friendly models (Haiku, GPT-4o-mini, Gemini Flash)
- **CI/CD Ready**: Exit codes designed for pipeline integration

## Installation

### Prerequisites

- [mise](https://mise.jdx.dev/getting-started.html) - Version manager
- API key for one of the supported LLM providers:
  - **Claude** (Anthropic) - Recommended for best quality
  - **OpenAI** (GPT models)
  - **Google Gemini**

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

6. **Set up your API key**

   Choose one of the following providers (checked in priority order):

   **Option 1: Claude (Anthropic)** - Fastest and most cost-effective
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-api03-..."
   ```

   **Option 2: OpenAI**
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

   **Option 3: Google Gemini**
   ```bash
   export GOOGLE_API_KEY="AIza..."
   ```

   Or add to `.env` file:
   ```bash
   echo "ANTHROPIC_API_KEY=your-api-key-here" > .env
   ```

   **Note**: If multiple API keys are set, the system uses Claude > OpenAI > Google Gemini in that order.

## LLM Providers

Dokken supports three LLM providers, automatically selecting the first available API key:

| Provider | Model | Priority | Best For |
|----------|-------|----------|----------|
| **Claude (Anthropic)** | claude-3-5-haiku-20241022 | 1st | Fast, cost-effective, excellent structured output |
| **OpenAI** | gpt-4o-mini | 2nd | Good balance of speed and quality |
| **Google Gemini** | gemini-2.5-flash | 3rd | Large context window, fast |

**All models use temperature=0.0 for deterministic, reproducible documentation.**

### Why These Models?

These budget-friendly models are specifically chosen for:
- **Speed**: Fast response times for frequent CI/CD runs
- **Cost**: Significantly cheaper than flagship models
- **Quality**: More than capable for structured documentation tasks
- **Consistency**: Reliable with Pydantic-validated outputs

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
- Analyze your code and detect drift
- Generate updated documentation
- Write to `README.md` in the module directory

### Excluding Files and Symbols from Documentation

You can configure Dokken to permanently exclude certain files or code symbols from documentation using `.dokken.toml` configuration files.

**Create a `.dokken.toml` file in:**
- Repository root (for global exclusions)
- Module directory (for module-specific exclusions)

**Example configuration:**

```toml
[exclusions]
# Exclude entire files (supports glob patterns)
files = [
    "__init__.py",
    "*_test.py",
    "conftest.py"
]

# Exclude specific symbols (functions/classes)
# Supports wildcards
symbols = [
    "_private_*",       # All private functions
    "setup_*",          # All setup functions
    "Temporary*"        # All temporary classes
]
```

**Common use cases:**
- Hide test utilities and fixtures from module documentation
- Exclude internal implementation details (e.g., `_private_*` functions)
- Skip boilerplate files like `__init__.py`
- Filter out experimental or temporary code

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
