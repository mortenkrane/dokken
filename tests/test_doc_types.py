"""Tests for doc_types module."""

from src.doctypes import DocType


def test_doc_type_enum() -> None:
    """Smoke test that DocType enum has expected members and values."""
    # Check all expected members exist
    assert len(DocType) == 3
    assert DocType.MODULE_README in DocType
    assert DocType.PROJECT_README in DocType
    assert DocType.STYLE_GUIDE in DocType

    # Check values
    assert DocType.MODULE_README.value == "module-readme"
    assert DocType.PROJECT_README.value == "project-readme"
    assert DocType.STYLE_GUIDE.value == "style-guide"
