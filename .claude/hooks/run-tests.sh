#!/bin/bash
# Claude Code hook: Run full test suite at end of session
set -e

echo "🧪 Running full test suite with coverage..."
make test

echo "✅ All tests passed!"
exit 0
