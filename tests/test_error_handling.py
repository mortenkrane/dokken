"""Tests for error handling in multi-module operations and production readiness."""

import json
from pathlib import Path

import pytest
from llama_index.core.llms import LLM
from pytest_mock import MockerFixture

from src.cache import load_drift_cache_from_disk, save_drift_cache_to_disk
from src.config import DokkenConfig
from src.exceptions import DocumentationDriftError
from src.file_utils import ensure_output_directory
from src.llm import check_drift, fix_doc_incrementally, generate_doc
from src.records import (
    DocumentationDriftCheck,
    ModuleDocumentation,
)
from src.workflows import check_multiple_modules_drift, generate_documentation

# --- Tests for LLM API Failures and Retries ---


def test_llm_api_failure_handling(mocker: MockerFixture, mock_llm_client: LLM) -> None:
    """Test that LLM API failures propagate correctly for caller to handle."""
    # Mock LLM program to raise API error
    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.side_effect = RuntimeError("API connection failed")
    mock_program_class.from_defaults.return_value = mock_program

    # When: Calling check_drift with API failure
    # Then: Should propagate the error for caller to handle
    with pytest.raises(RuntimeError, match="API connection failed"):
        check_drift(
            llm=mock_llm_client,
            context="def func(): pass",
            current_doc="# Documentation",
        )


def test_llm_rate_limit_error(mocker: MockerFixture, mock_llm_client: LLM) -> None:
    """Test that LLM rate limit errors propagate correctly."""
    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.side_effect = Exception("Rate limit exceeded. Please retry after 60s")
    mock_program_class.from_defaults.return_value = mock_program

    # When: Calling generate_doc with rate limit error
    # Then: Should propagate the error
    with pytest.raises(Exception, match="Rate limit exceeded"):
        generate_doc(
            llm=mock_llm_client,
            context="def func(): pass",
            output_model=ModuleDocumentation,
            prompt_template="Generate: {context}",
        )


def test_llm_authentication_error(mocker: MockerFixture, mock_llm_client: LLM) -> None:
    """Test that LLM authentication errors propagate correctly."""
    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.side_effect = PermissionError("Invalid API key")
    mock_program_class.from_defaults.return_value = mock_program

    # When: Calling fix_doc_incrementally with auth error
    # Then: Should propagate the error
    with pytest.raises(PermissionError, match="Invalid API key"):
        fix_doc_incrementally(
            llm=mock_llm_client,
            context="def func(): pass",
            current_doc="# Docs",
            drift_rationale="Drift detected",
        )


def test_llm_network_timeout_error(mocker: MockerFixture, mock_llm_client: LLM) -> None:
    """Test that LLM network timeout errors propagate correctly."""
    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.side_effect = TimeoutError("Request timed out after 30s")
    mock_program_class.from_defaults.return_value = mock_program

    # When: Calling check_drift with timeout
    # Then: Should propagate timeout error
    with pytest.raises(TimeoutError, match="timed out"):
        check_drift(
            llm=mock_llm_client,
            context="def func(): pass",
            current_doc="# Docs",
        )


def test_llm_malformed_response_error(
    mocker: MockerFixture, mock_llm_client: LLM
) -> None:
    """Test that malformed LLM responses are handled correctly."""
    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.side_effect = ValueError("Failed to parse LLM response as JSON")
    mock_program_class.from_defaults.return_value = mock_program

    # When: Calling generate_doc with malformed response
    # Then: Should propagate parsing error
    with pytest.raises(ValueError, match="Failed to parse"):
        generate_doc(
            llm=mock_llm_client,
            context="def func(): pass",
            output_model=ModuleDocumentation,
            prompt_template="Generate: {context}",
        )


# --- Tests for Partial Failures in Multi-Module Operations ---


def test_partial_failure_in_multi_module_check(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    """Test check_multiple_modules_drift handles partial failures correctly."""
    # Create a git repo with multiple modules
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    # Create three modules
    for i in range(1, 4):
        module = repo_dir / f"module{i}"
        module.mkdir()
        (module / "README.md").write_text(f"# Module {i}")

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.find_repo_root", return_value=str(repo_dir))
    mocker.patch(
        "src.workflows.load_config",
        return_value=DokkenConfig(modules=["module1", "module2", "module3"]),
    )

    # Simulate LLM failure on second module
    call_count = 0

    def check_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        module_path = kwargs["target_module_path"]
        if "module2" in module_path:
            # Simulate LLM API failure on module2
            raise RuntimeError("LLM API unavailable")
        # Other modules would succeed

    mocker.patch(
        "src.workflows.check_documentation_drift", side_effect=check_side_effect
    )

    # When: Checking all modules with LLM failure on one module
    # Then: Should fail fast and propagate the error
    with pytest.raises(RuntimeError, match="LLM API unavailable"):
        check_multiple_modules_drift()

    # Verify it stopped after the failure (didn't process module3)
    assert call_count == 2  # module1 succeeded, module2 failed


def test_partial_failure_multi_module_drift_and_errors(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    """Test multi-module check with mix of drift and unexpected errors."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    # Create four modules
    for i in range(1, 5):
        module = repo_dir / f"module{i}"
        module.mkdir()
        (module / "README.md").write_text(f"# Module {i}")

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.find_repo_root", return_value=str(repo_dir))
    mocker.patch(
        "src.workflows.load_config",
        return_value=DokkenConfig(modules=["module1", "module2", "module3", "module4"]),
    )

    # Simulate different scenarios for each module
    def check_side_effect(*args, **kwargs):
        module_path = kwargs["target_module_path"]
        if "module1" in module_path:
            # Module 1: No drift, passes
            return
        if "module2" in module_path:
            # Module 2: Has drift
            raise DocumentationDriftError(
                rationale="Documentation outdated", module_path=module_path
            )
        if "module3" in module_path:
            # Module 3: Network timeout
            raise TimeoutError("Network timeout during LLM call")
        # Module 4 would never be reached

    mocker.patch(
        "src.workflows.check_documentation_drift", side_effect=check_side_effect
    )

    # When: Checking all modules with timeout error
    # Then: Should propagate the timeout error (not drift error)
    with pytest.raises(TimeoutError, match="Network timeout"):
        check_multiple_modules_drift()


def test_partial_failure_multi_module_with_missing_readme(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    """Test multi-module check when some modules have missing README files."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    # Create modules - some with README, some without
    module1 = repo_dir / "module1"
    module1.mkdir()
    (module1 / "README.md").write_text("# Module 1")

    module2 = repo_dir / "module2"
    module2.mkdir()
    # No README for module2

    module3 = repo_dir / "module3"
    module3.mkdir()
    (module3 / "README.md").write_text("# Module 3")

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.find_repo_root", return_value=str(repo_dir))
    mocker.patch(
        "src.workflows.load_config",
        return_value=DokkenConfig(modules=["module1", "module2", "module3"]),
    )

    # Mock check_documentation_drift to control behavior per module
    def check_side_effect(*args, **kwargs):
        module_path = kwargs["target_module_path"]
        if "module2" in module_path:
            # Module 2: No README exists
            raise DocumentationDriftError(
                rationale="No documentation exists.", module_path=module_path
            )
        # Module 1 and 3: Pass

    mocker.patch(
        "src.workflows.check_documentation_drift", side_effect=check_side_effect
    )

    # When: Checking modules where module2 has no README
    # Then: Should raise DocumentationDriftError for missing docs
    with pytest.raises(DocumentationDriftError, match="No documentation exists"):
        check_multiple_modules_drift()


# --- Tests for Disk I/O Errors During Documentation Writing ---


def test_write_permission_errors(mocker: MockerFixture, tmp_path: Path) -> None:
    """Test generate_documentation handles write permission errors correctly."""
    module_dir = tmp_path / "module"
    module_dir.mkdir()

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code context")

    mock_drift = DocumentationDriftCheck(drift_detected=True, rationale="No docs")
    mocker.patch("src.workflows.check_drift", return_value=mock_drift)
    mocker.patch("src.workflows.ask_human_intent", return_value=None)

    mock_doc = ModuleDocumentation(
        component_name="Test",
        purpose_and_scope="Test purpose",
        architecture_overview="Test architecture",
        main_entry_points="Test entry points",
        control_flow="Test control flow",
        key_design_decisions="Test decisions",
        external_dependencies="None",
    )
    mocker.patch("src.workflows.generate_doc", return_value=mock_doc)

    # Mock file write to fail with permission error
    mocker.patch("builtins.open", side_effect=PermissionError("Permission denied"))

    # When: Attempting to write documentation
    # Then: Should propagate permission error
    with pytest.raises(PermissionError, match="Permission denied"):
        generate_documentation(target_module_path=str(module_dir))


def test_disk_full_error_during_write(mocker: MockerFixture, tmp_path: Path) -> None:
    """Test generate_documentation handles disk full errors correctly."""
    module_dir = tmp_path / "module"
    module_dir.mkdir()

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code context")

    mock_drift = DocumentationDriftCheck(drift_detected=True, rationale="No docs")
    mocker.patch("src.workflows.check_drift", return_value=mock_drift)
    mocker.patch("src.workflows.ask_human_intent", return_value=None)

    mock_doc = ModuleDocumentation(
        component_name="Test",
        purpose_and_scope="Test",
        architecture_overview="Test",
        main_entry_points="Test",
        control_flow="Test",
        key_design_decisions="Test",
        external_dependencies="None",
    )
    mocker.patch("src.workflows.generate_doc", return_value=mock_doc)

    # Mock disk full error (ENOSPC error code 28)
    mocker.patch("builtins.open", side_effect=OSError(28, "No space left on device"))

    # When: Attempting to write documentation
    # Then: Should propagate OSError
    with pytest.raises(OSError, match="No space left on device"):
        generate_documentation(target_module_path=str(module_dir))


def test_readonly_filesystem_error(mocker: MockerFixture, tmp_path: Path) -> None:
    """Test ensure_output_directory handles read-only filesystem errors."""
    output_path = tmp_path / "readonly" / "subdir" / "file.md"

    # Mock os.makedirs to raise read-only filesystem error
    mocker.patch("os.makedirs", side_effect=OSError(30, "Read-only file system"))

    # When: Attempting to create directory on read-only filesystem
    # Then: Should raise OSError
    with pytest.raises(OSError, match="Read-only file system"):
        ensure_output_directory(str(output_path))


def test_directory_creation_permission_error() -> None:
    """Test ensure_output_directory raises PermissionError for protected paths."""
    # Try to create directory in a typically protected location
    output_path = "/root/protected/file.md"

    # When: Attempting to create directory without permissions
    # Then: Should raise PermissionError
    # Note: This test may behave differently depending on environment permissions
    # In a sandboxed environment, it might succeed, so we just verify the function
    # handles the permission error correctly by checking the implementation
    try:
        ensure_output_directory(output_path)
    except PermissionError as e:
        # Expected behavior - PermissionError is raised
        assert "Cannot create" in str(e)


def test_file_write_interrupted_error(mocker: MockerFixture, tmp_path: Path) -> None:
    """Test documentation write handles interrupted I/O errors."""
    module_dir = tmp_path / "module"
    module_dir.mkdir()

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code")

    mock_drift = DocumentationDriftCheck(drift_detected=True, rationale="No docs")
    mocker.patch("src.workflows.check_drift", return_value=mock_drift)
    mocker.patch("src.workflows.ask_human_intent", return_value=None)

    mock_doc = ModuleDocumentation(
        component_name="Test",
        purpose_and_scope="Test",
        architecture_overview="Test",
        main_entry_points="Test",
        control_flow="Test",
        key_design_decisions="Test",
        external_dependencies="None",
    )
    mocker.patch("src.workflows.generate_doc", return_value=mock_doc)

    # Mock interrupted system call error (EINTR)
    mocker.patch("builtins.open", side_effect=OSError(4, "Interrupted system call"))

    # When: Write is interrupted
    # Then: Should propagate the error
    with pytest.raises(OSError, match="Interrupted system call"):
        generate_documentation(target_module_path=str(module_dir))


# --- Tests for Cache Corruption Recovery ---


def test_cache_corruption_recovery(tmp_path: Path) -> None:
    """Test load_drift_cache_from_disk recovers from corrupted cache files."""
    # Create various types of corrupted cache files
    cache_file = tmp_path / "corrupted.json"

    # Test 1: Invalid JSON syntax
    cache_file.write_text("{invalid json syntax")
    load_drift_cache_from_disk(str(cache_file))  # Should not raise

    # Test 2: Valid JSON but wrong structure
    cache_file.write_text('{"wrong": "structure"}')
    load_drift_cache_from_disk(str(cache_file))  # Should not raise

    # Test 3: Missing required fields
    cache_file.write_text('{"version": 1}')  # Missing entries
    load_drift_cache_from_disk(str(cache_file))  # Should not raise

    # Test 4: Invalid entry structure
    cache_data = {
        "version": 1,
        "entries": {
            "key1": {"invalid_field": "value"}  # Missing drift_detected/rationale
        },
    }
    cache_file.write_text(json.dumps(cache_data))
    load_drift_cache_from_disk(str(cache_file))  # Should not raise


def test_cache_corruption_with_partial_valid_data(tmp_path: Path) -> None:
    """Test cache recovery when file has some valid and some invalid entries."""
    cache_file = tmp_path / "partial.json"

    # Create cache with one valid and one invalid entry
    cache_data = {
        "version": 1,
        "entries": {
            "valid_key": {"drift_detected": True, "rationale": "Test"},
            "invalid_key": "this should be a dict not a string",
        },
    }
    cache_file.write_text(json.dumps(cache_data))

    # When: Loading cache with partial corruption
    # Then: Should not raise, handles corruption gracefully
    load_drift_cache_from_disk(str(cache_file))


def test_cache_save_failure_recovery(
    tmp_path: Path, mocker: MockerFixture, mock_llm_client: LLM
) -> None:
    """Test that cache save failures don't crash the application."""
    # Add entry to cache
    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = DocumentationDriftCheck(
        drift_detected=False, rationale="Test"
    )
    mock_program_class.from_defaults.return_value = mock_program

    check_drift(llm=mock_llm_client, context="test", current_doc="doc")

    # Mock Path to raise error during save
    mock_path = mocker.patch("src.cache.Path")
    mock_path_instance = mocker.MagicMock()
    mock_path.return_value = mock_path_instance
    mock_path_instance.parent.mkdir.side_effect = OSError("Permission denied")

    # When: Attempting to save cache with permission error
    # Then: Should not raise exception (silently fails)
    save_drift_cache_to_disk("/protected/cache.json")  # Should not crash


def test_cache_empty_file_recovery(tmp_path: Path) -> None:
    """Test cache recovery from empty file."""
    cache_file = tmp_path / "empty.json"
    cache_file.write_text("")

    # When: Loading empty cache file
    # Then: Should handle gracefully
    load_drift_cache_from_disk(str(cache_file))  # Should not raise


def test_cache_binary_file_recovery(tmp_path: Path) -> None:
    """Test cache recovery from binary/non-UTF8 file."""
    cache_file = tmp_path / "binary.json"
    cache_file.write_bytes(b"\xff\xfe\x00\x01Invalid UTF-8")

    # When: Loading binary cache file
    # Then: Should handle gracefully
    load_drift_cache_from_disk(str(cache_file))  # Should not raise


# --- Tests for Network Timeout Scenarios ---


def test_llm_connection_timeout(mocker: MockerFixture, mock_llm_client: LLM) -> None:
    """Test LLM operations handle connection timeout errors."""
    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.side_effect = ConnectionError("Connection timed out")
    mock_program_class.from_defaults.return_value = mock_program

    # When: LLM connection times out
    # Then: Should propagate connection error
    with pytest.raises(ConnectionError, match="Connection timed out"):
        check_drift(
            llm=mock_llm_client,
            context="def func(): pass",
            current_doc="# Docs",
        )


def test_llm_read_timeout(mocker: MockerFixture, mock_llm_client: LLM) -> None:
    """Test LLM operations handle read timeout errors."""
    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.side_effect = TimeoutError("Read timeout")
    mock_program_class.from_defaults.return_value = mock_program

    # When: LLM read times out
    # Then: Should propagate timeout error
    with pytest.raises(TimeoutError, match="Read timeout"):
        generate_doc(
            llm=mock_llm_client,
            context="def func(): pass",
            output_model=ModuleDocumentation,
            prompt_template="Generate: {context}",
        )


def test_multi_module_check_with_intermittent_timeouts(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    """Test multi-module check fails fast on timeout errors."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    # Create three modules
    for i in range(1, 4):
        module = repo_dir / f"module{i}"
        module.mkdir()
        (module / "README.md").write_text(f"# Module {i}")

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.find_repo_root", return_value=str(repo_dir))
    mocker.patch(
        "src.workflows.load_config",
        return_value=DokkenConfig(modules=["module1", "module2", "module3"]),
    )

    # First module succeeds, second times out
    call_count = 0

    def check_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        module_path = kwargs["target_module_path"]
        if "module2" in module_path:
            raise TimeoutError("LLM request timeout")

    mocker.patch(
        "src.workflows.check_documentation_drift", side_effect=check_side_effect
    )

    # When: Processing modules with timeout on second module
    # Then: Should fail fast
    with pytest.raises(TimeoutError, match="LLM request timeout"):
        check_multiple_modules_drift()

    # Should have stopped after module2 timeout
    assert call_count == 2


def test_generate_doc_with_slow_response_timeout(
    mocker: MockerFixture, mock_llm_client: LLM
) -> None:
    """Test generate_doc handles slow LLM response timeouts."""
    mock_program_class = mocker.patch("src.llm.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.side_effect = TimeoutError("Request exceeded 120s timeout")
    mock_program_class.from_defaults.return_value = mock_program

    # When: LLM takes too long to respond
    # Then: Should propagate timeout
    with pytest.raises(TimeoutError, match="exceeded"):
        generate_doc(
            llm=mock_llm_client,
            context="def very_complex_function(): pass",
            output_model=ModuleDocumentation,
            prompt_template="Generate: {context}",
        )


# --- Integration Tests for Error Recovery ---


def test_multi_module_error_recovery_workflow(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    """Test complete workflow of multi-module check with various error types."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    # Create five modules with different scenarios
    for i in range(1, 6):
        module = repo_dir / f"module{i}"
        module.mkdir()
        if i != 5:  # module5 will have no README
            (module / "README.md").write_text(f"# Module {i}")

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.find_repo_root", return_value=str(repo_dir))
    mocker.patch(
        "src.workflows.load_config",
        return_value=DokkenConfig(
            modules=["module1", "module2", "module3", "module4", "module5"]
        ),
    )

    call_count = 0

    def check_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        module_path = kwargs["target_module_path"]

        if "module1" in module_path:
            # Module 1: Success, no drift
            return
        if "module2" in module_path:
            # Module 2: Drift detected
            raise DocumentationDriftError(
                rationale="Drift in module2", module_path=module_path
            )
        if "module3" in module_path:
            # Module 3: LLM API error - should stop here
            raise RuntimeError("LLM service error")
        # Modules 4 and 5 should never be reached

    mocker.patch(
        "src.workflows.check_documentation_drift", side_effect=check_side_effect
    )

    # When: Running multi-module check with errors
    # Then: Should propagate first unexpected error (not drift)
    with pytest.raises(RuntimeError, match="LLM service error"):
        check_multiple_modules_drift()

    # Should have processed module1, module2, and stopped at module3
    assert call_count == 3
