# Dokken - Architectural Drift Detection

## Why Dokken?

**Dokken prevents architectural drift by enforcing your architecture decisions.**

In the era of AI coding assistants and agents, your codebase faces a new threat: technically correct changes that architecturally regress your system. Your AI pair programmer can read every line of code in milliseconds, but without understanding _why_ your system works the way it does—the architectural decisions, module boundaries, and design constraints—even the best AI will suggest changes that break your carefully considered architecture.

**Here's the problem:** Code can tell you WHAT exists (functions, classes, imports), but it can't tell you WHY it exists that way. Why does the auth module handle sessions but not password resets? Why is the API layer thin? Why do we avoid circular dependencies between specific modules? These decisions live in your head, in old Slack threads, in PRs from six months ago. Your AI agent has no access to this context.

**Dokken solves this with human intent capture.** When you run `dokken generate`, it asks you targeted questions about your architectural decisions:

- What problems does this module solve?
- What are its core responsibilities?
- What are its boundaries with other modules?
- What architectural constraints must be respected?

Your answers become the baseline. Now when code changes, Dokken's drift detection doesn't just check if the code changed—it checks if the code _violates your documented architectural intent_. New function in the wrong module? That's not just drift, that's a boundary violation. API getting fat? That contradicts your documented thin-layer decision. Someone added the circular dependency you explicitly avoided? Build fails.

**Dokken catches these regressions in CI.** The combination of human intent and automated detection is what makes it work.

Here's the workflow:

1. **Bootstrap**: Run `dokken generate` and answer questions about your architectural decisions—the interactive questionnaire captures the "why" that code can't express, creating a baseline of your intent
1. **Enforce**: Add `dokken check --all` to your CI pipeline—either fail PRs on drift (strict enforcement) or run on a schedule to auto-create fix PRs (cost-efficient for frequently changing repos)
1. **Protect**: Your architecture stays consistent, and docs stay synchronized with your documented intent

**The power is in capturing human intent.** Documentation has always failed because it rots. Dokken inverts this: instead of docs getting out of sync with code, your CI pipeline prevents code from getting out of sync with your architectural decisions. You document your architecture once—including the reasoning that only you know—and Dokken makes sure every change respects it.

**What makes Dokken's drift detection work:**

- **Human intent capture**: Interactive questionnaires capture the "why" behind your architecture—decisions, constraints, and reasoning that code can't express
- **Intent-based drift detection**: Detects when code violates your documented architectural decisions, not just when it changes (new functions in wrong modules, boundary violations, constraint violations)
- **AI-readable documentation**: Generates search-optimized docs structured for both humans and AI agents to understand your architecture
- **Flexible CI/CD integration**: Fail PRs on drift (strict enforcement), or scheduled auto-fix PRs (cost-efficient for frequently changing repos)
- **Preserves manual sections**: You control the intro and custom content, Dokken manages the technical details
- **Intelligent caching**: 80-95% token reduction for unchanged code (minimal API costs)

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

**Human Intent Questions**: The interactive questionnaire during `dokken generate` is where the magic happens—it captures the architecture decisions that code can't express. This is what makes Dokken's drift detection meaningful: instead of just detecting code changes, it detects violations of your documented architectural intent.

Questions vary by doc type:

- **Module**: Problems solved, core responsibilities, boundaries with other modules, system context, architectural constraints
- **Project**: Project type, target audience, key problem being solved, setup notes, architectural overview
- **Style Guide**: Unique conventions, code organization principles, patterns to follow/avoid, team decisions

**Why this matters:** Your answers to "What problems does this module solve?" or "What are its boundaries with other modules?" become the baseline for drift detection. When someone adds a function that crosses those boundaries or solves a problem that belongs elsewhere, Dokken catches it. The AI can analyze code structure, but only you can provide the architectural reasoning.

## Interactive Questionnaire

The questionnaire shows a preview of all questions before starting, displays questions on separate lines for readability, and supports multiline answers (press `Enter` for new lines).

**Example questions for a module:**

- What specific problems does this module solve?
- What are the core responsibilities of this module?
- What are the boundaries between this module and others?
- Are there any architectural constraints or design decisions that must be maintained?

Your answers are preserved in the generated documentation and become the reference point for detecting drift.

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

Dokken can live in your CI pipeline in two ways:

### Pattern 1: PR Validation (Strict Enforcement)

**Fail the build if drift detected.** This prevents any PR from merging if it violates your documented architecture.

```yaml
# .github/workflows/pr-check.yml
- name: Check documentation drift
  run: dokken check --all
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

**Exit codes:**

- Exit code 0: Code respects documented architecture
- Exit code 1: Drift detected (fails the build to prevent architectural regression)

**Best for:** Teams with stable architectures, strict architectural governance, or when architectural changes should be explicit and reviewed.

### Pattern 2: Scheduled Drift Detection (Cost-Efficient)

**Run on a cron schedule to detect drift and automatically create PRs that update docs.** This is more cost-efficient for repos that change frequently, as it batches drift checks instead of running on every PR.

```yaml
# .github/workflows/drift-check.yml
on:
  schedule:
    - cron: '0 9 * * 1'  # Monday 9am

jobs:
  drift-check:
    steps:
      - name: Check and fix drift
        run: dokken check --all --fix

      - name: Create PR if changes
        if: git diff --quiet
        run: |
          git config user.name "dokken-bot"
          git config user.email "bot@example.com"
          git checkout -b dokken/drift-fix-$(date +%s)
          git add .
          git commit -m "docs: update documentation to reflect code changes"
          git push origin HEAD
          gh pr create --title "Update docs to match code changes" \
                       --body "Automated drift detection found changes"
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Best for:** Rapidly changing codebases, large teams with frequent commits, or when you want to reduce LLM API costs by batching checks.

### Caching (Recommended for Both Patterns)

Add caching to reduce LLM token consumption by 80-95% for unchanged code:

```yaml
- name: Restore drift cache
  uses: actions/cache@v4
  with:
    path: .dokken-cache.json
    key: dokken-drift-${{ hashFiles('src/**/*.py', '.dokken.toml') }}
    restore-keys: dokken-drift-
```

**See [examples/dokken-drift-check.yml](examples/dokken-drift-check.yml) for complete workflows with setup instructions and multi-platform support.**

## Features

- **Human Intent Capture**: Interactive questionnaire captures the "why" behind your architecture—decisions, boundaries, constraints that code can't express (this is what makes drift detection meaningful)
- **Intent-Based Drift Detection**: Detects when code violates your documented architectural intent, not just when it changes (criteria-based detection prevents regression)
- **CI/CD Integration**: Exit code 1 if drift detected, with flexible deployment patterns (strict PR validation or scheduled auto-fix)
- **Intelligent Caching**: 80-95% token reduction for unchanged code (minimal API costs)
- **Multi-Module Check**: Check all modules with `--all` flag
- **Three Documentation Types**: Bootstrap with module READMEs, project READMEs, or style guides
- **AI-Readable Output**: Search-optimized documentation structured for both humans and AI agents
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
