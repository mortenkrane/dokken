"""Tests for doc_types module."""

from src.doc_types import DocType


def test_doc_type_enum_values() -> None:
    """Test that DocType enum has expected values."""
    assert DocType.MODULE_README.value == "module-readme"
    assert DocType.PROJECT_README.value == "project-readme"
    assert DocType.STYLE_GUIDE.value == "style-guide"


def test_doc_type_enum_members() -> None:
    """Test that DocType enum has exactly three members."""
    assert len(DocType) == 3
    assert set(DocType) == {
        DocType.MODULE_README,
        DocType.PROJECT_README,
        DocType.STYLE_GUIDE,
    }


def test_doc_type_string_representation() -> None:
    """Test string representation of DocType enum members."""
    assert DocType.MODULE_README.value == "module-readme"
    assert DocType.PROJECT_README.value == "project-readme"
    assert DocType.STYLE_GUIDE.value == "style-guide"


def test_doc_type_enum_iteration() -> None:
    """Test that we can iterate over DocType enum."""
    doc_types = list(DocType)
    assert len(doc_types) == 3
    assert DocType.MODULE_README in doc_types
    assert DocType.PROJECT_README in doc_types
    assert DocType.STYLE_GUIDE in doc_types


def test_doc_type_enum_comparison() -> None:
    """Test that DocType enum members can be compared."""
    assert DocType.MODULE_README == DocType.MODULE_README
    assert DocType.MODULE_README != DocType.PROJECT_README
    assert DocType.PROJECT_README != DocType.STYLE_GUIDE


def test_doc_type_enum_membership() -> None:
    """Test that DocType enum membership checks work."""
    assert DocType.MODULE_README in DocType
    assert DocType.PROJECT_README in DocType
    assert DocType.STYLE_GUIDE in DocType
