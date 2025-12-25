"""Shared fixtures for Dokken tests."""

from pathlib import Path
from typing import Any

import pytest
from pytest_mock import MockerFixture

from src.records import DocumentationDriftCheck, ModuleDocumentation
from src.utils import clear_drift_cache


@pytest.fixture(autouse=True)
def clear_drift_cache_before_each_test() -> None:
    """Clear drift detection cache before each test to ensure isolation."""
    clear_drift_cache()


@pytest.fixture
def sample_drift_check_no_drift() -> DocumentationDriftCheck:
    """Sample DocumentationDriftCheck with no drift."""
    return DocumentationDriftCheck(
        drift_detected=False,
        rationale="Documentation is up-to-date with the current code.",
    )


@pytest.fixture
def sample_drift_check_with_drift() -> DocumentationDriftCheck:
    """Sample DocumentationDriftCheck with drift detected."""
    return DocumentationDriftCheck(
        drift_detected=True,
        rationale="New functions were added but documentation was not updated.",
    )


@pytest.fixture
def sample_component_documentation() -> ModuleDocumentation:
    """Sample ModuleDocumentation."""
    return ModuleDocumentation(
        component_name="Sample Component",
        purpose_and_scope="This component handles sample operations for testing.",
        architecture_overview=(
            "The component consists of three main modules: data access, "
            "business logic, and API layer. Data flows from the API through "
            "validation, business rules, and finally to the database layer."
        ),
        main_entry_points=(
            "The primary entry point is `process_request()` which accepts "
            "user input and orchestrates the operation. For batch operations, "
            "use `batch_process()`."
        ),
        control_flow=(
            "Requests enter through the API layer, are validated, processed "
            "by business logic, and results are persisted to the database. "
            "Errors trigger rollback."
        ),
        key_design_decisions=(
            "We chose MongoDB over SQL for flexible schema management in the "
            "early phase. Redis was selected for caching to improve "
            "performance and reduce database load."
        ),
        external_dependencies="Redis, MongoDB",
    )


@pytest.fixture
def temp_module_dir(tmp_path: Path) -> Path:
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
def mock_llm_client(mocker: MockerFixture) -> Any:
    """Mock LLM client."""
    mock_client = mocker.MagicMock()
    mock_client.model = "gemini-2.5-flash"
    mock_client.temperature = 0.0
    return mock_client


@pytest.fixture
def mock_console(mocker: MockerFixture) -> Any:
    """Mock Rich console to suppress output during tests."""
    return mocker.patch("src.git.console")
