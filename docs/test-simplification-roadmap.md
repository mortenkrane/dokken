# Test Simplification Roadmap

## Overview

This document tracks the test suite simplification effort to reduce maintenance burden while maintaining 99% code coverage.

**Goal:** Reduce brittle, implementation-coupled tests that make refactoring difficult, while keeping behavior-focused tests.

## Status

### ✅ Phase 1 Complete (Quick Wins)

**Completed:** Tests reduced from **450 → 398** (-52 tests), lines from **8,990 → 8,405** (-585 lines, 6.5% reduction)

**Coverage:** Maintained at **99.68%** (target: 99%+)

**Changes made:**

1. ✅ Deleted duplicate API key priority tests in `test_llm.py` (L1022-1083, ~62 lines)
1. ✅ Deleted cache tests from `test_llm.py` (L246-362, ~116 lines) - already covered in `test_cache.py`
1. ✅ Deleted duplicate LLM error tests from `test_error_handling.py` (L24-112, ~88 lines)
1. ✅ Reduced `test_prompts.py` to 2 smoke tests (~214 → 47 lines)
1. ✅ Reduced `test_doc_types.py` to 1 smoke test (~50 → 18 lines)
1. ✅ Reduced `test_exceptions.py` to 1 smoke test (~68 → 29 lines)
1. ✅ Reduced `test_doc_configs.py` to 3 essential tests (~159 → 88 lines)

### ✅ Phase 2 Complete: Consolidation

**Completed:** Tests reduced from **398 → 377** (-21 tests), coverage maintained at **99.68%** (target: 99%+)

**Goal:** Parameterize repetitive test patterns

**Changes made:**

1. ✅ Consolidated `test_config.py` using parameterization (~115 lines saved)
1. ✅ Consolidated `test_formatters.py` field inclusion tests (~129 lines saved)
1. ✅ Removed Click framework tests from `test_main.py` (~50 lines saved)
1. ✅ Consolidated `test_error_handling.py` error propagation tests (~90 lines saved)
1. ✅ Consolidated `test_cache.py` disk persistence tests (~80 lines saved)

**Total savings:** ~464 lines removed

### ✅ Phase 3 Complete: Reduce Implementation Coupling

**Completed:** Tests reduced from **377 → 350** (-27 tests), lines from **~7,941 → ~7,443** (-498 lines, 6.3% reduction)

**Coverage:** Maintained at **99.47%** (target: 99%+)

**Goal:** Replace mock-heavy tests with integration tests; focus on behavior over implementation

**Changes made:**

1. ✅ Consolidated `test_workflows.py` mock-heavy tests (~187 lines saved)
   - Removed redundant drift detection tests (covered by integration tests)
   - Removed mock-heavy generation workflow tests (covered by integration tests)
   - Removed filesystem operation tests (covered by integration tests)
1. ✅ Consolidated `test_llm.py` drift detection tests (~54 lines saved)
   - Consolidated 3 drift detection tests into 1 parameter verification test
   - Kept error handling tests as they test different error scenarios
1. ✅ Removed `test_records.py` Pydantic validation tests (~198 lines saved)
   - Deleted tests validating Pydantic's library behavior (missing fields, type validation)
   - Kept smoke tests that models can be instantiated
   - Kept edge case and serialization tests
1. ✅ Removed `test_doc_merger.py` performance tests (~59 lines saved)
   - Removed stress tests with 100 sections and 10,000 lines
   - Kept legitimate edge case tests for parsing behavior

**Total savings:** ~498 lines removed

### 🔄 Phase 2: Original Plan (For Reference)

**Estimated savings:** ~730 lines, 0% coverage loss

**Files to modify:**

#### 1. **test_config.py** (Priority: HIGH)

**Current:** 711 lines, 32 tests with 90% identical code
**Target:** ~450 lines, ~10 tests
**Savings:** ~260 lines

**Problem:** Every test follows this pattern:

```python
def test_load_config_[feature](tmp_path):
    module_dir = tmp_path / "test"
    module_dir.mkdir()
    config_content = """..."""
    (module_dir / ".dokken.toml").write_text(config_content)
    config = load_config(str(module_dir))
    assert config.[field] == expected
```

**Solution:** Create parameterized tests:

```python
@pytest.mark.parametrize("config_toml,field_path,expected_value", [
    ('file_patterns = ["*.test.py"]', "exclusions.file_patterns", ["*.test.py"]),
    ('cache_enabled = true', "cache.enabled", True),
    # ... 30 more test cases
])
def test_load_config_fields(tmp_path, config_toml, field_path, expected_value):
    module_dir = tmp_path / "test"
    module_dir.mkdir()
    (module_dir / ".dokken.toml").write_text(f"[module]\n{config_toml}")
    config = load_config(str(module_dir))

    # Navigate nested fields using field_path
    obj = config
    for attr in field_path.split("."):
        obj = getattr(obj, attr)
    assert obj == expected_value
```

**Tests to consolidate:**

- Lines 27-147: File exclusion tests (8 tests → 1 parameterized)
- Lines 188-310: Custom prompts tests (6 tests → 1 parameterized)
- Lines 334-413: Module tests (5 tests → 1 parameterized)
- Lines 453-531: File types tests (5 tests → 1 parameterized)
- Lines 537-660: File depth tests (8 tests → 1 parameterized)

______________________________________________________________________

#### 2. **test_formatters.py** (Priority: HIGH)

**Current:** 567 lines
**Target:** ~420 lines
**Savings:** ~147 lines

**Problem:** Lines 17-116 have 9 separate tests, each checking if one field appears in formatted output:

```python
def test_format_module_documentation_includes_component_name():
    markdown = format_module_documentation(doc_data=sample)
    assert sample.component_name in markdown

def test_format_module_documentation_includes_purpose():
    markdown = format_module_documentation(doc_data=sample)
    assert sample.purpose_and_scope in markdown

# ... 7 more similar tests
```

**Solution:** Consolidate to 1 comprehensive test:

```python
def test_format_module_documentation_includes_all_fields():
    """Test that all fields appear in formatted output."""
    doc = sample_module_documentation
    markdown = format_module_documentation(doc_data=doc)

    # Check all fields present
    assert doc.component_name in markdown
    assert doc.purpose_and_scope in markdown
    assert doc.architecture_overview in markdown
    assert doc.main_entry_points in markdown
    assert doc.control_flow in markdown
    assert doc.key_design_decisions in markdown

    # Check section ordering
    assert markdown.index("## Purpose") < markdown.index("## Architecture")
    assert markdown.index("## Architecture") < markdown.index("## Entry Points")
```

**Similar consolidations needed for:**

- `test_format_project_documentation_*` tests (Lines 118-375)
- `test_format_style_guide_*` tests (Lines 377-510)

______________________________________________________________________

#### 3. **test_error_handling.py** (Priority: MEDIUM)

**Current:** 558 lines (after Phase 1 deletions)
**Target:** ~450 lines
**Savings:** ~108 lines

**Problem:** Lines 263-389 have 4 tests all verifying OSError propagates:

```python
def test_write_permission_errors(...):
    mocker.patch("builtins.open", side_effect=PermissionError("Permission denied"))
    with pytest.raises(PermissionError):
        write_documentation(...)

def test_disk_full_error_during_write(...):
    mocker.patch("builtins.open", side_effect=OSError("Disk full"))
    with pytest.raises(OSError):
        write_documentation(...)

# ... 2 more similar tests
```

**Solution:** Parameterize:

```python
@pytest.mark.parametrize("error_type,error_msg", [
    (PermissionError, "Permission denied"),
    (OSError, "Disk full"),
    (OSError, "Read-only file system"),
    (OSError, "Operation interrupted"),
])
def test_file_write_errors_propagate(error_type, error_msg, mocker):
    """Test that file I/O errors propagate correctly."""
    mocker.patch("builtins.open", side_effect=error_type(error_msg))
    with pytest.raises(error_type, match=error_msg):
        write_documentation(...)
```

**Also consolidate:**

- Multi-module error tests (Lines 118-210, 525-566) - testing same "stop on first error" behavior

______________________________________________________________________

#### 4. **test_main.py** (Priority: MEDIUM)

**Current:** 417 lines
**Target:** ~340 lines
**Savings:** ~77 lines

**Problem:** Too many tests for trivial CLI framework behavior:

**Tests to DELETE** (testing Click framework, not our code):

- Lines 21-28: `test_cli_help` - testing Click's `--help`
- Lines 39-54: `test_check_command_help`, `test_generate_command_help` - testing Click renders help
- Lines 255-259: `test_cli_commands_registered` - testing Click registers commands
- Lines 301-308, 345-361: Flag help tests - testing Click renders flags in help

**Keep:** Tests that verify our business logic (path validation, workflow calls, error handling)

______________________________________________________________________

#### 5. **test_cache.py** (Priority: LOW)

**Current:** 401 lines
**Target:** ~300 lines
**Savings:** ~100 lines

**Problem:** Disk persistence tests are repetitive (Lines 124-401, 8 tests)

**Solution:** Consolidate to 3 tests:

1. `test_save_and_load_roundtrip` (keep existing at L241-278)
1. `test_save_handles_errors` (consolidate L189-239, L341-368)
1. `test_save_creates_directories_atomically` (consolidate L313-339, L370-401)

______________________________________________________________________

### ✅ Phase 3 Complete: Implementation Details (For Reference)

**Files modified:**

#### 1. **test_workflows.py** ✅

**Before:** 947 lines
**After:** 760 lines
**Savings:** 187 lines

**Changes:**

- Removed mock-heavy drift detection tests (lines 79-123)
- Removed mock-heavy generation workflow tests (lines 153-215)
- Removed filesystem operation tests (lines 218-290)
- These behaviors are covered by integration tests in `test_integration.py`

______________________________________________________________________

#### 2. **test_llm.py** ✅

**Before:** 899 lines
**After:** 845 lines
**Savings:** 54 lines

**Changes:**

- Consolidated 3 drift detection tests into 1 parameter verification test
- Original tests mocked LLM to return values, then verified mocked values returned
- New test verifies LLM is called with correct parameters (tests behavior, not mocks)

______________________________________________________________________

#### 3. **test_records.py** ✅

**Before:** 514 lines
**After:** 316 lines
**Savings:** 198 lines

**Changes:**

- Removed Pydantic validation tests (testing library behavior, not our code)
- Deleted: missing field tests, invalid type tests, type coercion tests
- Kept: smoke tests, edge case tests (empty strings, unicode), serialization tests

______________________________________________________________________

#### 4. **test_doc_merger.py** ✅

**Before:** 852 lines
**After:** 793 lines
**Savings:** 59 lines

**Changes:**

- Removed performance/stress tests (100 sections test, 10,000 lines test)
- Kept legitimate edge case tests for parsing behavior
- Edge case tests validate real parsing logic, not implementation details

______________________________________________________________________

## Summary

| Phase | Status | Tests | Lines | Coverage Impact |
| ----- | ------ | ----- | ----- | --------------- |
| **Phase 1** | ✅ Complete | 450 → 398 (-52) | 8,990 → 8,405 (-585) | 0% |
| **Phase 2** | ✅ Complete | 398 → 377 (-21) | ~8,405 → ~7,941 (-464) | 0% |
| **Phase 3** | ✅ Complete | 377 → 350 (-27) | ~7,941 → ~7,443 (-498) | 0% |
| **TOTAL** | | 450 → 350 (-100) | 8,990 → 7,443 (-1,547) | 0% |

**Progress:** ~**17% reduction in test suite size** achieved while maintaining 99.47% coverage.

**All phases complete!** Test suite successfully simplified with focus on behavior over implementation.

## Benefits

### After Phase 1 ✅

- Removed duplicate tests (no value, pure maintenance burden)
- Removed tests of library features (Pydantic, Python stdlib, Click framework)
- Simplified constant/enum tests to smoke tests

### After Phase 2 ✅

- Reduced repetitive test patterns via parameterization
- Easier to add new test cases (just add to parameter list)
- Less code duplication = easier maintenance
- Removed tests of framework behavior (Click, Python stdlib)

### After Phase 3 ✅

- Tests focus on **behavior** not **implementation**
- Less brittle during refactoring
- Integration tests provide better confidence than mock-heavy unit tests
- Removed tests of library/framework behavior (Pydantic, Python stdlib)
- Consolidated mock-heavy tests that only verified mocked values were returned
- Kept valuable edge case tests while removing performance stress tests

## Implementation Priority

✅ **All phases complete!**

Phase 1, 2, and 3 have been successfully implemented with the following results:

1. ✅ Phase 1: Removed duplicate and redundant tests (-585 lines)
1. ✅ Phase 2: Consolidated repetitive patterns via parameterization (-464 lines)
1. ✅ Phase 3: Reduced implementation coupling (-498 lines)

**Total:** 100 fewer tests, 1,547 fewer lines, maintained 99.47% coverage

## Notes

- **Always run tests after changes:** `uv run pytest tests/ --cov=src --cov-report=term-missing`
- **Coverage threshold:** Must stay ≥99%
- **When in doubt:** Keep the test. Only remove if clearly redundant or testing framework/library code.
