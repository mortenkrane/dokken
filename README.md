# Dokken - Documentation Drift Detection

AI-powered documentation generation and drift detection. Detects when documentation is out of sync with code changes.

## Quick Start

```bash
# Check for drift in a module
dokken check src/module_name

# Check all modules configured in .dokken.toml
dokken check --all

# Generate module documentation
dokken generate src/module_name

# Generate project README
dokken generate . --doc-type project-readme

# Generate style guide
dokken generate . --doc-type style-guide
```

## Installation

**Prerequisites:** [mise](https://mise.jdx.dev) and API key (Anthropic/OpenAI/Google)

```bash
git clone https://github.com/mortenkrane/dokken.git
cd dokken
mise install         # Python 3.13.7 + uv
uv sync --all-groups # Dependencies + dev tools

# API key (choose one)
export ANTHROPIC_API_KEY="sk-ant-..."  # Recommended
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="AIza..."
```

## Commands

### `dokken check <module>`

Detect documentation drift. Exit code 1 if drift detected (CI/CD-friendly).

**Options:**

- `--all` - Check all modules configured in `.dokken.toml`
- `--fix` - Auto-generate documentation for modules with drift
- `--doc-type <type>` - Type of documentation (module-readme, project-readme, style-guide)
- `--depth <n>` - Directory depth to traverse (0=root only, 1=root+1 level, -1=infinite)

**Examples:**

```bash
dokken check src/auth                    # Check single module
dokken check --all                       # Check all configured modules
dokken check --all --fix                 # Check and auto-fix drift
dokken check . --doc-type project-readme # Check project README
dokken check . --doc-type style-guide    # Check style guide
```

### `dokken generate <module>`

Generate or update documentation.

**Options:**

- `--doc-type <type>` - Type of documentation to generate:
  - `module-readme` (default) - Module architectural docs in `<module>/README.md`
  - `project-readme` - Project README in `README.md`
  - `style-guide` - Code conventions guide in `docs/style-guide.md`
- `--depth <n>` - Directory depth to traverse (defaults: module=0, project=1, style-guide=-1)

**Process:**

1. Analyze code (depth varies by doc type)
1. Interactive questionnaire (captures human intent)
1. Generate documentation with LLM
1. Write to appropriate location

**Examples:**

```bash
dokken generate src/auth                # Generate module docs
dokken generate . --doc-type project-readme # Generate project README
dokken generate . --doc-type style-guide    # Generate style guide
dokken generate src/auth --depth 2         # Custom depth
```

## Key Concepts

**Drift**: Documentation out of sync with code. Detected when:

- New/removed functions or classes
- Changed function signatures
- Modified exports
- Major architectural changes
- See `DRIFT_CHECK_PROMPT` in `src/prompts.py` for full criteria

**Documentation Types**: Dokken generates three types of documentation:

- **module-readme**: Architectural docs for a specific module (depth=0 by default)
- **project-readme**: Top-level project README (depth=1, analyzes entire repo)
- **style-guide**: Code conventions and patterns guide (depth=-1, full recursion)

**Module**: Python package or directory. Target for `dokken check/generate`.

**Human Intent Questions**: Interactive questionnaire during generation (questions vary by doc type):

- **Module**: Problems solved, core responsibilities, boundaries, system context
- **Project**: Project type, target audience, key problem, setup notes
- **Style Guide**: Unique conventions, organization, patterns to follow/avoid

## Interactive Questionnaire

**Keyboard shortcuts:**

- `ESC` - Skip question or entire questionnaire (if first question)
- `Enter` twice - Submit answer (supports multiline)
- Leave blank - Skip if no relevant information

## Configuration

### API Keys (Environment Variables)

```bash
# Choose one provider
export ANTHROPIC_API_KEY="sk-ant-..."  # Claude (Haiku) - Recommended
export OPENAI_API_KEY="sk-..."         # OpenAI (GPT-4o-mini)
export GOOGLE_API_KEY="AIza..."        # Google (Gemini Flash)
```

### Multi-Module Detection (`.dokken.toml`)

Configure multiple modules to check in a single command:

```toml
# List of modules (paths relative to repo root)
modules = [
    "src/auth",
    "src/api",
    "src/database"
]
```

**Usage:**

```bash
dokken check --all              # Check all configured modules
dokken check --all --fix        # Check and auto-fix drift
dokken check src/auth           # Check single module
```

**Exit behavior:**

- Exit code 1 if any module has drift (CI/CD-friendly)
- Summary report at end showing all modules

### Exclusion Patterns (`.dokken.toml`)

**File locations:**

- `/.dokken.toml` - Global exclusions and module list
- `<module>/.dokken.toml` - Module-specific exclusions

**Syntax:**

```toml
# Configure modules to check (repo root only)
modules = ["src/auth", "src/api"]

[exclusions]
# Exclude files (glob patterns supported)
files = [
    "__init__.py",
    "*_test.py",
    "conftest.py"
]

# Exclude symbols (functions/classes with wildcard support)
symbols = [
    "_private_*",    # Private functions
    "setup_*",       # Setup functions
    "Temporary*"     # Temporary classes
]
```

**Common patterns:**

- Test files: `"*_test.py"`, `"test_*.py"`
- Private code: `"_private_*"`, `"_internal_*"`
- Boilerplate: `"__init__.py"`, `"conftest.py"`
- Experimental: `"experimental_*"`, `"Temp*"`

### Custom Prompts (`.dokken.toml`)

Inject preferences and instructions into documentation generation:

**Available prompt types:**

- `global_prompt` - Applied to all documentation types
- `module_readme` - Module-level docs (`<module>/README.md`)
- `project_readme` - Project README (`README.md`)
- `style_guide` - Style guide (`docs/style-guide.md`)

**Example:**

```toml
[custom_prompts]
global_prompt = """
Use British spelling.
Prefer active voice and present tense.
Keep sentences concise.
"""

module_readme = "Focus on architectural patterns and design decisions."
project_readme = "Include quick-start guide and highlight key features."
style_guide = "Reference specific files as examples."
```

**How it works:**

- Custom prompts appended to LLM generation under "USER PREFERENCES"
- Module-level configs extend/override repository-level configs
- Max 5,000 characters per prompt field

**Common use cases:**

- Enforce writing style/tone (British spelling, active voice)
- Request specific sections (mermaid diagrams, examples)
- Emphasize aspects (security, performance)
- Align with company style guides

## CI/CD Integration

**Exit codes:**

- `dokken check`: Exit 1 if drift detected, 0 if synchronized
- Use in pipelines to enforce documentation hygiene

**Example GitHub Actions:**

```yaml
# Single module
- name: Check documentation drift
  run: dokken check src/my_module

# All configured modules
- name: Check all modules for drift
  run: dokken check --all
```

## Features

- **Three Documentation Types**: Module READMEs, project READMEs, and style guides
- **Configurable Depth**: Control code analysis depth (0=root only, -1=infinite recursion)
- **Drift Detection**: Criteria-based detection (see `src/prompts.py`)
- **Multi-Module Check**: Check all modules with `--all` flag
- **Custom Prompts**: Inject preferences into generation (see Configuration)
- **Exclusion Rules**: Filter files and symbols via `.dokken.toml`
- **Multi-Provider LLM**: Claude (Haiku), OpenAI (GPT-4o-mini), Google (Gemini Flash)
- **Cost-Optimized**: Fast, budget-friendly models
- **Human-in-the-Loop**: Interactive questionnaire for context AI can't infer
- **Deterministic**: Temperature=0.0 for reproducible output

## Development

**Dev setup:**

```bash
uv sync --all-groups          # Install dependencies + dev tools
uv run pytest tests/ --cov=src  # Run tests with coverage
uv run ruff format            # Format code
uv run ruff check --fix       # Lint and auto-fix
uvx ty check                  # Type checking
```

**Full documentation:**

- [docs/style-guide.md](docs/style-guide.md) - Architecture, code style, testing, git workflow
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines

## Troubleshooting

**Q: `ModuleNotFoundError` when running dokken**
A: Run `uv sync --all-groups` to install dependencies

**Q: Drift detection too sensitive**
A: Adjust criteria in `DRIFT_CHECK_PROMPT` in `src/prompts.py`

**Q: How to skip questionnaire?**
A: Press `ESC` on first question

**Q: Change base branch for drift detection?**
A: Set `GIT_BASE_BRANCH` in `src/git.py`

**Q: Exclude test files from documentation?**
A: Add pattern to `.dokken.toml`:

```toml
[exclusions]
files = ["*_test.py", "test_*.py"]
```

**Q: How to use custom prompts?**
A: Add to `.dokken.toml`:

```toml
[custom_prompts]
global_prompt = "Use British spelling throughout."
```

**Q: How to check multiple modules at once?**
A: Configure modules in `.dokken.toml` and run `dokken check --all`

## License

MIT License - see [LICENSE](LICENSE)
