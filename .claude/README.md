# Claude Code Hooks

This directory contains Claude Code hooks that automatically run code quality checks and tests during AI coding sessions.

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

## Related

- Pre-commit hooks: `.pre-commit-config.yaml` (for manual git commits)
- CI checks: `.github/workflows/ci.yml` (for pull requests)
- Code quality docs: `CLAUDE.md`
