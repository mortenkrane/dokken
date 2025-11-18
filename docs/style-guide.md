# Style guide for Dokken

## Project structure

Dokken follows a clean separation of concerns architecture, with each module having a single, well-defined responsibility.

### Overview

```
src/
├── __init__.py          # Package initialization
├── main.py              # CLI entry points (Click commands)
├── exceptions.py        # Custom exceptions
├── prompts.py          # LLM prompt templates as constants
├── git.py              # Git operations
├── code_analyzer.py    # Code context extraction
├── llm.py              # LLM client initialization and operations
├── formatters.py       # Documentation formatting (Markdown, etc.)
├── workflows.py        # High-level orchestration logic
└── records.py          # Pydantic models for structured data
```

### Module Responsibilities

#### `main.py` - CLI Entry Points
- Contains **only** the Click-based CLI interface
- Delegates all business logic to `workflows.py`
- Handles user-facing output with Rich console
- Should remain thin - just UI concerns

**Example:**
```python
@cli.command()
def check(module_path: str):
    # Just CLI glue - delegates to workflows
    check_documentation_drift(target_module_path=module_path)
```

#### `exceptions.py` - Custom Exceptions
- All custom exception classes
- Currently contains `DocumentationDriftError`
- Add new exceptions here as needed

#### `prompts.py` - LLM Prompt Templates
- **All LLM prompts as module-level constants**
- Easy to iterate on prompts without touching logic
- Version control tracks prompt changes clearly
- Makes A/B testing prompts straightforward

**Example:**
```python
DRIFT_CHECK_PROMPT = """You are a Documentation Drift Detector..."""
```

**Why separate prompts?**
- Prompts are the most frequently tweaked part of LLM applications
- Keeping them as constants makes experimentation faster
- Changes are visible in git diffs
- Can add prompt variants easily

#### `git.py` - Git Operations
- Pure git functionality
- Uses `subprocess` to interact with git
- No LLM or file I/O mixing
- Single responsibility: git workflow automation

**Contains:**
- `setup_git()` - Checks out main, pulls, creates branch

#### `code_analyzer.py` - Code Context Extraction
- Analyzes code to create context for LLM
- Reads Python files and git diffs
- Pure extraction logic, no LLM calls
- Could be extended to support other languages

**Contains:**
- `get_module_context()` - Extracts code + diffs from a module

#### `llm.py` - LLM Client and Operations
- LLM initialization and configuration
- Direct LLM interaction functions
- Uses prompts from `prompts.py`
- Returns structured Pydantic objects

**Contains:**
- `initialize_llm()` - Sets up Google GenAI client
- `check_drift()` - Checks documentation drift via LLM
- `generate_doc()` - Generates structured documentation via LLM

#### `formatters.py` - Output Formatting
- Pure data transformation, no I/O
- Converts structured data to various formats
- Currently: Markdown formatting
- Future: Could add HTML, PDF, etc.

**Contains:**
- `generate_markdown()` - Converts `ComponentDocumentation` to Markdown

#### `workflows.py` - Orchestration Logic
- **High-level business logic**
- Coordinates git → analyzer → LLM → formatter
- Contains the full flow of operations
- Can be imported and used without CLI

**Contains:**
- `check_documentation_drift()` - Full drift check workflow
- `generate_documentation()` - Full doc generation workflow

**Why separate workflows?**
- Reusable - can be imported by other scripts
- Testable - can be tested without CLI
- Clear business logic separated from UI

#### `records.py` - Data Models
- Pydantic models for structured data
- Defines the "shape" of our data
- Used by LLM for structured output
- Type-safe data validation

**Contains:**
- `DocumentationDriftCheck` - Drift detection results
- `ComponentDocumentation` - Generated documentation structure

### Dependency Flow

```
main.py (CLI)
    └── workflows.py (Orchestration)
            ├── git.py
            ├── code_analyzer.py
            ├── llm.py
            │   ├── prompts.py
            │   └── records.py
            ├── formatters.py
            │   └── records.py
            └── exceptions.py
```

### Adding New Features

**Adding a new prompt:**
1. Add constant to `prompts.py`
2. Use it in `llm.py`

**Adding a new LLM operation:**
1. Add prompt to `prompts.py`
2. Add function to `llm.py`
3. Use it in `workflows.py`

**Adding a new output format:**
1. Add formatter function to `formatters.py`
2. Call it from `workflows.py`

**Adding a new CLI command:**
1. Add `@cli.command()` to `main.py`
2. Optionally add new workflow to `workflows.py`

## Code Style

### General Python Style

- Follow PEP 8 guidelines
- Use Ruff for code formatting and linting
    - Run `ruff format` to format code
    - Run `ruff check` to check for linting issues
    - Run `ruff check --fix` to automatically fix linting issues
- Use type hints consistently throughout the codebase, use MyPy for type checking
- Use absolute imports
- Keep imports at the top of the file, unless we need to break circular imports
- Use double quotes for strings
- Keep functions simple and bite-sized
    - If Ruff says your function is "too complex", it probably is, and should be refactored
- Keep files from growing indefinitely
    - We define no max limit, but it's recommended to start looking for potential dividers when files reach 800-1000 lines
    - Typically, the solution will be to convert a big file into a directory with subfiles


## Testing

## Documentation