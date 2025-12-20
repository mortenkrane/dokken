# Multi-Doc-Type Support Implementation Plan

## Overview

Extend Dokken to support three documentation types:

1. **Module README** - Architectural design and structural choices (current functionality)
1. **Top-level README** - Repository introduction, purpose, setup instructions
1. **Style Guide** - Code patterns and coding conventions extracted from codebase

## Current System Analysis

The current system is hardcoded for module READMEs:

- Hardcoded `README.md` path in workflows.py (lines 40, 146)
- Single `ComponentDocumentation` Pydantic model
- Single generation prompt (`DOCUMENTATION_GENERATION_PROMPT`)
- Formatter only handles module README structure

**Strengths to preserve:**

- Clean separation of concerns (workflows → analyzer → LLM → formatters)
- Prompt-as-constants pattern
- Structured output with Pydantic models
- Deterministic generation (temperature=0.0)
- Human-in-the-loop for intent capture

## Architectural Design

### 1. Core Abstraction: DocType Enum

```python
# src/doc_types.py (new file)
from enum import Enum

class DocType(str, Enum):
    MODULE_README = "module-readme"
    PROJECT_README = "project-readme"
    STYLE_GUIDE = "style-guide"
```

### 2. Doc-Type-Specific Models

Each doc type needs its own Pydantic model:

```python
# src/records.py (additions)

# Module README (existing ComponentDocumentation - rename for clarity)
class ModuleDocumentation(BaseModel):
    """Module-level architectural documentation"""
    component_name: str
    purpose_and_scope: str
    architecture_overview: str
    main_entry_points: str
    control_flow: str
    key_design_decisions: str
    external_dependencies: str | None

# Project README (new)
class ProjectDocumentation(BaseModel):
    """Top-level project documentation"""
    project_name: str
    project_purpose: str  # What problem does this solve?
    key_features: str  # Bulleted list of main features
    installation: str  # Setup for users
    development_setup: str  # Setup for contributors
    usage_examples: str  # Basic usage patterns
    project_structure: str  # High-level directory overview
    contributing: str | None  # How to contribute

# Style Guide (new)
class StyleGuideDocumentation(BaseModel):
    """Code style and conventions documentation"""
    project_name: str
    languages: list[str]  # Languages found in codebase
    code_style_patterns: str  # Formatting, naming conventions
    architectural_patterns: str  # Common patterns used
    testing_conventions: str  # Test structure and practices
    git_workflow: str  # Branching, commits, PR process
    module_organization: str  # How code is organized
    dependencies_management: str  # How deps are managed
```

### 3. Doc-Type-Specific Prompts

Add to `src/prompts.py`:

```python
# Existing drift check can be reused for all doc types

# Module README generation (existing - keep as is)
MODULE_GENERATION_PROMPT = """..."""  # Current DOCUMENTATION_GENERATION_PROMPT

# Project README generation (new)
PROJECT_README_GENERATION_PROMPT = """
You are an expert technical writer creating a top-level README for a software project.
Your goal is to introduce the project to new users and contributors.

Generate documentation that covers:
1. Project Purpose - What problem does this solve? Why does it exist?
2. Key Features - What are the main capabilities?
3. Installation - How do users install and set up for usage?
4. Development Setup - How do contributors set up for development?
5. Usage Examples - Basic usage patterns and commands
6. Project Structure - High-level overview of directory organization
7. Contributing - How to contribute (optional if not applicable)

Focus on:
- Clear, welcoming introduction for new users
- Practical setup instructions (both usage and development)
- Concrete examples
- High-level understanding of project structure

Avoid:
- Deep architectural details (those go in module READMEs)
- API reference documentation
- Marketing language or hype
- Excessive detail about implementation

Code context:
{context}

{human_intent_section}

Generate the documentation following the specified structure.
"""

# Style Guide generation (new)
STYLE_GUIDE_GENERATION_PROMPT = """
You are an expert technical writer analyzing code patterns to extract coding conventions.
Your goal is to document the *actual* patterns used in this codebase, not generic best practices.

Analyze the code and extract:
1. Languages - Programming languages used in this project
2. Code Style Patterns - Formatting, naming conventions, structure
3. Architectural Patterns - Design patterns, abstractions, DI patterns
4. Testing Conventions - Test structure, mocking patterns, fixtures
5. Git Workflow - Branching strategy, commit message format, PR practices
6. Module Organization - How code is organized into modules/packages
7. Dependencies Management - How dependencies are declared and managed

Focus on:
- Patterns that appear consistently across multiple files
- Specific examples from the codebase
- Conventions that new contributors should follow
- Differences from standard practices (if any)

Avoid:
- Generic best practices not evidenced in the code
- Prescriptive rules not currently followed
- Implementation details of specific features
- Documenting every minor variation

Code context:
{context}

{human_intent_section}

Generate the style guide following the specified structure.
"""
```

### 4. Doc-Type-Specific Formatters

Add to `src/formatters.py`:

```python
# Existing module README formatter (rename for clarity)
def format_module_documentation(*, doc_data: ModuleDocumentation) -> str:
    """Format module architectural documentation"""
    # Current implementation

def format_project_documentation(*, doc_data: ProjectDocumentation) -> str:
    """Format top-level project README"""
    sections = [
        f"# {doc_data.project_name}\n",
        f"## Purpose\n\n{doc_data.project_purpose}\n",
        f"## Key Features\n\n{doc_data.key_features}\n",
        f"## Installation\n\n{doc_data.installation}\n",
        f"## Development Setup\n\n{doc_data.development_setup}\n",
        f"## Usage\n\n{doc_data.usage_examples}\n",
        f"## Project Structure\n\n{doc_data.project_structure}\n",
    ]

    if doc_data.contributing:
        sections.append(f"## Contributing\n\n{doc_data.contributing}\n")

    return "\n".join(sections)

def format_style_guide(*, doc_data: StyleGuideDocumentation) -> str:
    """Format style guide documentation"""
    sections = [
        f"# {doc_data.project_name} Style Guide\n",
        f"## Languages\n\n{', '.join(doc_data.languages)}\n",
        f"## Code Style Patterns\n\n{doc_data.code_style_patterns}\n",
        f"## Architectural Patterns\n\n{doc_data.architectural_patterns}\n",
        f"## Testing Conventions\n\n{doc_data.testing_conventions}\n",
        f"## Git Workflow\n\n{doc_data.git_workflow}\n",
        f"## Module Organization\n\n{doc_data.module_organization}\n",
        f"## Dependencies Management\n\n{doc_data.dependencies_management}\n",
    ]

    return "\n".join(sections)
```

### 5. Doc-Type Configuration Registry (SIMPLIFIED)

```python
# src/doc_configs.py (new file)
from dataclasses import dataclass
from typing import Callable, Type
from pydantic import BaseModel

from .doc_types import DocType
from .records import (
    ModuleDocumentation, ProjectDocumentation, StyleGuideDocumentation,
    ModuleIntent, ProjectIntent, StyleGuideIntent
)
from . import prompts
from . import formatters

@dataclass
class DocConfig:
    """Configuration for documentation generation (NOT path resolution)"""
    model: Type[BaseModel]  # Pydantic model for structured output
    prompt: str  # Prompt template
    formatter: Callable[[BaseModel], str]  # Formatter function
    intent_model: Type[BaseModel]  # Intent model for human-in-the-loop
    intent_questions: list[dict[str, str]]  # Questions for intent capture
    default_depth: int  # Default code analysis depth
    analyze_entire_repo: bool  # Whether to analyze entire repo vs module

# Registry mapping doc types to their configurations
DOC_CONFIGS: dict[DocType, DocConfig] = {
    DocType.MODULE_README: DocConfig(
        model=ModuleDocumentation,
        prompt=prompts.MODULE_GENERATION_PROMPT,
        formatter=formatters.format_module_documentation,
        intent_model=ModuleIntent,
        intent_questions=[
            {"key": "problems_solved", "question": "What problems does this module solve?"},
            {"key": "core_responsibilities", "question": "What are the module's core responsibilities?"},
            {"key": "non_responsibilities", "question": "What is NOT this module's responsibility?"},
            {"key": "system_context", "question": "How does the module fit into the larger system?"},
        ],
        default_depth=0,
        analyze_entire_repo=False,
    ),
    DocType.PROJECT_README: DocConfig(
        model=ProjectDocumentation,
        prompt=prompts.PROJECT_README_GENERATION_PROMPT,
        formatter=formatters.format_project_documentation,
        intent_model=ProjectIntent,
        intent_questions=[
            {"key": "project_type", "question": "Is this a library/tool/application/framework?"},
            {"key": "target_audience", "question": "Who is the primary audience?"},
            {"key": "key_problem", "question": "What problem does this project solve?"},
            {"key": "setup_notes", "question": "Any special setup considerations?"},
        ],
        default_depth=1,
        analyze_entire_repo=True,
    ),
    DocType.STYLE_GUIDE: DocConfig(
        model=StyleGuideDocumentation,
        prompt=prompts.STYLE_GUIDE_GENERATION_PROMPT,
        formatter=formatters.format_style_guide,
        intent_model=StyleGuideIntent,
        intent_questions=[
            {"key": "unique_conventions", "question": "Are there any unique conventions in this codebase?"},
            {"key": "organization_notes", "question": "What should new contributors know about code organization?"},
            {"key": "patterns", "question": "Are there specific patterns to follow or avoid?"},
        ],
        default_depth=-1,  # Full recursion
        analyze_entire_repo=True,
    ),
}
```

### 5b. Path Resolution (in workflows.py - NOT in registry)

```python
# src/workflows.py (addition)
def resolve_output_path(*, doc_type: DocType, module_path: str) -> str:
    """Resolve output path with explicit error handling.

    Raises:
        ValueError: If git root not found for repo-wide doc types
        PermissionError: If cannot create directories
    """
    if doc_type == DocType.MODULE_README:
        return os.path.join(module_path, "README.md")

    # Find git root for repo-wide docs
    repo_root = _find_repo_root(module_path)
    if not repo_root:
        raise ValueError(
            f"Cannot generate {doc_type.value}: not in a git repository. "
            f"Initialize git or use MODULE_README type."
        )

    if doc_type == DocType.PROJECT_README:
        return os.path.join(repo_root, "README.md")

    if doc_type == DocType.STYLE_GUIDE:
        # Explicit side effect: create docs/ directory
        docs_dir = os.path.join(repo_root, "docs")
        try:
            os.makedirs(docs_dir, exist_ok=True)
        except PermissionError as e:
            raise PermissionError(f"Cannot create {docs_dir}: {e}")
        return os.path.join(docs_dir, "style-guide.md")

    raise ValueError(f"Unknown doc type: {doc_type}")
```

### 6. Workflow Updates

Update `src/workflows.py` to accept doc type parameter:

```python
def generate_documentation(
    *,
    target_module_path: str,
    depth: int = 0,
    doc_type: DocType = DocType.MODULE_README  # New parameter
) -> str | None:
    """Generate documentation for specified doc type"""

    # Get doc type configuration
    doc_config = DOC_TYPE_REGISTRY[doc_type]

    # Resolve output path based on doc type
    output_path = doc_config.default_path_resolver(target_module_path)

    # Initialize LLM
    llm = initialize_llm()

    # Analyze code (may need different depth for different doc types)
    context = analyze_code_context(
        target_module_path=target_module_path,
        depth=depth if doc_type == DocType.MODULE_README else 1  # Style guide needs broader view
    )

    # Check drift
    current_doc = read_existing_doc(output_path)
    drift_check = check_drift(llm=llm, context=context, current_doc=current_doc)

    if not drift_check.drift_detected and current_doc != PLACEHOLDER_DOC:
        # No drift, skip generation
        return None

    # Capture human intent (questionnaire may vary by doc type)
    human_intent = capture_human_intent_for_doc_type(doc_type=doc_type)

    # Generate structured documentation using doc-type-specific config
    doc_data = generate_structured_documentation(
        llm=llm,
        context=context,
        human_intent=human_intent,
        output_cls=doc_config.output_cls,
        prompt_template=doc_config.generation_prompt,
    )

    # Format to markdown using doc-type-specific formatter
    markdown = doc_config.formatter(doc_data=doc_data)

    # Write to disk
    with open(output_path, "w") as f:
        f.write(markdown)

    return output_path
```

### 7. CLI Updates

Update `src/main.py` to support doc type selection:

```python
@app.command()
def generate(
    module: str = typer.Argument(..., help="Path to module directory"),
    depth: int = typer.Option(0, help="Directory traversal depth"),
    doc_type: DocType = typer.Option(
        DocType.MODULE_README,
        help="Type of documentation to generate"
    ),
):
    """Generate documentation for a module"""
    result = generate_documentation(
        target_module_path=module,
        depth=depth,
        doc_type=doc_type,
    )
    # ...

@app.command()
def check(
    module: str = typer.Argument(..., help="Path to module directory"),
    depth: int = typer.Option(0, help="Directory traversal depth"),
    fix: bool = typer.Option(False, "--fix", help="Auto-fix drift"),
    doc_type: DocType = typer.Option(
        DocType.MODULE_README,
        help="Type of documentation to check"
    ),
):
    """Check for documentation drift"""
    # ...
```

### 8. Human-in-the-Loop Customization

Different doc types need different questions:

```python
# src/human_in_the_loop.py (updates)

def capture_human_intent_for_doc_type(*, doc_type: DocType) -> HumanIntent:
    """Capture human intent with doc-type-specific questions"""

    if doc_type == DocType.MODULE_README:
        # Existing module-focused questions
        return capture_human_intent()

    elif doc_type == DocType.PROJECT_README:
        # Project-level questions
        questions = [
            "What problem does this project solve? (Who is it for?)",
            "What are the 3-5 most important features?",
            "Are there any special setup considerations?",
            "Is this library/tool/application/framework?",
        ]
        # ...

    elif doc_type == DocType.STYLE_GUIDE:
        # Style guide questions
        questions = [
            "Are there any unique conventions in this codebase?",
            "What should new contributors know about code organization?",
            "Are there specific patterns to follow or avoid?",
        ]
        # ...
```

## Implementation Steps (REVISED)

### Phase 1: Build All Components First

1. Create `src/doc_types.py` with `DocType` enum
1. Add ALL new Pydantic models to `src/records.py`:
   - `ModuleDocumentation` (rename from `ComponentDocumentation`)
   - `ProjectDocumentation` (new)
   - `StyleGuideDocumentation` (new)
   - `ModuleIntent`, `ProjectIntent`, `StyleGuideIntent` (new)
1. Add ALL new prompts to `src/prompts.py`:
   - `MODULE_GENERATION_PROMPT` (rename from `DOCUMENTATION_GENERATION_PROMPT`)
   - `PROJECT_README_GENERATION_PROMPT` (new)
   - `STYLE_GUIDE_GENERATION_PROMPT` (new)
1. Add ALL new formatters to `src/formatters.py`:
   - `format_module_documentation` (rename from `generate_markdown`)
   - `format_project_documentation` (new)
   - `format_style_guide` (new)
1. Add backward compatibility aliases for breaking changes

### Phase 2: Create Complete Registry

6. Create `src/doc_configs.py` with `DocConfig` dataclass
1. Populate `DOC_CONFIGS` registry with ALL three doc types
1. Add `resolve_output_path()` function to `src/workflows.py`
1. Export `_find_repo_root()` from `src/config.py` (or make it importable)

### Phase 3: Refactor Workflows

10. Update `generate_documentation()` to accept `doc_type` parameter
01. Implement code analysis path resolution (module vs repo-wide)
01. Update drift checking to use doc type config
01. Update human-in-the-loop to use intent models from config
01. Use registry for prompt, model, and formatter selection

### Phase 4: CLI Integration

15. Update `generate` command to accept `--doc-type` option
01. Update `check` command to accept `--doc-type` option
01. Add doc type to help text and descriptions
01. Handle optional module path for repo-wide doc types

### Phase 5: Testing

19. Update existing tests to use new names (with aliases for compatibility)
01. Add tests for project README generation
01. Add tests for style guide generation
01. Add tests for path resolution
01. Add CLI tests for each doc type
01. Integration tests for drift detection across doc types

### Phase 6: Refinement & Documentation

25. Test prompts with real codebases and iterate
01. Verify repo-wide analysis works for style guide
01. Update project README and style guide
01. Remove deprecation aliases in future major version

## Risks & Mitigations (REVISED)

**Risk 1: Git root may not exist**

- Problem: Repo-wide docs need git root, but user may run outside git repo
- Mitigation: Explicit error handling in `resolve_output_path()` with clear error messages

**Risk 2: Style guide needs repo-wide analysis**

- Problem: Current system is module-centric, style guide should analyze entire repo
- Solution: Add `analyze_entire_repo` flag to config; when true, use git root and full recursion

**Risk 3: Drift detection prompt is module-specific**

- Problem: Current checklist (structural changes, purpose mismatch) is for module READMEs
- Mitigation: Start with shared prompt (pragmatic), plan for doc-type-specific drift prompts later
- Future: Add style-guide-specific drift criteria ("new patterns emerged", "conventions changed")

**Risk 4: Breaking changes without deprecation**

- Problem: Renaming `ComponentDocumentation` breaks imports
- Solution: Add backward compatibility aliases with deprecation warnings

**Risk 5: CLI UX for repo-wide docs**

- Problem: `dokken generate src/ --doc-type style-guide` is confusing (why pass module?)
- Solution: Make module path optional when doc type is repo-wide

**Risk 6: Prompt quality for new doc types**

- Mitigation: Iterate on prompts, test with real codebases

**Risk 7: Output path conflicts**

- Mitigation: Clear path resolution rules, validate before writing
- Solution: Warn if overwriting important files

## Open Questions

1. Should style guide be generated from entire repo or per-module?

   - **Recommendation**: Entire repo (single style guide in docs/)

1. Should project README use git root detection or explicit path?

   - **Recommendation**: Git root detection for convenience

1. Should drift detection prompt be doc-type-specific?

   - **Recommendation**: Start with shared prompt, customize if needed

1. Should we support custom output paths via CLI flags?

   - **Recommendation**: Phase 2 enhancement, use defaults first

## Success Criteria

- ✅ Generate module README (existing functionality preserved)
- ✅ Generate project README at repository root
- ✅ Generate style guide in docs/ directory
- ✅ Drift detection works for all doc types
- ✅ All existing tests pass
- ✅ New tests cover each doc type
- ✅ CLI supports --doc-type flag
- ✅ No breaking changes to existing API
- ✅ Code remains readable with clear separation of concerns
