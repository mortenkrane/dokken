"""Integration tests for dokken CLI commands.

These tests exercise the full command flow with only the LLM mocked.
All other modules (code analyzer, config, formatters, etc.) are kept intact.
"""

from pathlib import Path

from click.testing import CliRunner
from pytest_mock import MockerFixture

from src.main import cli
from src.records import DocumentationDriftCheck, ModuleDocumentation


def test_integration_generate_documentation(
    tmp_path: Path, mocker: MockerFixture
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

    # Create sample Python files
    (module_dir / "__init__.py").write_text('"""Payment service module."""\n')
    (module_dir / "processor.py").write_text('''"""Payment processor."""


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
''')

    # Mock the LLM initialization and program
    mock_llm_client = mocker.MagicMock()
    mocker.patch("src.workflows.initialize_llm", return_value=mock_llm_client)
    mocker.patch("src.llm.initialize_llm", return_value=mock_llm_client)

    # Mock the LLM program to return realistic structured output
    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()

    # Setup mock to return drift detection (drift detected since no doc exists)
    # followed by generated documentation
    drift_check = DocumentationDriftCheck(
        drift_detected=True,
        rationale="No existing documentation provided.",
    )

    generated_doc = ModuleDocumentation(
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

    # Configure mock to return different values on successive calls
    mock_program.side_effect = [drift_check, generated_doc]
    mock_program_class.from_defaults.return_value = mock_program

    # Mock console to suppress output during tests
    mocker.patch("src.main.console")
    mocker.patch("src.workflows.console")

    # Mock human intent capture (return None to skip)
    mocker.patch("src.workflows.ask_human_intent", return_value=None)

    # Run the generate command
    runner = CliRunner()
    result = runner.invoke(cli, ["generate", str(module_dir)])

    # Assert command succeeded
    assert result.exit_code == 0, f"Command failed with: {result.output}"

    # Assert README.md was created
    readme_path = module_dir / "README.md"
    assert readme_path.exists(), "README.md was not created"

    # Assert README contains expected content from the generated documentation
    readme_content = readme_path.read_text()
    assert "Payment Service" in readme_content
    assert "payment processing operations" in readme_content
    assert "process_payment()" in readme_content
    assert "validate_payment()" in readme_content
    assert "Dictionary-based return values" in readme_content

    # Verify the LLM was called twice (drift check + doc generation)
    assert mock_program.call_count == 2


def test_integration_check_documentation_drift(
    tmp_path: Path, mocker: MockerFixture
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

    # Create sample Python files
    (module_dir / "__init__.py").write_text('"""Authentication service."""\n')
    (module_dir / "auth.py").write_text('''"""Authentication handlers."""


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
''')

    # Create existing README (with some drift)
    readme_path = module_dir / "README.md"
    readme_path.write_text("""# Authentication Service

This service handles user authentication.

## Main Functions

- `authenticate_user()` - Authenticates users
- `create_session()` - Creates user sessions (OUTDATED - this function was removed)

## Dependencies

- JWT library
""")

    # Mock the LLM initialization and program
    mock_llm_client = mocker.MagicMock()
    mocker.patch("src.workflows.initialize_llm", return_value=mock_llm_client)
    mocker.patch("src.llm.initialize_llm", return_value=mock_llm_client)

    # Mock the LLM program to detect drift
    mock_program_class = mocker.patch("src.llm.LLMTextCompletionProgram")
    mock_program = mocker.MagicMock()

    drift_check = DocumentationDriftCheck(
        drift_detected=True,
        rationale=(
            "Documentation references removed function 'create_session()'. "
            "New function 'generate_token()' is not documented. "
            "Missing details about password validation requirements."
        ),
    )

    mock_program.return_value = drift_check
    mock_program_class.from_defaults.return_value = mock_program

    # Mock console to suppress output during tests
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
