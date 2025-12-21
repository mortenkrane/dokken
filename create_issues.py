#!/usr/bin/env python3
"""Script to create GitHub issues from the future improvements document."""

import json
import os
import sys
from typing import Any

try:
    import requests
except ImportError:
    print("ERROR: requests library not found. Install with: pip install requests")
    sys.exit(1)


def create_issue(
    token: str, owner: str, repo: str, title: str, body: str, labels: list[str]
) -> dict[str, Any]:
    """Create a GitHub issue using the GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {"title": title, "body": body, "labels": labels}

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def main() -> None:
    """Main function to create all issues."""
    # Get GitHub token from environment or command line
    token = os.getenv("GITHUB_TOKEN")
    if not token and len(sys.argv) > 1:
        token = sys.argv[1]

    if not token:
        print("ERROR: GitHub token required!")
        print("Usage: python create_issues.py <github_token>")
        print("   OR: GITHUB_TOKEN=<token> python create_issues.py")
        sys.exit(1)

    owner = "mortenkrane"
    repo = "dokken"

    # Define all issues
    issues = [
        {
            "title": "Code Quality: Reduce code duplication in workflows",
            "body": """## Category
Code Quality

## Current State
`check_documentation_drift` and `generate_documentation` share significant setup code

## Recommendation
Extract common initialization logic into helper functions

## Benefits
- DRY principle
- Easier to maintain
- Consistent behavior

## Effort/Impact
- Effort: Low
- Impact: Medium (improves maintainability)

## Example
```python
def _initialize_documentation_workflow(target_module_path: str, doc_type: DocType, depth: int | None):
    \"\"\"Common setup for documentation workflows.\"\"\"
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

**Priority: MEDIUM**""",
            "labels": ["enhancement", "code-quality"],
        },
        {
            "title": "Code Quality: Replace NO_DOC_MARKER string constant",
            "body": """## Category
Code Quality

## Current State
Using special string marker `"No existing documentation provided."`

## Recommendation
Use sentinel object or Optional pattern

## Benefits
- More explicit
- Type-safe
- Easier to understand intent

## Effort/Impact
- Effort: Low
- Impact: Low (minor code clarity improvement)

## Example
```python
from typing import Optional

# Option 1: Sentinel
_NO_DOC = object()

# Option 2: Just use None
current_doc: str | None = None if not exists else read_file()
```

**Priority: LOW**""",
            "labels": ["enhancement", "code-quality"],
        },
        {
            "title": "Testing: Add integration tests",
            "body": """## Category
Testing

## Current State
188 unit tests, 0 integration tests

## Recommendation
Add end-to-end tests that exercise the full workflow

## Benefits
- Catch integration issues
- Verify real-world behavior
- Increase confidence in releases

## Effort/Impact
- Effort: Medium (requires test infrastructure setup)
- Impact: High (significantly improves test coverage)

## Example
```python
def test_full_documentation_generation_workflow(tmp_path):
    \"\"\"Test complete workflow from code analysis to file writing.\"\"\"
    # Setup: Create a real Python module
    module_dir = create_sample_module(tmp_path)

    # Execute: Run actual generation (not mocked)
    result = generate_documentation(
        target_module_path=str(module_dir),
        doc_type=DocType.MODULE_README,
    )

    # Verify: Check README was created with expected structure
    readme = module_dir / "README.md"
    assert readme.exists()
    assert "## Purpose & Scope" in readme.read_text()
```

**Priority: HIGH**""",
            "labels": ["enhancement", "testing"],
        },
        {
            "title": "Testing: Reduce mocking, increase behavior testing",
            "body": """## Category
Testing

## Current State
Heavy use of mocking makes tests brittle

## Recommendation
Focus on testing behavior/outcomes rather than implementation

## Benefits
- Tests survive refactoring
- Better documentation of expected behavior
- Faster test execution (less setup)

## Effort/Impact
- Effort: High (requires rewriting many tests)
- Impact: High (more robust test suite)

## Example
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

**Priority: HIGH**""",
            "labels": ["enhancement", "testing"],
        },
        {
            "title": "Testing: Add property-based tests",
            "body": """## Category
Testing

## Current State
Example-based tests only

## Recommendation
Use hypothesis for property-based testing

## Benefits
- Find edge cases automatically
- Better test coverage
- Discover unexpected bugs

## Effort/Impact
- Effort: Medium
- Impact: Medium (catches edge cases)

## Example
```python
from hypothesis import given
import hypothesis.strategies as st

@given(st.text(), st.text())
def test_drift_check_always_returns_valid_result(code, doc):
    \"\"\"Drift check should never crash, regardless of input.\"\"\"
    result = check_drift(llm, code, doc)
    assert isinstance(result, DocumentationDriftCheck)
    assert isinstance(result.drift_detected, bool)
    assert isinstance(result.rationale, str)
```

**Priority: LOW**""",
            "labels": ["enhancement", "testing"],
        },
        {
            "title": "Architecture: Split config module",
            "body": """## Category
Architecture

## Current State
`config.py` handles both file loading and git operations

## Recommendation
Separate concerns into multiple modules

## Benefits
- Single Responsibility Principle
- Easier to test
- More discoverable

## Effort/Impact
- Effort: Low
- Impact: Medium (cleaner architecture)

## Proposed Structure
```
src/config/
├── __init__.py
├── loader.py       # TOML loading logic
├── models.py       # Pydantic models
└── merger.py       # Config merging logic
```

**Priority: MEDIUM**""",
            "labels": ["enhancement", "architecture"],
        },
        {
            "title": "Architecture: Extract git operations",
            "body": """## Category
Architecture

## Current State
Git operations scattered across modules

## Recommendation
Create dedicated `src/git.py` module

## Benefits
- Centralized git logic
- Easier to test
- Could support other VCS later

## Effort/Impact
- Effort: Low
- Impact: Medium (better organization)

## Example
```python
# src/git.py
class GitRepository:
    def __init__(self, path: str):
        self.path = path
        self.root = self._find_root()

    def _find_root(self) -> str | None:
        \"\"\"Find repository root.\"\"\"
        ...

    def is_git_repo(self) -> bool:
        \"\"\"Check if path is in a git repository.\"\"\"
        return self.root is not None

    def get_repo_root(self) -> str:
        \"\"\"Get repository root (raises if not in repo).\"\"\"
        if not self.root:
            raise ValueError("Not in a git repository")
        return self.root
```

**Priority: MEDIUM**""",
            "labels": ["enhancement", "architecture"],
        },
        {
            "title": "Architecture: Consider plugin architecture for formatters",
            "body": """## Category
Architecture

## Current State
Formatters hardcoded in `formatters.py`

## Recommendation
Allow custom formatters via plugin system

## Benefits
- Extensibility
- Third-party formatters
- A/B testing different formats

## Effort/Impact
- Effort: High
- Impact: Low (nice-to-have feature)

## Example
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

**Priority: LOW**""",
            "labels": ["enhancement", "architecture"],
        },
        {
            "title": "Type Safety: Resolve type ignore comments",
            "body": """## Category
Type Safety

## Current State
Some `# type: ignore` comments remain due to complex type relationships

## Recommendation
Explore advanced typing features to eliminate type ignores

## Benefits
- Full type safety
- Better IDE support
- Catch more errors at development time

## Effort/Impact
- Effort: High
- Impact: Medium (developer experience)

## Options
- Use Protocol classes for structural typing
- Leverage overloads for function variants
- Consider TypeGuard for runtime type narrowing

## Example
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

**Priority: MEDIUM**""",
            "labels": ["enhancement", "type-safety"],
        },
        {
            "title": "Type Safety: Make DocConfig generic for full type safety",
            "body": """## Category
Type Safety

## Current State
`DocConfig` has fields typed as `type[BaseModel]`, losing specific type information

## Recommendation
Make `DocConfig` a generic dataclass to preserve intent and model types

## Benefits
- Full type safety throughout the workflow
- Type checker understands intent types from config
- No `BaseModel | None` - precise `ModuleIntent | None` instead
- Better IDE autocomplete
- Catches mismatched intent/model combinations at type-check time

## Effort/Impact
- Effort: Medium (affects `doc_configs.py`, `workflows.py`, type annotations)
- Impact: High (eliminates remaining type safety gaps)

## Example
```python
from typing import Generic, TypeVar
from pydantic import BaseModel

# Define type variables
IntentT = TypeVar("IntentT", bound=BaseModel)
ModelT = TypeVar("ModelT", bound=BaseModel)

@dataclass
class DocConfig(Generic[IntentT, ModelT]):
    \"\"\"Configuration for a specific documentation type.\"\"\"

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

# Now type inference works perfectly
config = DOC_CONFIGS[DocType.MODULE_README]  # type: DocConfig[ModuleIntent, ModuleDocumentation]
intent = ask_human_intent(intent_model=config.intent_model)  # type: ModuleIntent | None
```

**Priority: HIGH**""",
            "labels": ["enhancement", "type-safety"],
        },
        {
            "title": "Type Safety: Add runtime type validation",
            "body": """## Category
Type Safety

## Current State
Type hints are not enforced at runtime

## Recommendation
Use Pydantic's `validate_call` decorator for critical functions

## Benefits
- Catch type errors early
- Better error messages
- Validates external inputs

## Effort/Impact
- Effort: Low
- Impact: Low (safety net for edge cases)

## Example
```python
from pydantic import validate_call

@validate_call
def resolve_output_path(
    *,
    doc_type: DocType,
    module_path: str,
) -> str:
    \"\"\"Type-checked at runtime.\"\"\"
    ...
```

**Priority: LOW**""",
            "labels": ["enhancement", "type-safety"],
        },
        {
            "title": "Performance: Cache LLM initialization",
            "body": """## Category
Performance

## Current State
LLM client created fresh for each operation

## Recommendation
Implement singleton or caching for LLM client

## Benefits
- Faster startup
- Reduced memory usage
- Consistent client across operations

## Effort/Impact
- Effort: Low
- Impact: Low (minor performance improvement)

## Example
```python
from functools import lru_cache

@lru_cache(maxsize=1)
def get_llm_client() -> LLM:
    \"\"\"Cached LLM client initialization.\"\"\"
    return initialize_llm()
```

**Priority: LOW**""",
            "labels": ["enhancement", "performance"],
        },
        {
            "title": "Performance: Parallelize file reading",
            "body": """## Category
Performance

## Current State
Files read sequentially in `get_module_context`

## Recommendation
Use concurrent file reading for large codebases

## Benefits
- Faster for large projects
- Better resource utilization

## Effort/Impact
- Effort: Medium
- Impact: Medium (noticeable on large codebases)

## Example
```python
from concurrent.futures import ThreadPoolExecutor

def get_module_context(module_path: str, depth: int = 0) -> str:
    files = _find_python_files(module_path=module_path, depth=depth)

    with ThreadPoolExecutor() as executor:
        contents = executor.map(_read_and_filter_file, files)

    return _combine_file_contents(contents)
```

**Priority: MEDIUM**""",
            "labels": ["enhancement", "performance"],
        },
        {
            "title": "Performance: Add caching for drift detection",
            "body": """## Category
Performance

## Current State
Every check requires full LLM call

## Recommendation
Cache drift detection results based on code hash

## Benefits
- Faster CI/CD checks
- Reduced LLM API costs
- Better developer experience

## Effort/Impact
- Effort: Medium
- Impact: High (significant speed improvement)

## Example
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

**Priority: HIGH**""",
            "labels": ["enhancement", "performance"],
        },
    ]

    print(f"Creating {len(issues)} issues in {owner}/{repo}...")
    created_count = 0

    for issue in issues:
        try:
            result = create_issue(
                token=token,
                owner=owner,
                repo=repo,
                title=issue["title"],
                body=issue["body"],
                labels=issue["labels"],
            )
            created_count += 1
            print(f"✓ Created issue #{result['number']}: {issue['title']}")
        except requests.exceptions.HTTPError as e:
            print(f"✗ Failed to create issue '{issue['title']}': {e}")
            if e.response.status_code == 401:
                print("  ERROR: Invalid GitHub token")
                sys.exit(1)
            elif e.response.status_code == 403:
                print("  ERROR: Insufficient permissions")
                sys.exit(1)

    print(f"\nSuccessfully created {created_count}/{len(issues)} issues!")


if __name__ == "__main__":
    main()
