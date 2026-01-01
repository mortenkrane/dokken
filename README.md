# Dokken - Documentation Drift Detection

## Why Dokken?

In the era of AI coding assistants and agents, documentation matters more than ever—just not for the reasons you might think.

Here's the paradox: your AI pair programmer can read every line of code in milliseconds, but it still needs docs to understand _why_ your system works the way it does. The architectural decisions. The boundaries between modules. The things you can't grep for. Without that context, even the best AI will suggest changes that technically work but architecturally regress your codebase.

And let's be honest—documentation has always sucked at its job. Not because developers can't write, but because docs have a shelf life measured in commits. They rot. They lie. Nobody updates them because nobody trusts them, and nobody trusts them because nobody updates them. It's the software equivalent of heat death.

**Dokken breaks this cycle.** It detects when your docs drift from reality and regenerates them automatically. No more archaeological digs through git history to figure out if that README is from 2019 or 2023. No more "the code is the documentation" excuses (we both know that's a cop-out).

Here's how it works: Dokken captures the stuff code can't express through an **interactive questionnaire**, asking you about architectural decisions, design trade-offs, and why things are the way they are. Then it generates docs optimized for how both humans and AI agents actually consume them: **through grep and search**. Because let's face it, nobody reads docs cover-to-cover. We all jump straight to the section we need. Dokken's docs are structured so you (or your AI) can find what you're looking for in seconds.

And here's the best part: **Dokken preserves manually written sections.** Write an intro by hand (like this one), add custom examples, or craft specific sections yourself. Dokken will leave them untouched and only regenerate the parts it manages. You get the control of manual documentation with the freshness of automated generation.

But here's what matters: **Dokken writes documentation for humans, not just machines.** Because at the end of the day, humans are the ones who need to understand the overall system architecture to make good decisions, whether they're coding manually or instructing an AI to do it for them. Your AI assistant might be able to implement a feature, but you need to decide if that feature belongs in the auth module or the API layer. That's a human judgment call, and it requires human-level understanding.

**What Dokken does:**

- Generates documentation from scratch when you don't have any (or when you're starting fresh)
- Detects documentation drift automatically (new functions, changed signatures, architectural shifts)
- Regenerates docs that are actually useful (architectural patterns, design decisions, module boundaries)
- Works in CI/CD pipelines (exit code 1 if docs are stale)
- Captures human intent through interactive questionnaires (the "why" that code can't express)
- Generates search-optimized docs (because grep is how we all find things anyway)

**The result?** Documentation you can trust. Documentation your AI can use. Documentation that doesn't make you cringe when you read it six months later.

---

**⚠️ Early Development Warning**

Dokken is in early alpha development. Expect breaking changes, rough edges, and occasional surprises. If you're using it in production, pin your versions and test thoroughly. Bug reports and feedback are welcome!

---

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

# File types to analyze (optional, defaults to [".py"])
file_types = [".py", ".js", ".ts"]
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

### File Types (`.dokken.toml`)

Configure which file types to analyze for documentation:

```toml
# File types to analyze (optional, defaults to [".py"])
# Supports any programming language file extension
file_types = [".py"]           # Python only (default)
# file_types = [".js", ".ts"]  # JavaScript/TypeScript
# file_types = [".py", ".js"]  # Multiple languages
```

**Notes:**

- Extensions can be specified with or without leading dot (`.py` or `py`)
- Applies to all modules in the repository
- Can be overridden in module-specific `.dokken.toml` files

### Exclusion Patterns (`.dokken.toml`)

**File locations:**

- `/.dokken.toml` - Global exclusions, module list, and file types
- `<module>/.dokken.toml` - Module-specific exclusions and file types

**Syntax:**

```toml
# Configure modules to check (repo root only)
modules = ["src/auth", "src/api"]

# File types to analyze (optional, defaults to [".py"])
file_types = [".py", ".js", ".ts"]

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

**Common file exclusion patterns:**

- Test files: `"*_test.py"`, `"test_*.py"`, `"*.spec.js"`
- Private code: `"_private_*"`, `"_internal_*"`
- Boilerplate: `"__init__.py"`, `"conftest.py"`
- Experimental: `"experimental_*"`, `"Temp*"`
- Build artifacts: `"*.min.js"`, `"*.d.ts"`

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

### Cache Configuration (`.dokken.toml`)

Dokken caches drift detection results to avoid redundant LLM API calls. The cache persists across runs, making it especially useful in CI environments.

**Configuration:**

```toml
[cache]
file = ".dokken-cache.json"  # Path to cache file (default)
max_size = 100               # Max cache entries (default)
```

**How it works:**

- Cache key: SHA256 hash of code + documentation content + LLM model
- Persistent: Stored as JSON file, survives across runs
- Automatic: Loaded/saved by `dokken check` and `dokken generate`
- Thread-safe: FIFO eviction when cache reaches `max_size`

**Benefits:**

- Reduces LLM token consumption in CI (80-95% reduction for unchanged code)
- Faster drift checks on repeated runs
- Works locally and in CI/CD pipelines

**Cache location:**

- Default: `.dokken-cache.json` in repository root
- Customize via `cache.file` in `.dokken.toml`
- Add to `.gitignore` (cache is environment-specific)

## CI/CD Integration

**Exit codes:**

- `dokken check`: Exit 1 if drift detected, 0 if synchronized
- Use in pipelines to enforce documentation hygiene

**GitHub Actions Example (with caching):**

```yaml
name: Documentation Drift Check

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  dokken-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv sync --all-groups

      # Restore drift detection cache (saves LLM tokens)
      - name: Restore drift cache
        uses: actions/cache@v4
        with:
          path: .dokken-cache.json
          key: dokken-drift-${{ hashFiles('src/**/*.py', '.dokken.toml') }}
          restore-keys: |
            dokken-drift-

      # Check for drift (cache auto-loaded/saved)
      - name: Check documentation drift
        run: uv run dokken check --all
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

**Notes:**

- Cache key includes source files hash (invalidates when code changes)
- Restore-keys provide fallback (partial cache hits still beneficial)
- Cache automatically loaded/saved by dokken (no manual steps needed)
- Other CI platforms (GitLab CI, CircleCI, Azure Pipelines) have similar caching mechanisms

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
