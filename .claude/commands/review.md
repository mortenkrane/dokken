---
name: Code Review
description: Perform a comprehensive code review against Dokken project standards
---

You are an expert code reviewer for the Dokken project. Review the provided code or pending changes using the comprehensive checklist and principles defined in `.claude/code-review-agent.md`.

## Instructions

1. **Load the specification**: Read `.claude/code-review-agent.md` - this contains the complete review criteria, checklist, and examples
2. **Determine scope**: Review current branch changes (use git diff), or specific files if provided in $ARGUMENTS
3. **Apply the checklist systematically**:
   - Architecture & Design (separation of concerns, module boundaries)
   - Code Quality (KISS, DRY, readability)
   - Code Standards (type hints, formatting, patterns)
   - Testing & Testability (coverage, test quality, mocking)
   - Documentation
   - Error Handling
   - Performance & Security
   - Git & Versioning (Conventional Commits)
4. **Provide structured feedback** using this format:

```markdown
## Summary
[Brief overview of the review]

## Critical Issues 🔴
[Issues that MUST be fixed before merging]

## Important Suggestions 🟡
[Issues that SHOULD be addressed]

## Minor Improvements 🟢
[Nice-to-have improvements]

## Positive Feedback ✨
[Things done well]
```

## Reference Files

- `.claude/code-review-agent.md` - Complete review specification
- `docs/style-guide.md` - Dokken style guide
- `CLAUDE.md` - Project overview

## Usage Examples

- `/review` - Review all pending changes on current branch
- `/review src/llm.py` - Review specific file(s)
- `/review src/workflows.py src/prompts.py` - Review multiple files
