"""Integration tests for dokken CLI commands.

These tests exercise the full command flow with only the LLM mocked.
All other modules (code analyzer, config, formatters, etc.) are kept intact.
"""

from pathlib import Path

import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from src.main import cli
from src.records import (
    DocumentationChange,
    DocumentationDriftCheck,
    IncrementalDocumentationFix,
    ModuleDocumentation,
)

# --- Test Data Constants ---

# Payment service example code
PAYMENT_SERVICE_INIT = '"""Payment service module."""\n'

PAYMENT_PROCESSOR_CODE = '''"""Payment processor."""


def process_payment(amount: float, currency: str) -> dict:
    """Process a payment transaction.

    Args:
        amount: Payment amount
        currency: Currency code (USD, EUR, etc.)

    Returns:
        Transaction result dictionary
    """
    return {"status": "success", "amount": amount, "currency": currency}


def validate_payment(amount: float) -> bool:
    """Validate payment amount."""
    return amount > 0
'''

# Auth service example code
AUTH_SERVICE_INIT = '"""Authentication service."""\n'

AUTH_SERVICE_CODE = '''"""Authentication handlers."""


def authenticate_user(username: str, password: str) -> bool:
    """Authenticate a user with username and password.

    Args:
        username: User's username
        password: User's password

    Returns:
        True if authentication successful, False otherwise
    """
    # Simplified auth logic for testing
    return len(username) > 0 and len(password) >= 8


def generate_token(user_id: int) -> str:
    """Generate an authentication token.

    Args:
        user_id: ID of the authenticated user

    Returns:
        JWT token string
    """
    return f"token_{user_id}"
'''

# Existing documentation with drift
AUTH_SERVICE_OUTDATED_README = """# Authentication Service

This service handles user authentication.

## Main Functions

- `authenticate_user()` - Authenticates users
- `create_session()` - Creates user sessions (OUTDATED - this function was removed)

## Dependencies

- JWT library
"""

# --- Test Fixtures ---


@pytest.fixture
def payment_service_drift_check() -> DocumentationDriftCheck:
    """Drift check result for payment service (no existing docs)."""
    return DocumentationDriftCheck(
        drift_detected=True,
        rationale="No existing documentation provided.",
    )


@pytest.fixture
def payment_service_generated_doc() -> ModuleDocumentation:
    """Generated documentation for payment service."""
    return ModuleDocumentation(
        component_name="Payment Service",
        purpose_and_scope=(
            "This module handles payment processing operations including "
            "transaction processing and payment validation."
        ),
        architecture_overview=(
            "The payment service consists of a processor module that handles "
            "the core payment operations. Transactions are validated before "
            "processing to ensure data integrity."
        ),
        main_entry_points=(
            "The primary entry point is `process_payment()` which accepts "
            "payment details and returns transaction results. Use `validate_payment()` "
            "to pre-validate amounts."
        ),
        control_flow=(
            "Payment requests are validated first, then processed through the "
            "processor module. Results are returned as dictionaries containing "
            "transaction status and details."
        ),
        key_design_decisions=(
            "Dictionary-based return values provide flexibility for different payment "
            "types. Currency codes follow ISO 4217 standard. Validation is separated "
            "from processing for reusability."
        ),
        external_dependencies="None",
    )


@pytest.fixture
def auth_service_drift_check() -> DocumentationDriftCheck:
    """Drift check result for auth service (outdated docs)."""
    return DocumentationDriftCheck(
        drift_detected=True,
        rationale=(
            "Documentation references removed function 'create_session()'. "
            "New function 'generate_token()' is not documented. "
            "Missing details about password validation requirements."
        ),
    )


# --- Integration Tests ---


def test_integration_generate_documentation(
    tmp_path: Path,
    mocker: MockerFixture,
    payment_service_drift_check: DocumentationDriftCheck,
    payment_service_generated_doc: ModuleDocumentation,
) -> None:
    """
    Integration test for doc generation command.

    Tests the full flow of 'dokken generate' with a realistic module structure.
    Only the LLM is mocked; all other components (code analyzer, formatters, etc.)
    are used as-is.
    """
    # Create a realistic module structure
    module_dir = tmp_path / "payment_service"
    module_dir.mkdir()
    (module_dir / "__init__.py").write_text(PAYMENT_SERVICE_INIT)
    (module_dir / "processor.py").write_text(PAYMENT_PROCESSOR_CODE)

    # Mock the LLM initialization and program
    mock_llm_client = mocker.MagicMock()
    mocker.patch("src.workflows.initialize_llm", return_value=mock_llm_client)
    mocker.patch("src.llm.initialize_llm", return_value=mock_llm_client)

    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.side_effect = [
        payment_service_drift_check,
        payment_service_generated_doc,
    ]
    mock_program_class.from_defaults.return_value = mock_program

    # Mock console and human intent
    mocker.patch("src.main.console")
    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.ask_human_intent", return_value=None)

    # Run the generate command
    runner = CliRunner()
    result = runner.invoke(cli, ["generate", str(module_dir)])

    # Assert command succeeded
    assert result.exit_code == 0, f"Command failed with: {result.output}"

    # Assert README.md was created with expected content
    readme_path = module_dir / "README.md"
    assert readme_path.exists(), "README.md was not created"

    readme_content = readme_path.read_text()
    assert "Payment Service" in readme_content
    assert "payment processing operations" in readme_content
    assert "process_payment()" in readme_content
    assert "validate_payment()" in readme_content
    assert "Dictionary-based return values" in readme_content

    # Verify the LLM was called twice (drift check + doc generation)
    assert mock_program.call_count == 2


def test_integration_check_documentation_drift(
    tmp_path: Path,
    mocker: MockerFixture,
    auth_service_drift_check: DocumentationDriftCheck,
) -> None:
    """
    Integration test for drift detection command.

    Tests the full flow of 'dokken check' with a realistic module structure.
    Only the LLM is mocked; all other components (code analyzer, formatters, etc.)
    are used as-is.
    """
    # Create a realistic module structure
    module_dir = tmp_path / "auth_service"
    module_dir.mkdir()
    (module_dir / "__init__.py").write_text(AUTH_SERVICE_INIT)
    (module_dir / "auth.py").write_text(AUTH_SERVICE_CODE)

    # Create existing README with drift
    readme_path = module_dir / "README.md"
    readme_path.write_text(AUTH_SERVICE_OUTDATED_README)

    # Mock the LLM initialization and program
    mock_llm_client = mocker.MagicMock()
    mocker.patch("src.workflows.initialize_llm", return_value=mock_llm_client)
    mocker.patch("src.llm.initialize_llm", return_value=mock_llm_client)

    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = auth_service_drift_check
    mock_program_class.from_defaults.return_value = mock_program

    # Mock console
    mocker.patch("src.main.console")
    mocker.patch("src.workflows.console")

    # Run the check command (without --fix)
    runner = CliRunner()
    result = runner.invoke(cli, ["check", str(module_dir)])

    # Assert command failed (exit code 1) due to drift detection
    assert result.exit_code == 1, "Command should fail when drift is detected"

    # README should remain unchanged (no --fix flag)
    original_content = readme_path.read_text()
    assert "create_session()" in original_content  # Outdated reference still there
    assert "generate_token()" not in original_content  # New function not added

    # Verify the LLM was called once for drift check
    assert mock_program.call_count == 1

    # Verify drift check was called with the code context and existing docs
    call_args = mock_program.call_args
    assert call_args is not None
    assert "context" in call_args.kwargs
    assert "current_doc" in call_args.kwargs

    # Verify code context includes the actual Python code
    context = call_args.kwargs["context"]
    assert "authenticate_user" in context
    assert "generate_token" in context

    # Verify current doc includes the existing README
    current_doc = call_args.kwargs["current_doc"]
    assert "Authentication Service" in current_doc
    assert "create_session()" in current_doc


def test_integration_check_fix_workflow(tmp_path: Path, mocker: MockerFixture) -> None:
    """
    Integration test for check → fix workflow.

    Tests detecting drift, then fixing it with --fix flag.
    """
    # Create module with outdated docs
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "__init__.py").write_text("")
    (module_dir / "auth.py").write_text(
        """
def authenticate(username: str, password: str) -> bool:
    '''Authenticate user.'''
    return True

def new_function():
    '''This is new and not documented.'''
    pass
"""
    )
    (module_dir / "README.md").write_text(
        """# Auth Module

## Main Functions
- authenticate() - Authenticates users
"""
    )

    # Mock LLM
    mock_llm_client = mocker.MagicMock()
    mocker.patch("src.workflows.initialize_llm", return_value=mock_llm_client)

    # First call: detect drift
    drift_check = DocumentationDriftCheck(
        drift_detected=True,
        rationale="new_function is not documented",
    )

    # Second call: generate fix
    fix = IncrementalDocumentationFix(
        changes=[
            DocumentationChange(
                section="Main Functions",
                change_type="update",
                updated_content=(
                    "- authenticate() - Authenticates users\n"
                    "- new_function() - New functionality"
                ),
                rationale="Added new_function",
            )
        ],
        summary="Added new_function to documentation",
        preserved_sections=["Auth Module"],
    )

    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.side_effect = [drift_check, fix]
    mock_program_class.from_defaults.return_value = mock_program

    # Mock console
    mocker.patch("src.main.console")
    mocker.patch("src.workflows.console")

    # Run check with --fix
    runner = CliRunner()
    result = runner.invoke(cli, ["check", str(module_dir), "--fix"])

    # Should succeed
    assert result.exit_code == 0

    # README should be updated
    updated_readme = (module_dir / "README.md").read_text()
    assert "new_function" in updated_readme


def test_integration_cache_persistence(tmp_path: Path, mocker: MockerFixture) -> None:
    """
    Integration test for cache persistence across runs.

    Tests that drift check results are cached and reused.
    """
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "__init__.py").write_text("")
    (module_dir / "code.py").write_text("def func(): pass")
    (module_dir / "README.md").write_text("# Module\nDocs here")

    # Mock LLM
    mock_llm_client = mocker.MagicMock()
    mocker.patch("src.workflows.initialize_llm", return_value=mock_llm_client)

    drift_check = DocumentationDriftCheck(drift_detected=False, rationale="Up to date")

    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()
    mock_program.return_value = drift_check
    mock_program_class.from_defaults.return_value = mock_program

    # Mock console
    mocker.patch("src.main.console")
    mocker.patch("src.workflows.console")

    # First run
    runner = CliRunner()
    result1 = runner.invoke(cli, ["check", str(module_dir)])
    assert result1.exit_code == 0

    # LLM should have been called once
    first_call_count = mock_program.call_count
    assert first_call_count == 1

    # Second run with same code (cache should be used)
    result2 = runner.invoke(cli, ["check", str(module_dir)])
    assert result2.exit_code == 0

    # LLM should not be called again (cache hit)
    second_call_count = mock_program.call_count
    assert second_call_count == first_call_count  # No new calls
