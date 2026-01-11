"""Shared fixtures for Dokken tests."""

from pathlib import Path
from typing import Any, Protocol, cast

import pytest
from llama_index.core.llms import LLM
from pytest_mock import MockerFixture

from src.cache import clear_drift_cache
from src.records import DocumentationDriftCheck, ModuleDocumentation


class MockLLMClient(Protocol):
    """Protocol for mocked LLM client.

    This protocol documents the expected interface for LLM mocks in tests.
    It includes the key attributes used by the LLM client.
    """

    model: str
    temperature: float


class MockConsoleProtocol(Protocol):
    """Protocol for mocked Rich console."""

    def print(self, *args: Any, **kwargs: Any) -> None:
        """Print method for console output."""
        ...

    def status(self, *args: Any, **kwargs: Any) -> Any:
        """Status method for console status display."""
        ...


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
def mock_llm_client(mocker: MockerFixture) -> LLM:
    """Mock LLM client with proper typing.

    Returns a MagicMock configured with model and temperature attributes
    that conforms to the LLM interface expected by the application.
    """
    mock_client = mocker.MagicMock(spec=["model", "temperature"])
    mock_client.model = "gemini-2.5-flash"
    mock_client.temperature = 0.0
    return cast(LLM, mock_client)


@pytest.fixture
def mock_console(mocker: MockerFixture) -> MockConsoleProtocol:
    """Mock Rich console to suppress output during tests."""
    # Patch all console locations
    mocker.patch("src.workflows.console")
    mocker.patch("src.code_analyzer.console")
    mocker.patch("src.human_in_the_loop.console")
    return mocker.patch("src.main.console")


@pytest.fixture
def mock_workflows_console(mocker: MockerFixture) -> MockConsoleProtocol:
    """Mock workflows console to suppress output."""
    return mocker.patch("src.workflows.console")


@pytest.fixture
def mock_main_console(mocker: MockerFixture) -> MockConsoleProtocol:
    """Mock main console to suppress output."""
    return mocker.patch("src.main.console")


@pytest.fixture
def mock_code_analyzer_console(mocker: MockerFixture) -> MockConsoleProtocol:
    """Mock code_analyzer console to suppress output."""
    return mocker.patch("src.code_analyzer.console")


@pytest.fixture
def mock_hitl_console(mocker: MockerFixture) -> MockConsoleProtocol:
    """Mock human_in_the_loop console to suppress output."""
    return mocker.patch("src.human_in_the_loop.console")


@pytest.fixture
def mock_all_consoles(mocker: MockerFixture) -> dict[str, MockConsoleProtocol]:
    """Mock all console instances across modules."""
    return {
        "workflows": mocker.patch("src.workflows.console"),
        "code_analyzer": mocker.patch("src.code_analyzer.console"),
        "human_in_the_loop": mocker.patch("src.human_in_the_loop.console"),
        "main": mocker.patch("src.main.console"),
    }


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a temporary git repository."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    return repo


@pytest.fixture
def git_repo_with_module(git_repo: Path) -> tuple[Path, Path]:
    """Create a git repo with a Python module."""
    module = git_repo / "src"
    module.mkdir()
    (module / "__init__.py").write_text("")
    (module / "main.py").write_text("def main():\n    pass\n")
    return git_repo, module
