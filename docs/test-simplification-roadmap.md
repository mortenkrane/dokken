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

### 🔮 Phase 3: Reduce Implementation Coupling (Optional)

**Goal:** Replace mock-heavy tests with integration tests

**Estimated savings:** ~480 lines, \<1% coverage impact

**Rationale:** Tests that mock 5-6 internal functions are brittle and break when refactoring. Focus on behavior, not implementation.

**Files to modify:**

#### 1. **test_workflows.py** (Priority: HIGH)

**Current:** 947 lines
**Target:** ~750 lines
**Savings:** ~200 lines

**Problem:** Almost every test mocks 5-6 internal functions:

```python
def test_generate_documentation_no_drift(mocker):
    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code")
    mocker.patch("src.workflows.check_drift", return_value=no_drift)
    mocker.patch("src.workflows.console")
    # Test just verifies mocked value is returned
```

**This doesn't test actual behavior** - it tests that mocked values are returned correctly.

**Solution:**

- **Keep integration tests** in `test_integration.py` (they test real behavior with only LLM mocked)
- **Reduce workflow unit tests by 40-50%** - delete tests that only orchestrate mocks
- **Focus on business logic:** error handling, edge cases, state transitions

**Specific deletions:**

- Lines 79-98, 101-123: No drift / with drift tests - covered by integration tests
- Lines 218-256, 258-290: Filesystem tests - covered by integration tests
- Lines 153-175, 178-215: Skip generation tests - covered by integration tests

______________________________________________________________________

#### 2. **test_llm.py** (Priority: MEDIUM)

**Current:** 900 lines (after Phase 1 deletions)
**Target:** ~740 lines
**Savings:** ~160 lines

**Problem 1:** Lines 154-240 - Mock-heavy drift detection tests (3 tests)

These mock the LLM to return specific results, then verify the mocked result is returned. They don't test drift detection logic (which happens in the LLM).

**Solution:** Consolidate to 1 test verifying LLM is called with correct parameters.

**Problem 2:** Lines 892-1019 - Error propagation tests (5 tests)

Testing that Python exceptions propagate through function calls. This is Python's built-in behavior.

**Solution:** Consolidate to 1 parameterized test:

```python
@pytest.mark.parametrize("function,error", [
    (check_drift, APIError("API failure")),
    (generate_doc, TimeoutError("Timeout")),
    (fix_doc_incrementally, ValueError("Invalid response")),
])
def test_llm_errors_propagate(function, error, mocker):
    mocker.patch("src.llm.llm.LLMTextCompletionProgram", side_effect=error)
    with pytest.raises(type(error)):
        function(...)
```

______________________________________________________________________

#### 3. **test_records.py** (Priority: LOW)

**Current:** 514 lines
**Target:** ~370 lines
**Savings:** ~144 lines

**Problem:** Lines 42-185 test Pydantic's validation:

```python
def test_module_documentation_missing_field_raises():
    with pytest.raises(ValidationError):
        ModuleDocumentation(component_name="Test")  # Missing other required fields

def test_module_documentation_invalid_type_raises():
    with pytest.raises(ValidationError):
        ModuleDocumentation(component_name=123)  # Wrong type
```

**This tests Pydantic's library, not our code.**

**Solution:** Keep 1-2 smoke tests that models can be instantiated. Delete 8+ validation tests.

______________________________________________________________________

#### 4. **test_doc_merger.py** (Priority: LOW)

**Current:** 852 lines
**Target:** ~700 lines
**Savings:** ~150 lines

**Problem:** Lines 421-671 - 8 tests for markdown parsing edge cases

**Solution:** Parameterize into 2-3 tests:

```python
@pytest.mark.parametrize("markdown,description", [
    ("# Header with `code`", "special characters"),
    ("##Missing space", "malformed markdown"),
    ("No headers\njust text", "missing headers"),
    ("# 🔥 Unicode header", "unicode/emoji"),
])
def test_parse_markdown_edge_cases(markdown, description):
    sections = parse_sections(markdown)
    # Assert expected behavior
```

**Also move performance tests** (L596-614, L817-852) to separate suite or mark with `@pytest.mark.slow`

______________________________________________________________________

## Summary

| Phase | Status | Tests | Lines | Coverage Impact |
| ----- | ------ | ----- | ----- | --------------- |
| **Phase 1** | ✅ Complete | 450 → 398 (-52) | 8,990 → 8,405 (-585) | 0% |
| **Phase 2** | ✅ Complete | 398 → 377 (-21) | ~8,405 → ~7,941 (-464) | 0% |
| **Phase 3** | 🔮 Optional | ~377 → ~347 (-30) | ~7,941 → ~7,461 (-480) | \<1% |
| **TOTAL** | | 450 → 377 (-73) | 8,990 → 7,941 (-1,049) | 0% |

**Progress:** ~**12% reduction in test suite size** achieved while maintaining 99.68% coverage.

**Remaining (Optional Phase 3):** Additional ~5% reduction possible.

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

### After Phase 3 🔮

- Tests focus on **behavior** not **implementation**
- Less brittle during refactoring
- Integration tests provide better confidence than mock-heavy unit tests

## Implementation Priority

**Start here:**

1. `test_config.py` - Biggest savings (260 lines), clear pattern
1. `test_formatters.py` - High value (147 lines), simple consolidation
1. `test_main.py` - Easy deletions (77 lines), low risk

**Then:**

4. `test_error_handling.py` - Medium effort (108 lines)
1. `test_cache.py` - Low priority (100 lines)

**Optional (Phase 3):**

6. `test_workflows.py` - Requires careful analysis
1. `test_llm.py` - Moderate complexity
1. `test_records.py` - Low impact
1. `test_doc_merger.py` - Low priority

## Notes

- **Always run tests after changes:** `uv run pytest tests/ --cov=src --cov-report=term-missing`
- **Coverage threshold:** Must stay ≥99%
- **When in doubt:** Keep the test. Only remove if clearly redundant or testing framework/library code.
