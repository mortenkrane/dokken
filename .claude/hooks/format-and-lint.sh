#!/bin/bash
# Claude Code hook: Format and lint all files
set -e

# Only process if files were changed (passed via $CLAUDE_FILE_PATHS)
if [ -z "$CLAUDE_FILE_PATHS" ]; then
  echo "No files changed, skipping code quality checks"
  exit 0
fi

echo "🔍 Running code quality checks..."

# Run format, lint-fix, mdformat, and typecheck
make fix typecheck

echo "✅ Code quality checks passed!"
exit 0
