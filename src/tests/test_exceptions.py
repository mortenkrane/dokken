"""Tests for src/exceptions.py"""

import pytest

from src.exceptions import DocumentationDriftError


def test_documentation_drift_error_initialization() -> None:
    """Test DocumentationDriftError initialization with rationale and module_path."""
    rationale = "Documentation is outdated"
    module_path = "src/test_module"

    error = DocumentationDriftError(rationale=rationale, module_path=module_path)

    assert error.rationale == rationale
    assert error.module_path == module_path


def test_documentation_drift_error_message() -> None:
    """Test DocumentationDriftError generates correct error message."""
    rationale = "New functions added without docs"
    module_path = "src/payment"

    error = DocumentationDriftError(rationale=rationale, module_path=module_path)

    expected_message = f"Documentation drift detected in {module_path}:\n{rationale}"
    assert str(error) == expected_message


@pytest.mark.parametrize(
    "rationale,module_path",
    [
        ("No docs found", "src/module1"),
        ("Outdated API", "src/module2"),
        ("Missing dependencies", "src/module3"),
    ],
)
def test_documentation_drift_error_various_inputs(
    rationale: str, module_path: str
) -> None:
    """Test DocumentationDriftError with various rationale and module_path combinations."""
    error = DocumentationDriftError(rationale=rationale, module_path=module_path)

    assert error.rationale == rationale
    assert error.module_path == module_path
    assert module_path in str(error)
    assert rationale in str(error)


def test_documentation_drift_error_is_exception() -> None:
    """Test that DocumentationDriftError is a proper Exception."""
    error = DocumentationDriftError(rationale="test", module_path="test/path")

    assert isinstance(error, Exception)


def test_documentation_drift_error_can_be_raised() -> None:
    """Test that DocumentationDriftError can be raised and caught."""
    rationale = "Test error"
    module_path = "test/module"

    with pytest.raises(DocumentationDriftError) as exc_info:
        raise DocumentationDriftError(rationale=rationale, module_path=module_path)

    assert exc_info.value.rationale == rationale
    assert exc_info.value.module_path == module_path
