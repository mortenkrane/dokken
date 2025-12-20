#!/bin/bash
# Claude Code hook: Run full test suite at end of session
set -e

echo "🧪 Running full test suite with coverage..."
uv run pytest src/tests/ --cov=src --cov-report=term-missing

echo "✅ All tests passed!"
exit 0
