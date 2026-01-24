# Dokken - Architectural Drift Detection

## Why Dokken?

**Dokken prevents architectural drift by enforcing your architecture decisions.**

In the era of AI coding assistants and agents, your codebase faces a new threat: technically correct changes that architecturally regress your system. Your AI pair programmer can read every line of code in milliseconds, but without understanding _why_ your system works the way it does—the architectural decisions, module boundaries, and design constraints—even the best AI will suggest changes that break your carefully considered architecture.

**Dokken catches these regressions before they merge.** Run `dokken check --all` in your CI pipeline, and it will fail the build if code changes violate your documented architecture. New function in the wrong module? Drift detected. Breaking a module boundary? Build fails. Changed a core design decision without updating docs? You'll know immediately.

Here's the workflow:

1. **Bootstrap**: Run `dokken generate` to capture your architecture decisions through an interactive questionnaire and generate baseline documentation
1. **Enforce**: Add `dokken check --all` to your CI pipeline
1. **Protect**: Every PR gets validated against your architectural decisions—if code drifts from the documented architecture, the build fails

**The power is in the enforcement.** Documentation has always failed because it rots. Dokken inverts this: instead of docs getting out of sync with code, your CI pipeline prevents code from getting out of sync with your architectural decisions. You document your architecture once, and Dokken makes sure every change respects it.

**What makes Dokken's drift detection work:**

- Detects architectural drift automatically (new functions, changed signatures, module boundary violations)
- Captures human intent through interactive questionnaires (the "why" that code can't express)
- Generates search-optimized docs (structured for both humans and AI agents)
- Works in CI/CD pipelines (exit code 1 if drift detected)
- Preserves manually written sections (you control the intro, Dokken manages the technical details)
- Intelligent caching (80-95% token reduction, minimal API costs)

**The workflow in practice:**

```bash
# 1. Bootstrap - capture your architecture decisions
dokken generate src/auth
dokken generate src/api

# 2. Enforce - add to CI (GitHub Actions, etc.)
dokken check --all  # Fails build if drift detected

# 3. Maintain - regenerate when architecture intentionally changes
dokken check --all --fix  # Update docs to match new architecture
```

**The result?** Architecture decisions that stick. PRs that respect your design constraints. A codebase that doesn't regress when you're not looking.

______________________________________________________________________

**⚠️ Early Development Warning**

Dokken is in early alpha development. Expect breaking changes, rough edges, and occasional surprises. If you're using it in production, pin your versions and test thoroughly. Bug reports and feedback are welcome!

______________________________________________________________________

## Quick Start

**First time setup (bootstrap your architecture docs):**

```bash
# Generate module documentation (captures architecture decisions)
dokken generate src/module_name

# Or generate for all modules in .dokken.toml
dokken generate src/auth
dokken generate src/api
dokken generate src/database
```

**Drift detection (run in CI to enforce architecture):**

```bash
# Check for drift in a module
dokken check src/module_name

# Check all modules configured in .dokken.toml
dokken check --all

# Check and auto-fix drift (updates docs to match code)
dokken check --all --fix
```

**Other documentation types:**

```bash
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

**Drift Detection**: Dokken's primary purpose is catching when code changes violate your documented architecture. Drift is detected when:

- New/removed functions or classes (did a module grow beyond its boundaries?)
- Changed function signatures (breaking a documented API contract?)
- Modified exports (changing module interfaces?)
- Major architectural changes (violating design decisions?)
- See `DRIFT_CHECK_PROMPT` in `src/llm/prompts.py` for full criteria

**Module**: Python package or directory. The unit of architecture you document and protect from drift.

**Documentation Types**: Dokken generates three types of architecture documentation:

- **module-readme**: Architectural decisions for a specific module (depth=0 by default)
- **project-readme**: Top-level project architecture (depth=1, analyzes entire repo)
- **style-guide**: Code conventions and patterns (depth=-1, full recursion)

**Human Intent Questions**: The interactive questionnaire during `dokken generate` captures the architecture decisions that code can't express (questions vary by doc type):

- **Module**: Problems solved, core responsibilities, boundaries, system context
- **Project**: Project type, target audience, key problem, setup notes
- **Style Guide**: Unique conventions, organization, patterns to follow/avoid

## Interactive Questionnaire

The questionnaire shows a preview of all questions before starting, displays questions on separate lines for readability, and supports multiline answers (press `Enter` for new lines).

**Keyboard shortcuts:**

- `Ctrl+C` - Skip question or entire questionnaire (at preview or first question)
- `Esc+Enter` or `Ctrl+D` - Submit answer (most reliable across terminals)
- `Meta+Enter` - Submit answer (may work depending on your terminal)
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

Use `dokken check --all` in CI pipelines to enforce your architecture decisions:

- Exit code 0: Code respects documented architecture
- Exit code 1: Drift detected (fails the build to prevent architectural regression)

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

- **Drift Detection**: Criteria-based detection prevents architectural regression (see `src/llm/prompts.py`)
- **CI/CD Integration**: Exit code 1 if drift detected, failing builds that violate architecture
- **Intelligent Caching**: 80-95% token reduction for unchanged code (minimal API costs)
- **Multi-Module Check**: Check all modules with `--all` flag
- **Architecture Documentation**: Bootstrap with three doc types (module READMEs, project READMEs, style guides)
- **Human-in-the-Loop**: Interactive questionnaire captures architecture decisions code can't express
- **Configurable Depth**: Control code analysis depth (0=root only, -1=infinite recursion)
- **Custom Prompts**: Inject preferences into generation (see Configuration)
- **Exclusion Rules**: Filter files via `.dokken.toml`
- **Multi-Provider LLM**: Claude (Haiku), OpenAI (GPT-4o-mini), Google (Gemini Flash)
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
A: Press `Ctrl+C` during the question preview or on the first question

**Q: Configuration questions (exclusions, custom prompts, multi-module setup)?**
A: See [examples/.dokken.toml](examples/.dokken.toml) for comprehensive configuration examples

## License

MIT License - see [LICENSE](LICENSE)
