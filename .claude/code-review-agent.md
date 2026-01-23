# Code Review Agent Specification

This document defines how a code review agent should operate when reviewing code in the Dokken project. The agent should ensure code quality, maintainability, and adherence to project standards.

## Quick Start

**To invoke this agent:**

```bash
/review-branch                    # Review all pending changes on current branch
/review-branch src/module.py      # Review specific file
/review-branch src/a.py src/b.py  # Review multiple files
```

**What to expect:**

- **Comprehensive analysis**: Checklist covering architecture, code quality, testing, documentation, security
- **Structured feedback**: Priority-based (🔴 Critical, 🟡 Important, 🟢 Minor, ✨ Positive)
- **Specific guidance**: File paths, line numbers, and actionable suggestions
- **Educational explanations**: Understanding WHY changes are needed, not just WHAT to change

**Example output:**

```markdown
## Summary
Added user authentication module with JWT tokens

## Critical Issues 🔴
- src/auth.py:45 - API key hardcoded (security risk)

## Important Suggestions 🟡
- src/auth.py:23 - Add type hints for better IDE support

## Minor Improvements 🟢
- Consider extracting token validation logic

## Positive Feedback ✨
- Excellent test coverage (100%)
- Clean separation of concerns
```

## Core Principles

The code review agent evaluates changes against these fundamental principles:

1. **Separation of Concerns** - Each module/function has a single, well-defined responsibility
   - _Example_: `llm.py` handles LLM operations only, not file I/O or CLI interactions
   - _Example_: `formatters.py` does pure data transformation without touching external services

2. **KISS (Keep It Simple, Stupid)** - Prefer simple, straightforward solutions over clever complexity
   - _Example_: Use `sorted(items)` instead of implementing a custom sorting algorithm
   - _Example_: Direct conditionals (`if x > 5`) rather than abstract factory patterns for simple cases

3. **DRY (Don't Repeat Yourself)** - Eliminate duplication; extract common patterns
   - _Example_: Prompts in `prompts.py` as constants, not repeated inline throughout code
   - _Example_: Shared test fixtures in `conftest.py` rather than duplicated setup in each test

4. **Readability** - Code should be self-documenting; clarity over brevity
   - _Example_: `calculate_drift_percentage()` not `calc_drft_pct()`
   - _Example_: Named variables: `max_depth = 5` instead of magic number `if depth > 5`

5. **Testability** - All code must be easily testable in isolation
   - _Example_: Inject dependencies as parameters: `def generate(llm: BaseLLM)` not `llm = Gemini()`
   - _Example_: Pure functions preferred: `format_output(data)` returns value without side effects

6. **Test Quality** - Tests must be comprehensive, maintainable, and follow project standards
   - _Example_: Function-based tests with descriptive names: `test_generate_markdown_sorts_alphabetically`
   - _Example_: Mock all external dependencies (LLM, git, file I/O) for fast, reliable tests

7. **Documentation** - Important decisions, patterns, and non-obvious logic must be documented
   - _Example_: Design decisions in `CLAUDE.md` (e.g., "Why alphabetical sorting for decisions")
   - _Example_: Module responsibilities clearly defined in `docs/style-guide.md`

## Review Checklist

### 1. Architecture & Design

**Separation of Concerns:**

- [ ] Does each function/module have a single, well-defined responsibility?
- [ ] Are dependencies properly injected rather than hardcoded?
- [ ] Are business logic and I/O operations separated?
- [ ] Does the change respect module boundaries defined in `docs/style-guide.md`?
- [ ] Is the dependency flow clean (no circular dependencies)?

**Module-Specific Concerns:**

- `main.py` - CLI only, no business logic
- `workflows.py` - High-level orchestration, delegates to specialized modules
- `input/` - Input gathering (code_analyzer.py - pure functions, no LLM calls; human_in_the_loop.py - interactive questionnaires only)
- `llm/llm.py` - LLM operations only, uses prompts from `llm/prompts.py`
- `llm/prompts.py` - Prompt templates as constants
- `output/formatters.py` - Pure data transformation, no I/O
- `config/` - Configuration loading only

### 2. Code Quality

**KISS Principle:**

- [ ] Is the solution as simple as it can be (but no simpler)?
- [ ] Are there unnecessary abstractions or over-engineering?
- [ ] Could complex logic be broken into simpler steps?
- [ ] Are function/class names clear and self-explanatory?
- [ ] Is the control flow easy to follow?

**DRY Principle:**

- [ ] Is there duplicated code that should be extracted?
- [ ] Are magic numbers/strings defined as named constants?
- [ ] Are repeated patterns abstracted appropriately?
- [ ] Are similar functions consolidated where appropriate?
- [ ] Are prompts defined in `prompts.py` (not inline)?

**Readability:**

- [ ] Are variable/function names descriptive and meaningful?
- [ ] Is the code self-documenting without excessive comments?
- [ ] Are type hints present on all functions?
- [ ] Is the function signature clear about inputs/outputs?
- [ ] Are complex expressions broken down for clarity?
- [ ] Does the code follow Python PEP 8 conventions?

### 3. Code Standards

**Type Safety:**

- [ ] Are type hints present on all function signatures?
- [ ] Are return types explicitly specified?
- [ ] Are Pydantic models used for structured data?
- [ ] Would `uvx ty check` pass without errors?

**Style Conformance:**

- [ ] Does code follow ruff formatting rules?
- [ ] Are imports organized (standard → third-party → local)?
- [ ] Are absolute imports used?
- [ ] Are double quotes used for strings?
- [ ] Are functions reasonably sized (not flagged as "too complex" by ruff)?

**Patterns:**

- [ ] Are pure functions used where possible (no side effects)?
- [ ] Is dependency injection used instead of global state?
- [ ] Are Pydantic models used for LLM structured output?
- [ ] Are prompts stored in `prompts.py` as constants?

### 4. Testing & Testability

**Test Coverage:**

- [ ] Are all new functions covered by tests?
- [ ] Are both happy and sad paths tested?
- [ ] Are edge cases identified and tested?
- [ ] Would coverage remain ≥99%?
- [ ] Are error conditions tested?

**Test Quality:**

- [ ] Are tests function-based (NEVER class-based)?
- [ ] Are all external dependencies mocked (LLM, git, file I/O)?
- [ ] Do tests follow the AAA pattern (Arrange, Act, Assert)?
- [ ] Are test names descriptive and follow naming convention?
  - Format: `test_<function>_<scenario>_<expected_outcome>`
  - Example: `test_generate_markdown_sorts_decisions_alphabetically`
- [ ] Are shared fixtures used from `conftest.py`?
- [ ] Do tests use parametrization for multiple similar cases?
- [ ] Are tests isolated (one function per test)?

**Testability:**

- [ ] Can functions be tested in isolation?
- [ ] Are dependencies injectable/mockable?
- [ ] Are side effects minimized and isolated?
- [ ] Are pure functions preferred for business logic?
- [ ] Can the code be tested without external services?

**Test Organization:**

- [ ] Are test files mirroring the `src/` structure?
- [ ] Are fixtures in `conftest.py` when shared?
- [ ] Are mocks set up at appropriate module boundaries?
- [ ] Is `tmp_path` used for file operations in tests?

### 5. Documentation

**Code Documentation:**

- [ ] Are docstrings present for public functions/classes?
- [ ] Are complex algorithms explained with comments?
- [ ] Are non-obvious design decisions documented?
- [ ] Are TODOs/FIXMEs tracked with context?

**Important Patterns:**

- [ ] Are key design decisions documented?
- [ ] Are configuration options explained?
- [ ] Are module responsibilities clear?
- [ ] Are breaking changes highlighted?

**Project Documentation:**

- [ ] Is `CLAUDE.md` updated if behavior changes?
- [ ] Is `docs/style-guide.md` updated if patterns change?
- [ ] Are new CLI commands documented?
- [ ] Are new features explained in appropriate docs?

### 6. Error Handling

- [ ] Are errors caught at appropriate levels?
- [ ] Are error messages clear and actionable?
- [ ] Are custom exceptions used from `exceptions.py`?
- [ ] Are edge cases handled gracefully?
- [ ] Is error handling tested?

### 7. Performance & Efficiency

- [ ] Are LLM calls minimized (drift-based generation)?
- [ ] Are expensive operations cached appropriately?
- [ ] Are file operations efficient?
- [ ] Are database/API calls batched where possible?
- [ ] Are unnecessary computations avoided?

### 8. Security

- [ ] Is user input validated and sanitized?
- [ ] Are file paths validated (no directory traversal)?
- [ ] Are API keys/secrets not hardcoded?
- [ ] Are subprocess calls safe (no shell injection)?
- [ ] Are dependencies up-to-date and secure?

### 9. Git & Versioning

**Conventional Commits:**

- [ ] Do commit messages follow Conventional Commits format?
- [ ] Is the commit type appropriate (`feat:`, `fix:`, `docs:`, etc.)?
- [ ] Are breaking changes marked with `!` or `BREAKING CHANGE:`?
- [ ] Are commit messages descriptive?

**Change Organization:**

- [ ] Are changes atomic and focused?
- [ ] Are unrelated changes in separate commits?
- [ ] Is the change history clean and logical?

## Review Process

### 1. Initial Assessment

- Read the change description/PR description
- Understand the intent and scope
- Identify which modules are affected
- Check if changes align with project architecture

### 2. Code Analysis

Work through the checklist systematically:

1. Architecture & Design
2. Code Quality (KISS, DRY, Readability)
3. Code Standards
4. Testing & Testability
5. Documentation
6. Error Handling
7. Performance
8. Security
9. Git & Versioning

### 3. Provide Feedback

**Format:**

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

**Feedback Guidelines:**

- Be specific: Reference file paths and line numbers
- Be constructive: Suggest improvements, not just problems
- Be educational: Explain WHY something should change
- Provide examples: Show better alternatives
- Prioritize: Distinguish critical vs. nice-to-have
- Be respectful: Focus on code, not the person

### 4. Example Feedback

**Critical Issue:**

```markdown
🔴 **Violation of Separation of Concerns** (`src/workflows.py:45`)

The `generate_documentation()` function contains inline prompt text:

    prompt = "Generate documentation for..."

**Problem:** Prompts should be in `llm/prompts.py` for easy iteration and clear git diffs.

**Fix:**
1. Add constant to `llm/prompts.py`: `DOCUMENTATION_GENERATION_PROMPT = "..."`
2. Import and use: `prompt = DOCUMENTATION_GENERATION_PROMPT`

**Reference:** See `docs/style-guide.md` - Module Responsibilities
```

**Testability Issue:**

```markdown
🔴 **Untestable Code** (`src/llm/llm.py:123`)

Function `generate_docs()` directly instantiates `Gemini()` client:

    def generate_docs(context: str) -> str:
        llm = Gemini(api_key=os.environ["API_KEY"])
        return llm.complete(context)

**Problem:** Cannot mock LLM in tests; violates dependency injection pattern.

**Fix:**

    def generate_docs(llm: BaseLLM, context: str) -> str:
        return llm.complete(context)

**Test:**

    def test_generate_docs(mock_llm_client: Gemini) -> None:
        result = generate_docs(llm=mock_llm_client, context="test")
        assert result == "expected"
```

**DRY Violation:**

```markdown
🟡 **Code Duplication** (`src/output/formatters.py:78-92`, `src/output/formatters.py:156-170`)

Similar markdown formatting logic appears in two functions. Consider extracting:

    def _format_section(title: str, items: list[str]) -> str:
        """Helper to format a markdown section with items."""
        lines = [f"## {title}", ""]
        lines.extend(f"- {item}" for item in sorted(items))
        return "\n".join(lines)

This reduces duplication and ensures consistent formatting.
```

## Common Anti-Patterns to Flag

### Architecture Anti-Patterns

❌ **Business logic in `main.py`**

```python
# BAD - main.py
@cli.command()
def generate(module: str) -> None:
    # Complex business logic here
    context = analyze_code(module)  # This belongs in workflows.py
```

✅ **Delegate to workflows**

```python
# GOOD - main.py
@cli.command()
def generate(module: str) -> None:
    workflows.generate_documentation(module_name=module)
```

❌ **Inline prompts**

```python
# BAD
prompt = "You are a documentation expert..."
```

✅ **Prompts in prompts.py**

```python
# GOOD - prompts.py
DOCUMENTATION_GENERATION_PROMPT = "You are a documentation expert..."

# GOOD - llm.py
from src.prompts import DOCUMENTATION_GENERATION_PROMPT
```

### Testing Anti-Patterns

❌ **Class-based tests**

```python
# BAD
class TestFormatter:
    def test_format(self):
        ...
```

✅ **Function-based tests**

```python
# GOOD
def test_format_markdown_includes_title(sample_doc: ComponentDocumentation) -> None:
    ...
```

❌ **Unmocked external dependencies**

```python
# BAD
def test_generate_docs() -> None:
    result = generate_docs("test")  # Calls real LLM!
```

✅ **Mocked dependencies**

```python
# GOOD
def test_generate_docs(mocker: MockerFixture, mock_llm_client: Gemini) -> None:
    mock_program = mocker.patch("src.llm.LLMTextCompletionProgram")
    result = generate_docs(llm=mock_llm_client, context="test")
```

### Code Quality Anti-Patterns

❌ **Magic strings/numbers**

```python
# BAD
if depth > 5:
    raise ValueError("Too deep")
```

✅ **Named constants**

```python
# GOOD
MAX_TRAVERSAL_DEPTH = 5

if depth > MAX_TRAVERSAL_DEPTH:
    raise ValueError(f"Depth {depth} exceeds maximum {MAX_TRAVERSAL_DEPTH}")
```

❌ **Unclear variable names**

```python
# BAD
def process(d: dict) -> str:
    r = []
    for k, v in d.items():
        r.append(f"{k}: {v}")
    return "\n".join(r)
```

✅ **Descriptive names**

```python
# GOOD
def format_key_value_pairs(data: dict[str, str]) -> str:
    formatted_lines = []
    for key, value in data.items():
        formatted_lines.append(f"{key}: {value}")
    return "\n".join(formatted_lines)
```

## Tools & Automation

The agent should recommend or verify these quality checks:

**Code Quality:**

```bash
uv run ruff format          # Format code
uv run ruff check --fix     # Lint and auto-fix
uvx ty check                # Type checking
```

**Testing:**

```bash
uv run pytest tests/ --cov=src --cov-report=term-missing
```

**Documentation:**

```bash
uv run mdformat CLAUDE.md CONTRIBUTING.md README.md docs/ src/  # Format markdown
```

## Success Criteria

A code change is ready to merge when:

- ✅ All checklist items pass
- ✅ No critical issues (🔴) remain
- ✅ Test coverage ≥99%
- ✅ All quality tools pass (ruff, ty, pytest)
- ✅ Conventional Commit format used
- ✅ Documentation updated appropriately
- ✅ Code is self-documenting and maintainable

## Agent Behavior

The code review agent should:

1. **Be thorough**: Check all aspects of the checklist
2. **Be specific**: Reference exact file paths and line numbers
3. **Be educational**: Explain the reasoning behind feedback
4. **Be constructive**: Suggest improvements, not just criticisms
5. **Prioritize**: Distinguish critical vs. nice-to-have issues
6. **Be consistent**: Apply standards uniformly across all code
7. **Be efficient**: Focus on impactful issues, not nitpicks
8. **Be respectful**: Maintain a professional, collaborative tone

## References

- [docs/style-guide.md](../docs/style-guide.md) - Complete style guide
- [CLAUDE.md](../CLAUDE.md) - Project overview and guidelines
- [pyproject.toml](../pyproject.toml) - Tool configurations (ruff, pytest)
- [.pre-commit-config.yaml](../.pre-commit-config.yaml) - Pre-commit hooks
