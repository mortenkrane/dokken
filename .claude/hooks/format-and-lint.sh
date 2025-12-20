#!/bin/bash
# Claude Code hook: Format and lint changed files
set -e

# Only process changed files (passed via $CLAUDE_FILE_PATHS)
if [ -z "$CLAUDE_FILE_PATHS" ]; then
  echo "No files changed, skipping code quality checks"
  exit 0
fi

echo "🔍 Running code quality checks on changed files..."

# Separate Python and Markdown files
python_files=""
markdown_files=""

for file in $CLAUDE_FILE_PATHS; do
  if [[ "$file" == *.py ]]; then
    python_files="$python_files $file"
  elif [[ "$file" == *.md ]]; then
    markdown_files="$markdown_files $file"
  fi
done

# Format and lint Python files
if [ -n "$python_files" ]; then
  echo "  📝 Formatting Python files: $python_files"
  uv run ruff format $python_files

  echo "  🔧 Linting Python files: $python_files"
  uv run ruff check --fix $python_files

  echo "  🔬 Type checking..."
  uvx ty check
fi

# Format markdown files
if [ -n "$markdown_files" ]; then
  echo "  📄 Formatting markdown files: $markdown_files"
  uvx --with mdformat-gfm --with mdformat-tables mdformat $markdown_files
fi

echo "✅ Code quality checks passed!"
exit 0
