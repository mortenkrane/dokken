# Future Improvements

This document outlines potential improvements to the Dokken codebase identified during the comprehensive code review conducted on 2025-12-20.

## Table of Contents

- [Code Quality](#code-quality)
- [Testing](#testing)
- [Architecture](#architecture)
- [Type Safety](#type-safety)
- [Performance](#performance)

______________________________________________________________________

## Code Quality

### 1. Reduce Code Duplication in Workflows

**Current State:** `check_documentation_drift` and `generate_documentation` share significant setup code

**Recommendation:** Extract common initialization logic into helper functions

**Example:**

```python
def _initialize_documentation_workflow(target_module_path: str, doc_type: DocType, depth: int | None):
    """Common setup for documentation workflows."""
    llm_client = initialize_llm()
    ctx = prepare_documentation_context(
        target_module_path=target_module_path,
        doc_type=doc_type,
        depth=depth,
    )
    code_context = get_module_context(
        module_path=ctx.analysis_path, depth=ctx.analysis_depth
    )
    return llm_client, ctx, code_context
```

**Benefits:**

- DRY principle
- Easier to maintain
- Consistent behavior

**Effort:** Low

**Impact:** Medium (improves maintainability)

______________________________________________________________________

### 2. Replace `NO_DOC_MARKER` String Constant

**Current State:** Using special string marker `"No existing documentation provided."`

**Recommendation:** Use sentinel object or Optional pattern

**Example:**

```python
from typing import Optional

# Option 1: Sentinel
_NO_DOC = object()

# Option 2: Just use None
current_doc: str | None = None if not exists else read_file()
```

**Benefits:**

- More explicit
- Type-safe
- Easier to understand intent

**Effort:** Low

**Impact:** Low (minor code clarity improvement)

______________________________________________________________________

## Testing

### 2. Reduce Mocking, Increase Behavior Testing

**Current State:** Heavy use of mocking makes tests brittle

**Recommendation:** Focus on testing behavior/outcomes rather than implementation

**Example:**

```python
# Current (implementation-focused)
def test_check_drift_creates_program(mocker):
    mock_program = mocker.patch("src.llm.LLMTextCompletionProgram")
    check_drift(...)
    mock_program.from_defaults.assert_called_once()  # Testing HOW

# Better (behavior-focused)
def test_check_drift_detects_structural_changes():
    # Given: Code with new module
    code = "# New module added"
    doc = "# Old documentation"

    # When: Check drift
    result = check_drift(llm, code, doc)

    # Then: Drift should be detected
    assert result.drift_detected  # Testing WHAT
    assert "Structural Changes" in result.rationale
```

**Benefits:**

- Tests survive refactoring
- Better documentation of expected behavior
- Faster test execution (less setup)

**Effort:** High (requires rewriting many tests)

**Impact:** High (more robust test suite)

______________________________________________________________________

### 3. Add Property-Based Tests

**Current State:** Example-based tests only

**Recommendation:** Use hypothesis for property-based testing

**Example:**

```python
from hypothesis import given
import hypothesis.strategies as st

@given(st.text(), st.text())
def test_drift_check_always_returns_valid_result(code, doc):
    """Drift check should never crash, regardless of input."""
    result = check_drift(llm, code, doc)
    assert isinstance(result, DocumentationDriftCheck)
    assert isinstance(result.drift_detected, bool)
    assert isinstance(result.rationale, str)
```

**Benefits:**

- Find edge cases automatically
- Better test coverage
- Discover unexpected bugs

**Effort:** Medium

**Impact:** Medium (catches edge cases)

______________________________________________________________________

## Architecture

### 1. Split Config Module

**Current State:** `config.py` handles both file loading and git operations

**Recommendation:** Separate concerns into multiple modules

**Proposed Structure:**

```
src/config/
├── __init__.py
├── loader.py       # TOML loading logic
├── models.py       # Pydantic models
└── merger.py       # Config merging logic
```

**Benefits:**

- Single Responsibility Principle
- Easier to test
- More discoverable

**Effort:** Low

**Impact:** Medium (cleaner architecture)

______________________________________________________________________

### 2. Extract Git Operations

**Current State:** Git operations scattered across modules

**Recommendation:** Create dedicated `src/git.py` module

**Example:**

```python
# src/git.py
class GitRepository:
    def __init__(self, path: str):
        self.path = path
        self.root = self._find_root()

    def _find_root(self) -> str | None:
        """Find repository root."""
        ...

    def is_git_repo(self) -> bool:
        """Check if path is in a git repository."""
        return self.root is not None

    def get_repo_root(self) -> str:
        """Get repository root (raises if not in repo)."""
        if not self.root:
            raise ValueError("Not in a git repository")
        return self.root
```

**Benefits:**

- Centralized git logic
- Easier to test
- Could support other VCS later

**Effort:** Low

**Impact:** Medium (better organization)

______________________________________________________________________

### 3. Consider Plugin Architecture for Formatters

**Current State:** Formatters hardcoded in `formatters.py`

**Recommendation:** Allow custom formatters via plugin system

**Example:**

```python
# Plugin discovery
class FormatterPlugin(Protocol):
    def format(self, doc_data: BaseModel) -> str: ...

# Registration
FORMATTERS: dict[DocType, FormatterPlugin] = {}

def register_formatter(doc_type: DocType):
    def decorator(cls: type[FormatterPlugin]):
        FORMATTERS[doc_type] = cls()
        return cls
    return decorator

# Usage
@register_formatter(DocType.MODULE_README)
class ModuleFormatter:
    def format(self, doc_data: ModuleDocumentation) -> str:
        ...
```

**Benefits:**

- Extensibility
- Third-party formatters
- A/B testing different formats

**Effort:** High

**Impact:** Low (nice-to-have feature)

______________________________________________________________________

## Type Safety

### 1. Resolve Type Ignore Comments

**Current State:** Some `# type: ignore` comments remain due to complex type relationships

**Recommendation:** Explore advanced typing features to eliminate type ignores

**Options:**

- Use Protocol classes for structural typing
- Leverage overloads for function variants
- Consider TypeGuard for runtime type narrowing

**Example:**

```python
# Current
def generate_doc(
    human_intent: BaseModel | None = None,  # type: ignore
    ...
) -> BaseModel: ...

# Option 1: Overloads
from typing import overload

@overload
def generate_doc(
    human_intent: ModuleIntent,
    output_model: type[ModuleDocumentation],
    ...
) -> ModuleDocumentation: ...

@overload
def generate_doc(
    human_intent: ProjectIntent,
    output_model: type[ProjectDocumentation],
    ...
) -> ProjectDocumentation: ...
```

**Benefits:**

- Full type safety
- Better IDE support
- Catch more errors at development time

**Effort:** High

**Impact:** Medium (developer experience)

______________________________________________________________________

### 2. Make DocConfig Generic for Full Type Safety

**Current State:** `DocConfig` has fields typed as `type[BaseModel]`, losing specific type information

**Recommendation:** Make `DocConfig` a generic dataclass to preserve intent and model types

**Example:**

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

# Define type variables
IntentT = TypeVar("IntentT", bound=BaseModel)
ModelT = TypeVar("ModelT", bound=BaseModel)

@dataclass
class DocConfig(Generic[IntentT, ModelT]):
    """Configuration for a specific documentation type."""

    intent_model: type[IntentT]
    model: type[ModelT]
    formatter: Callable[[ModelT], str]
    prompt: str
    # ... other fields

# Specific configurations with precise types
MODULE_README_CONFIG = DocConfig[ModuleIntent, ModuleDocumentation](
    intent_model=ModuleIntent,
    model=ModuleDocumentation,
    formatter=format_module_documentation,
    ...
)

PROJECT_README_CONFIG = DocConfig[ProjectIntent, ProjectDocumentation](
    intent_model=ProjectIntent,
    model=ProjectDocumentation,
    formatter=format_project_documentation,
    ...
)

# Now type inference works perfectly
config = DOC_CONFIGS[DocType.MODULE_README]  # type: DocConfig[ModuleIntent, ModuleDocumentation]
intent = ask_human_intent(intent_model=config.intent_model)  # type: ModuleIntent | None
```

**Benefits:**

- Full type safety throughout the workflow
- Type checker understands intent types from config
- No `BaseModel | None` - precise `ModuleIntent | None` instead
- Better IDE autocomplete
- Catches mismatched intent/model combinations at type-check time

**Effort:** Medium (affects `doc_configs.py`, `workflows.py`, type annotations)

**Impact:** High (eliminates remaining type safety gaps)

______________________________________________________________________

### 3. Add Runtime Type Validation

**Current State:** Type hints are not enforced at runtime

**Recommendation:** Use Pydantic's `validate_call` decorator for critical functions

**Example:**

```python
from pydantic import validate_call

@validate_call
def resolve_output_path(
    *,
    doc_type: DocType,
    module_path: str,
) -> str:
    """Type-checked at runtime."""
    ...
```

**Benefits:**

- Catch type errors early
- Better error messages
- Validates external inputs

**Effort:** Low

**Impact:** Low (safety net for edge cases)

______________________________________________________________________

## Performance

### 1. Cache LLM Initialization

**Current State:** LLM client created fresh for each operation

**Recommendation:** Implement singleton or caching for LLM client

**Example:**

```python
from functools import lru_cache

@lru_cache(maxsize=1)
def get_llm_client() -> LLM:
    """Cached LLM client initialization."""
    return initialize_llm()
```

**Benefits:**

- Faster startup
- Reduced memory usage
- Consistent client across operations

**Effort:** Low

**Impact:** Low (minor performance improvement)

______________________________________________________________________

### 2. Parallelize File Reading

**Current State:** Files read sequentially in `get_module_context`

**Recommendation:** Use concurrent file reading for large codebases

**Example:**

```python
from concurrent.futures import ThreadPoolExecutor

def get_module_context(module_path: str, depth: int = 0) -> str:
    files = _find_python_files(module_path=module_path, depth=depth)

    with ThreadPoolExecutor() as executor:
        contents = executor.map(_read_and_filter_file, files)

    return _combine_file_contents(contents)
```

**Benefits:**

- Faster for large projects
- Better resource utilization

**Effort:** Medium

**Impact:** Medium (noticeable on large codebases)

______________________________________________________________________

### 3. Add Caching for Drift Detection

**Current State:** Every check requires full LLM call

**Recommendation:** Cache drift detection results based on code hash

**Example:**

```python
import hashlib
from functools import lru_cache

def _hash_content(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()

@lru_cache(maxsize=100)
def check_drift_cached(
    code_hash: str,
    doc_hash: str,
) -> DocumentationDriftCheck:
    # Only called if cache miss
    return check_drift(llm, code, doc)
```

**Benefits:**

- Faster CI/CD checks
- Reduced LLM API costs
- Better developer experience

**Effort:** Medium

**Impact:** High (significant speed improvement)

______________________________________________________________________

## Priority Matrix

| Improvement | Effort | Impact | Priority |
|-------------|--------|--------|----------|
| Reduce Mocking | High | High | **HIGH** |
| Cache Drift Detection | Medium | High | **HIGH** |
| Make DocConfig Generic | Medium | High | **HIGH** |
| Extract Git Operations | Low | Medium | **MEDIUM** |
| Reduce Code Duplication | Low | Medium | **MEDIUM** |
| Split Config Module | Low | Medium | **MEDIUM** |
| Add Property-Based Tests | Medium | Medium | **LOW** |
| Plugin Architecture | High | Low | **LOW** |

______________________________________________________________________

## Contributing

These improvements are suggestions based on a comprehensive code review. Before implementing:

1. **Discuss with maintainers** - Ensure alignment with project goals
1. **Create issues** - Track each improvement separately
1. **Start small** - Begin with high-priority, low-effort items
1. **Test thoroughly** - All changes should maintain 100% test pass rate

______________________________________________________________________

**Last Updated:** 2025-12-20
**Review By:** Claude Code (Comprehensive Python Code Review)
