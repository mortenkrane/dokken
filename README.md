# Dokken - Documentation Drift Detection

## Why Dokken?

In the era of AI coding assistants and agents, documentation matters more than ever, just not for the reasons you might think.

Here's the paradox: your AI pair programmer can read every line of code in milliseconds, but it still needs docs to understand _why_ your system works the way it does. The architectural decisions. The boundaries between modules. The things you can't grep for. Without that context, even the best AI will suggest changes that technically work but architecturally regress your codebase.

And let's be honest: documentation has always sucked at its job. Not because developers can't write, but because docs have a shelf life measured in commits. They rot. They lie. Nobody updates them because nobody trusts them, and nobody trusts them because nobody updates them. It's the software equivalent of heat death.

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

______________________________________________________________________

**⚠️ Early Development Warning**

Dokken is in early alpha development. Expect breaking changes, rough edges, and occasional surprises. If you're using it in production, pin your versions and test thoroughly. Bug reports and feedback are welcome!

______________________________________________________________________

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
- See `DRIFT_CHECK_PROMPT` in `src/llm/prompts.py` for full criteria

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

- `Ctrl+C` - Skip question or entire questionnaire (if first question)
- `Meta+Enter` or `Esc+Enter` - Submit answer (supports multiline)
- Leave blank - Skip if no relevant information

## Configuration

**Quick reference:** See [examples/.dokken.toml](examples/.dokken.toml) for a comprehensive configuration example with all available options.

### API Keys (Environment Variables)

```bash
# Choose one provider
export ANTHROPIC_API_KEY="sk-ant-..."  # Claude (Haiku) - Recommended
export OPENAI_API_KEY="sk-..."         # OpenAI (GPT-4o-mini)
export GOOGLE_API_KEY="AIza..."        # Google (Gemini Flash)
```

### Configuration Options

Create a `.dokken.toml` file at your repository root to configure Dokken. Available options:

**Multi-Module Projects:**

```toml
modules = ["src/auth", "src/api", "src/database"]
```

```bash
dokken check --all              # Check all configured modules
dokken check --all --fix        # Check and auto-fix drift
```

**File Types:**

```toml
file_types = [".py"]           # Python (default)
# file_types = [".js", ".ts"]  # JavaScript/TypeScript
# file_types = [".py", ".js"]  # Multiple languages
```

**Exclusions:**

```toml
[exclusions]
files = ["__init__.py", "*_test.py", "conftest.py"]
```

**Custom Prompts:**

```toml
[custom_prompts]
global_prompt = "Use British spelling and active voice."
module_readme = "Focus on architectural patterns."
```

**Drift Detection Cache:**

```toml
[cache]
file = ".dokken-cache.json"  # Default location
max_size = 100               # Max entries (default)
```

Cache automatically saves drift detection results to avoid redundant LLM API calls (80-95% token reduction in CI). Add `.dokken-cache.json` to `.gitignore`.

**See [examples/.dokken.toml](examples/.dokken.toml) for complete configuration details and all available options.**

## CI/CD Integration

Use `dokken check --all` in CI pipelines to enforce documentation hygiene:

- Exit code 0: Documentation is up-to-date
- Exit code 1: Drift detected (fails the build)

**Minimal GitHub Actions workflow:**

```yaml
- name: Check documentation drift
  run: dokken check --all
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

**With caching (recommended):**

```yaml
- name: Restore drift cache
  uses: actions/cache@v4
  with:
    path: .dokken-cache.json
    key: dokken-drift-${{ hashFiles('src/**/*.py', '.dokken.toml') }}
    restore-keys: dokken-drift-

- name: Check documentation drift
  run: dokken check --all
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

Caching reduces LLM token consumption by 80-95% for unchanged code.

**See [examples/dokken-drift-check.yml](examples/dokken-drift-check.yml) for a complete workflow with setup instructions, auto-fix options, and multi-platform support.**

## Features

- **Three Documentation Types**: Module READMEs, project READMEs, and style guides
- **Configurable Depth**: Control code analysis depth (0=root only, -1=infinite recursion)
- **Drift Detection**: Criteria-based detection (see `src/llm/prompts.py`)
- **Multi-Module Check**: Check all modules with `--all` flag
- **Custom Prompts**: Inject preferences into generation (see Configuration)
- **Exclusion Rules**: Filter files via `.dokken.toml`
- **Multi-Provider LLM**: Claude (Haiku), OpenAI (GPT-4o-mini), Google (Gemini Flash)
- **Cost-Optimized**: Fast, budget-friendly models
- **Human-in-the-Loop**: Interactive questionnaire for context AI can't infer
- **Deterministic**: Temperature=0.0 for reproducible output

## Development

**Dev setup:**

```bash
# Using mise tasks (recommended)
mise run dev                  # Set up development environment
mise run check                # Run all checks (format, lint, type, test)
mise run test                 # Run tests with coverage
mise run fix                  # Auto-fix formatting and linting
mise tasks                    # List all available tasks

# Or using uv directly
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
A: Adjust criteria in `DRIFT_CHECK_PROMPT` in `src/llm/prompts.py`

**Q: How to skip questionnaire?**
A: Press `Ctrl+C` on first question

**Q: Configuration questions (exclusions, custom prompts, multi-module setup)?**
A: See [examples/.dokken.toml](examples/.dokken.toml) for comprehensive configuration examples

## License

MIT License - see [LICENSE](LICENSE)
