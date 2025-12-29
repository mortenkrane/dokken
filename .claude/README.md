# Claude Code Configuration

This directory contains Claude Code configuration including hooks, slash commands, and agents for automated code quality and reviews.

## Hook Scripts

### `format-and-lint.sh` (PostToolUse)

Runs after file Write/Edit operations on **changed files only**:

- `ruff format` - Format Python files
- `ruff check --fix` - Lint and auto-fix Python files
- `mdformat` - Format markdown files (with GFM and tables plugins)
- `ty check` - Type checking

### `run-tests.sh` (SessionEnd)

Runs once at the end of the Claude Code session:

- `pytest` - Full test suite with coverage

## Configuration

Hooks are configured in `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/format-and-lint.sh"
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/run-tests.sh"
          }
        ]
      }
    ]
  }
}
```

## Environment Variables

Available in hook scripts:

- `$CLAUDE_FILE_PATHS` - Space-separated list of files changed by the tool
- `$CLAUDE_PROJECT_DIR` - Absolute path to project root

## How It Works

1. **When Claude Code edits a file**: The `PostToolUse` hook runs `format-and-lint.sh` on the changed file(s)
1. **When session ends**: The `SessionEnd` hook runs the full test suite

This ensures code quality without manual intervention while keeping the workflow fast by only checking changed files.

## Code Review Agent

Comprehensive code review agent that evaluates changes against Dokken project standards.

### Slash Command: `/review`

Manually invoke a code review:

```bash
/review
# → Reviews all pending changes on current branch
# → Provides comprehensive analysis against checklist
# → Returns structured feedback with 🔴🟡🟢✨ priorities

/review src/llm.py
# → Focuses analysis on the single file
# → Checks code quality, testing, documentation
# → References line numbers for specific issues

/review src/workflows.py src/llm.py
# → Reviews multiple files
# → Cross-checks for consistency and patterns
# → Identifies duplication between files
```

### Subagent: Code Review Agent

The code review agent can be automatically invoked by Claude when doing code reviews.

**Review Criteria:**
- Separation of Concerns
- KISS (Keep It Simple, Stupid)
- DRY (Don't Repeat Yourself)
- Readability
- Testability & Test Quality (≥99% coverage)
- Documentation

**Configuration Files:**
- `commands/review.md` - Slash command definition
- `agents/code-review.json` - Subagent configuration
- `code-review-agent.md` - Complete review specification

**Feedback Format:**
- 🔴 Critical Issues (MUST fix before merge)
- 🟡 Important Suggestions (SHOULD address)
- 🟢 Minor Improvements (nice-to-have)
- ✨ Positive Feedback (things done well)

## Related

- Pre-commit hooks: `.pre-commit-config.yaml` (for manual git commits)
- CI checks: `.github/workflows/ci.yml` (for pull requests)
- Code quality docs: `CLAUDE.md`
