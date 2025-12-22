# Dokken

AI-powered documentation generation and drift detection tool that keeps your codebase documentation synchronized with source code changes.

## Features

- **Drift Detection**: Automatically detect when documentation is out of sync with code
- **Multi-Provider LLM Support**: Use Claude, OpenAI, or Google Gemini for documentation generation
- **Cost-Optimized**: Uses fast, budget-friendly models (Haiku, GPT-4o-mini, Gemini Flash)
- **Human-in-the-Loop**: Interactive questionnaire to capture intent that AI cannot infer from code alone
- **CI/CD Ready**: Exit codes designed for pipeline integration

## Installation

**Prerequisites:** [mise](https://mise.jdx.dev) and an API key from Claude, OpenAI, or Google Gemini.

```bash
# Clone and install
git clone https://github.com/your-username/dokken.git
cd dokken
mise install         # Installs Python 3.13.7 and uv
uv sync --all-groups # Install all dependencies (including dev)

# Set up API key (choose one)
export ANTHROPIC_API_KEY="sk-ant-..."  # Recommended
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="AIza..."
```

## Usage

```bash
# Check for documentation drift (useful in CI/CD)
dokken check src/module_name

# Generate or update documentation
dokken generate src/module_name
```

### Generate Documentation

When you run `dokken generate`, it will:

1. Analyze your code and detect drift
1. **Prompt you with an interactive questionnaire** to capture human intent (see below)
1. Generate updated documentation using both code analysis and human input
1. Write to `README.md` in the module directory

#### Human Intent Capture

When generating documentation, Dokken will ask you questions to capture context that AI cannot infer from code alone:

- **What problems does this module solve?**
- **What are the module's core responsibilities?**
- **What is NOT this module's responsibility?**
- **How does the module fit into the larger system?**

**Tips:**

- Press `ESC` on any question to skip it
- Press `ESC` on the first question to skip the entire questionnaire
- Press `Enter` twice to submit your answer (supports multiline input)
- Leave answers blank if you don't have relevant information

Your responses help create more accurate, context-aware documentation that reflects the true intent behind your code.

### Excluding Files and Symbols

Create a `.dokken.toml` file to exclude files or symbols from documentation:

**Configuration locations:**

- Repository root: `.dokken.toml` - Global exclusions
- Module directory: `<module>/.dokken.toml` - Module-specific exclusions

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
symbols = [
    "_private_*",       # All private functions
    "setup_*",          # All setup functions
    "Temporary*"        # All temporary classes
]
```

**Common use cases:**

- Hide test utilities and fixtures
- Exclude internal implementation details (`_private_*`)
- Skip boilerplate files like `__init__.py`
- Filter experimental or temporary code

### Custom Prompts

Inject your own preferences and instructions into the documentation generation process using custom prompts in `.dokken.toml`:

**Configuration locations:**

- Repository root: `.dokken.toml` - Global custom prompts
- Module directory: `<module>/.dokken.toml` - Module-specific custom prompts

**Example configuration:**

```toml
[custom_prompts]
# Global prompt applies to all documentation types
global_prompt = """
Use British spelling throughout.
Prefer active voice and present tense.
Keep sentences concise and direct.
"""

# Doc-type-specific prompts
module_readme = "Focus on architectural patterns and design decisions."
project_readme = "Include a quick-start guide and highlight key features."
style_guide = "Reference specific files and functions as examples."
```

**Available doc types:**

- `global_prompt` - Applied to all documentation types
- `module_readme` - Module-level documentation (`docs/module-readme.md`)
- `project_readme` - Project README (`README.md`)
- `style_guide` - Style guide documentation (`docs/style-guide.md`)

**How it works:**

Custom prompts are appended to the LLM generation prompt under a "USER PREFERENCES" section. Both global and doc-type-specific prompts are included when applicable. Module-level configs extend (and can override) repository-level configs.

**Common use cases:**

- Enforce specific writing style or tone
- Request inclusion of particular sections
- Emphasize certain aspects (security, performance, etc.)
- Exclude topics you prefer not to document

## Development

See [docs/style-guide.md](docs/style-guide.md) for comprehensive architecture, code style, testing guidelines, and git workflow.

**Quick start:**

```bash
# Install dev dependencies
uv sync --all-groups

# Run tests
uv run pytest src/tests/ --cov=src

# Code quality
uv run ruff format && uv run ruff check --fix && uvx ty check
```

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on code style, testing, and the pull request process.

## License

MIT License - see [LICENSE](LICENSE) file for details
