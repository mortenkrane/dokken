# Future Improvements

This document outlines potential improvements to the Dokken codebase.

## Table of Contents

- [Architecture](#architecture)
- [Testing](#testing)
- [Type Safety](#type-safety)
- [Performance](#performance)
- [Priority Matrix](#priority-matrix)

______________________________________________________________________

## Architecture

### 1. Consider Plugin Architecture for Formatters

**Current State:** Formatters hardcoded in `output/formatters.py` and `doctypes/configs.py`

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

| Improvement                       | Effort | Impact | Priority     | Category     |
| --------------------------------- | ------ | ------ | ------------ | ------------ |
| Preserved sections display test   | Low    | Low    | **LOW**      | Testing      |
| Python version compatibility test | Low    | Low    | **LOW**      | Testing      |
| Resource exhaustion scenarios     | Medium | Low    | **LOW**      | Testing      |
| Cross-platform testing            | Medium | Low    | **LOW**      | Testing      |
| Performance benchmarking          | Medium | Low    | **LOW**      | Testing      |
| Add runtime type validation       | Low    | Low    | **OPTIONAL** | Type Safety  |
| Question thread safety            | Low    | Low    | **OPTIONAL** | Performance  |
| Plugin architecture               | High   | Low    | **FUTURE**   | Architecture |
