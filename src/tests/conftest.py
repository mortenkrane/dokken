"""Shared fixtures for Dokken tests."""

import pytest

from src.records import ComponentDocumentation, DocumentationDriftCheck


@pytest.fixture
def sample_readme_content():
    """Sample README content for testing."""
    return """# Sample Component Overview

## Purpose & Scope

This is a sample component for testing purposes.

## External Dependencies

- dependency1
- dependency2

## Key Design Decisions (The 'Why')

### Decision: DB_CHOICE

We chose MongoDB for flexibility.

### Decision: CACHE_STRATEGY

We use Redis for caching.
"""


@pytest.fixture
def sample_code_content():
    """Sample Python code for testing."""
    return '''def hello_world():
    """Print hello world."""
    print("Hello, World!")


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
'''


@pytest.fixture
def sample_git_diff():
    """Sample git diff output."""
    diff_text = (
        "diff --git a/src/sample.py b/src/sample.py\n"
        "index 123abc..456def 100644\n"
        "--- a/src/sample.py\n"
        "+++ b/src/sample.py\n"
        "@@ -1,3 +1,7 @@\n"
        " def hello_world():\n"
        '-    print("Hello, World!")\n'
        '+    """Print hello world."""\n'
        '+    print("Hello, World!")\n'
        "+\n"
        "+def add(a: int, b: int) -> int:\n"
        '+    """Add two numbers."""\n'
        "+    return a + b\n"
    )
    return diff_text


@pytest.fixture
def sample_module_context(sample_code_content, sample_git_diff):
    """Sample module context for LLM."""
    return f"""--- MODULE PATH: src/sample ---

--- FILE: src/sample.py ---
--- CURRENT CODE CONTENT ---
{sample_code_content}
--- CODE CHANGES (GIT DIFF vs. main) ---
{sample_git_diff}

"""


@pytest.fixture
def sample_drift_check_no_drift():
    """Sample DocumentationDriftCheck with no drift."""
    return DocumentationDriftCheck(
        drift_detected=False,
        rationale="Documentation is up-to-date with the current code.",
    )


@pytest.fixture
def sample_drift_check_with_drift():
    """Sample DocumentationDriftCheck with drift detected."""
    return DocumentationDriftCheck(
        drift_detected=True,
        rationale="New functions were added but documentation was not updated.",
    )


@pytest.fixture
def sample_component_documentation():
    """Sample ComponentDocumentation."""
    return ComponentDocumentation(
        component_name="Sample Component",
        purpose_and_scope="This component handles sample operations for testing.",
        design_decisions={
            "DB_CHOICE": "We chose MongoDB over SQL for flexible schema management.",
            "CACHE_STRATEGY": "We use Redis for caching to improve performance.",
        },
        external_dependencies="Redis, MongoDB",
    )


@pytest.fixture
def temp_module_dir(tmp_path):
    """Create a temporary module directory with Python files."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    # Create a sample Python file
    sample_file = module_dir / "sample.py"
    sample_file.write_text('''def hello():
    """Say hello."""
    return "Hello"
''')

    return module_dir


@pytest.fixture
def temp_readme(tmp_path):
    """Create a temporary README.md file."""
    readme_path = tmp_path / "README.md"
    readme_path.write_text("""# Test Component

## Purpose & Scope

Test documentation.
""")
    return readme_path


@pytest.fixture
def mock_llm_client(mocker):
    """Mock LLM client."""
    mock_client = mocker.MagicMock()
    mock_client.model = "gemini-2.5-flash"
    mock_client.temperature = 0.0
    return mock_client


@pytest.fixture
def mock_console(mocker):
    """Mock Rich console to suppress output during tests."""
    return mocker.patch("src.git.console")
