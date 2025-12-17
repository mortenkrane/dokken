"""Shared fixtures for Dokken tests."""

from pathlib import Path
from typing import Any

import pytest
from pytest_mock import MockerFixture

from src.records import ComponentDocumentation, DocumentationDriftCheck


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
def sample_component_documentation() -> ComponentDocumentation:
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
