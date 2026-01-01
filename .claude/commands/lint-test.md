---
name: Lint and Test
description: Run all linters, formatters, type checks, and tests with detailed output
---

Run all code quality checks and tests for the Dokken project. This command executes:

1. **Ruff Format** - Auto-format all Python code
2. **Ruff Check** - Lint Python code with auto-fix enabled
3. **Type Checking** - Run ty type checker
4. **Markdown Format** - Format all markdown files
5. **Tests** - Run pytest with coverage

## Instructions

Execute the following commands in sequence and report the results:

```bash
# Run formatters and linters with auto-fix
uv run ruff format
uv run ruff check --fix
uvx mdformat *.md docs/ src/

# Run type checking
uvx ty check

# Run tests with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing
```

## Output Format

For each step:
- ✅ Report if it passed
- ❌ Report failures with full error details
- Show relevant output, especially for failing tests or type errors

## Summary

At the end, provide a summary:
- Total checks run
- Which checks passed
- Which checks failed (with details)
- Overall status (PASS/FAIL)

## Example Output Structure

```markdown
## Code Quality Check Results

### 1. Ruff Format
✅ PASSED - All files formatted

### 2. Ruff Check (with --fix)
✅ PASSED - No linting issues found

### 3. Markdown Format
✅ PASSED - All markdown files formatted

### 4. Type Checking
❌ FAILED
- src/example.py:42: error: Incompatible types...

### 5. Tests
❌ FAILED
- test_example.py::test_foo - AssertionError...
Coverage: 85%

## Summary
- Passed: 3/5
- Failed: 2/5 (Type checking, Tests)
- Overall: FAIL
```
