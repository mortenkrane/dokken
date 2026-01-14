"""Tests for src/exceptions.py"""

import pytest

from src.exceptions import DocumentationDriftError


def test_documentation_drift_error() -> None:
    """Smoke test that DocumentationDriftError works as expected."""
    rationale = "New functions added without documentation"
    module_path = "src/payment"

    # Test initialization and attributes
    error = DocumentationDriftError(rationale=rationale, module_path=module_path)
    assert error.rationale == rationale
    assert error.module_path == module_path

    # Test string representation
    error_str = str(error)
    assert module_path in error_str
    assert rationale in error_str

    # Test it can be raised and caught
    with pytest.raises(DocumentationDriftError) as exc_info:
        raise DocumentationDriftError(rationale=rationale, module_path=module_path)

    assert exc_info.value.rationale == rationale
    assert exc_info.value.module_path == module_path
