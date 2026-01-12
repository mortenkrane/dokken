# Future Improvements

This document outlines potential improvements to the Dokken codebase.

## Table of Contents

- [Code Quality](#code-quality)
- [Architecture](#architecture)
- [Testing](#testing)
- [Type Safety](#type-safety)
- [Performance](#performance)
- [Priority Matrix](#priority-matrix)

______________________________________________________________________

## Code Quality

### 1. Centralize More Constants

**Current State:** Some constants scattered across modules:

- `TEMPERATURE = 0.0` in `src/llm.py:22`
- `depth` defaults in `src/doc_configs.py:80,106,130`
- Section headers hardcoded in `src/formatters.py` (e.g., "## Main Entry Points")

**Recommendation:** Consider moving to `src/constants.py`:

```python
# LLM configuration
LLM_TEMPERATURE = 0.0

# Analysis depth defaults
DEFAULT_DEPTH_MODULE = 0
DEFAULT_DEPTH_PROJECT = 1
DEFAULT_DEPTH_STYLE_GUIDE = -1

# Formatter section headers
SECTION_MAIN_ENTRY_POINTS = "## Main Entry Points"
SECTION_PURPOSE_SCOPE = "## Purpose & Scope"
# ... etc
```

**Benefits:**

- Single source of truth for all constants
- Easier to change formatting conventions
- Clearer what values are configurable vs hardcoded

**Drawbacks:**

- May be over-engineering for values that rarely change
- Section headers in formatters might be better as template strings

**Effort:** Low

**Impact:** Low (code organization)

**Priority:** Low

______________________________________________________________________

## Architecture

### 1. Consider Dataclass for Workflow Return Values

**Current State:** `_initialize_documentation_workflow` in `workflows.py:109-148` returns a 3-tuple:

```python
def _initialize_documentation_workflow(
    *,
    target_module_path: str,
    doc_type: DocType,
    depth: int | None,
) -> tuple[LLM, DocumentationContext, str]:
    """Returns: Tuple of (llm_client, context, code_context)."""
    # ...
    return llm_client, ctx, code_context
```

**Recommendation:** Consider using a dataclass for more explicit return type:

```python
@dataclass
class WorkflowContext:
    """Context for documentation workflow operations."""
    llm_client: LLM
    doc_context: DocumentationContext
    code_context: str

def _initialize_documentation_workflow(
    *,
    target_module_path: str,
    doc_type: DocType,
    depth: int | None,
) -> WorkflowContext:
    """Initialize and prepare all context for documentation workflow."""
    # ...
    return WorkflowContext(
        llm_client=llm_client,
        doc_context=ctx,
        code_context=code_context,
    )
```

**Benefits:**

- More explicit and self-documenting return type
- Named fields instead of tuple unpacking
- Easier to extend with additional fields
- Better IDE autocomplete
- Type checking for field access

**Drawbacks:**

- Slightly more verbose
- One more class to maintain
- Current tuple approach is simple and works well

**Effort:** Low

**Impact:** Low (code clarity improvement)

**Priority:** Low

______________________________________________________________________

### 2. Simplify Generic Types in `doc_configs.py`

**Current State:** `src/doc_configs.py:25-35` uses complex generics:

```python
@dataclass
class DocConfig[IntentT: BaseModel, ModelT: BaseModel]:
    """Configuration for documentation generation."""
    model: type[ModelT]
    intent_model: type[IntentT]
    # ...

# But usage still requires union type anyway:
AnyDocConfig = (
    DocConfig[ModuleIntent, ModuleDocumentation]
    | DocConfig[ProjectIntent, ProjectDocumentation]
    | DocConfig[StyleGuideIntent, StyleGuideDocumentation]
)
```

**Question:** Does the generic complexity provide value over direct union types?

**Recommendation:** Consider simplifying if generics don't provide practical type safety benefits:

```python
@dataclass
class DocConfig:
    """Configuration for documentation generation."""
    model: type[BaseModel]
    prompt: str
    formatter: Callable[..., str]
    intent_model: type[BaseModel]
    intent_questions: list[dict[str, str]]
    default_depth: int
    analyze_entire_repo: bool
```

**Benefits:**

- Simpler code
- Easier to understand
- Less type complexity
- Same runtime behavior

**Drawbacks:**

- Loses some compile-time type checking
- IDE autocomplete slightly less specific

**Effort:** Low

**Impact:** Low (code simplification)

**Priority:** Low

______________________________________________________________________

### 3. Reduce Overload Complexity in `input/human_in_the_loop.py`

**Current State:** Four overload signatures for type hints (`src/input/human_in_the_loop.py:14-44`):

```python
@overload
def ask_human_intent(
    *, intent_model: type[ModuleIntent], questions: list[dict[str, str]] | None = None
) -> ModuleIntent | None: ...

@overload
def ask_human_intent(
    *, intent_model: type[ProjectIntent], questions: list[dict[str, str]] | None = None
) -> ProjectIntent | None: ...

@overload
def ask_human_intent(
    *, intent_model: type[StyleGuideIntent], questions: list[dict[str, str]] | None = None
) -> StyleGuideIntent | None: ...

@overload
def ask_human_intent[IntentModelT: BaseModel](
    *, intent_model: type[IntentModelT], questions: list[dict[str, str]] | None = None
) -> IntentModelT | None: ...
```

**Question:** Are the specific overloads necessary, or would the generic version suffice?

**Recommendation:** Consider whether the three specific overloads add value. The generic overload (`IntentModelT`) should handle all cases.

**Benefits of Simplification:**

- Less code to maintain
- Simpler type signatures
- Still provides correct type hints

**Effort:** Low

**Impact:** Low (code simplification)

**Priority:** Low

______________________________________________________________________

### 4. Consider Plugin Architecture for Formatters

**Current State:** Formatters hardcoded in `formatters.py` and `doc_configs.py`

**Recommendation:** Allow custom formatters via plugin system (future enhancement):

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

- Extensibility for users
- Third-party formatters possible
- A/B testing different formats

**Effort:** High

**Impact:** Low (nice-to-have feature)

**Priority:** Future

______________________________________________________________________

## Testing

### 1. Low Priority Testing Improvements

#### Preserved Sections Display

Line 289-292 in `workflows.py` shows preserved sections in console output but isn't tested.

Suggested test:

```python
def test_fix_documentation_drift_displays_preserved_sections()
```

**Effort:** Low

**Impact:** Low (completeness)

______________________________________________________________________

#### Resource Exhaustion Scenarios

No tests for:

- Very large codebases (memory limits)
- Very deep directory structures
- Extremely long file paths
- Cache size limits

Suggested tests:

```python
def test_large_codebase_memory_efficiency()
def test_deep_directory_traversal()
def test_cache_eviction_under_size_limits()
```

**Effort:** Medium

**Impact:** Low (edge case handling)

______________________________________________________________________

#### Cross-Platform Testing

No tests for:

- Path handling differences (Windows vs Unix)
- Line ending differences (CRLF vs LF)
- Permission models (Unix file permissions)

**Effort:** Medium

**Impact:** Low (portability)

______________________________________________________________________

#### Python Version Compatibility

Line 10 in `config/loader.py` has a fallback import for Python 3.10, but this isn't tested.

Suggested test:

```python
def test_config_loader_python_310_compatibility()
```

**Effort:** Low

**Impact:** Low (compatibility assurance)

______________________________________________________________________

#### Performance Benchmarking

No performance tests. Consider adding:

- Benchmark for large codebase analysis
- Benchmark for cache hit/miss scenarios
- Benchmark for LLM call overhead

**Effort:** Medium

**Impact:** Low (performance monitoring)

______________________________________________________________________

## Type Safety

### 1. Add Runtime Type Validation for Critical Functions

**Current State:** Type hints not enforced at runtime

**Recommendation:** Use Pydantic's `validate_call` for critical functions:

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
- Better error messages for users
- Validates external inputs (CLI args, config files)

**Drawbacks:**

- Small performance overhead
- May be overkill for internal functions

**Effort:** Low

**Impact:** Low (safety net for edge cases)

**Priority:** Optional

______________________________________________________________________

## Performance

### 1. Question: Is Thread Safety Necessary for Caching?

**Current State:** `src/cache.py:17-18` uses `threading.Lock` for thread safety

```python
_drift_cache: dict[str, Any] = {}
_cache_lock = threading.Lock()
```

**Question:** Is thread safety needed for single-threaded CLI tool?

**Recommendation:** Either:

1. **Remove thread safety** if CLI is always single-threaded (simpler code)
1. **Keep thread safety** if planning async/parallel processing (document why)
1. **Use `functools.lru_cache`** if simpler caching suffices

**Option 1: Simplify (if single-threaded)**

```python
# Simple dict-based cache without locks
_drift_cache: dict[str, Any] = {}

def content_based_cache(cache_key_fn):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = cache_key_fn(*args, **kwargs)

            if cache_key in _drift_cache:
                return _drift_cache[cache_key]

            result = func(*args, **kwargs)

            if len(_drift_cache) >= DRIFT_CACHE_SIZE:
                oldest_key = next(iter(_drift_cache))
                del _drift_cache[oldest_key]

            _drift_cache[cache_key] = result
            return result
        return wrapper
    return decorator
```

**Benefits:**

- Simpler code (if removing locks)
- Better performance (no lock overhead)
- Clearer intent

**Effort:** Low

**Impact:** Low (code simplification)

**Priority:** Optional

______________________________________________________________________

## Priority Matrix

| Improvement | Effort | Impact | Priority | Category |
|-------------|--------|--------|----------|----------|
| Centralize more constants | Low | Low | **LOW** | Code Quality |
| Dataclass for workflow return values | Low | Low | **LOW** | Architecture |
| Simplify generic types | Low | Low | **LOW** | Architecture |
| Reduce overload complexity | Low | Low | **LOW** | Architecture |
| Preserved sections display test | Low | Low | **LOW** | Testing |
| Python version compatibility test | Low | Low | **LOW** | Testing |
| Resource exhaustion scenarios | Medium | Low | **LOW** | Testing |
| Cross-platform testing | Medium | Low | **LOW** | Testing |
| Performance benchmarking | Medium | Low | **LOW** | Testing |
| Add runtime type validation | Low | Low | **OPTIONAL** | Type Safety |
| Question thread safety | Low | Low | **OPTIONAL** | Performance |
| Plugin architecture | High | Low | **FUTURE** | Architecture |
