"""Tests for src/doc_merger.py"""

import pytest
from pydantic import ValidationError

from src.output import apply_incremental_fixes, parse_sections
from src.records import DocumentationChange, IncrementalDocumentationFix

# Fixtures for test documentation strings


@pytest.fixture
def basic_doc():
    """Simple document with title and two sections."""
    return """# Title

## Section 1

Content 1

## Section 2

Content 2"""


@pytest.fixture
def doc_with_preamble():
    """Document with preamble content before first section."""
    return """# Title

Introduction paragraph.

## First Section

Content."""


@pytest.fixture
def module_doc_two_sections():
    """Module document with Purpose & Scope and Architecture sections."""
    return """# Module

## Purpose & Scope

Old purpose description.

## Architecture

Existing architecture."""


@pytest.fixture
def simple_module_doc():
    """Simple module document with one section."""
    return """# Module

## Purpose & Scope

Purpose content."""


@pytest.fixture
def module_doc_with_deprecated():
    """Module document with a deprecated section."""
    return """# Module

## Purpose & Scope

Purpose content.

## Deprecated Feature

Old feature no longer in use."""


@pytest.fixture
def module_doc_three_sections():
    """Module document with three ordered sections."""
    return """# Module

## First

Content 1

## Second

Content 2

## Third

Content 3"""


@pytest.fixture
def empty_module_doc():
    """Module document with only title, no sections."""
    return """# Module

Just a title, no sections yet."""


@pytest.fixture
def module_doc_with_all_sections():
    """Module document with multiple sections including deprecated."""
    return """# Module

## Purpose & Scope

Old purpose.

## Deprecated Section

Old stuff.

## Architecture

Old architecture."""


@pytest.fixture
def doc_with_empty_sections():
    """Document with sections that have minimal content."""
    return """# Title

## Section 1

## Section 2

Content"""


@pytest.fixture
def simple_two_section_doc():
    """Simple document with two sections for multiple changes test."""
    return """# Module

## Purpose & Scope

Old purpose.

## Architecture

Old architecture."""


def test_parse_sections_basic(basic_doc):
    """Test parsing a simple markdown document into sections."""
    sections = parse_sections(basic_doc)

    assert "Section 1" in sections
    assert "Section 2" in sections
    assert "Content 1" in sections["Section 1"]
    assert "Content 2" in sections["Section 2"]


def test_parse_sections_preserves_preamble(doc_with_preamble):
    """Test that content before first section is preserved."""
    sections = parse_sections(doc_with_preamble)

    assert "_preamble" in sections
    assert "# Title" in sections["_preamble"]
    assert "Introduction" in sections["_preamble"]


def test_apply_incremental_fixes_update(module_doc_two_sections):
    """Test updating an existing section."""
    fixes = IncrementalDocumentationFix(
        changes=[
            DocumentationChange(
                section="Purpose & Scope",
                change_type="update",
                rationale="Updated to reflect new features",
                updated_content="New purpose description with added features.",
            )
        ],
        summary="Updated purpose section",
        preserved_sections=["Architecture"],
    )

    result = apply_incremental_fixes(current_doc=module_doc_two_sections, fixes=fixes)

    assert "New purpose description" in result
    assert "Old purpose description" not in result
    assert "Existing architecture" in result  # Preserved


def test_apply_incremental_fixes_add(simple_module_doc):
    """Test adding a new section."""
    fixes = IncrementalDocumentationFix(
        changes=[
            DocumentationChange(
                section="External Dependencies",
                change_type="add",
                rationale="Added new dependency section",
                updated_content="Uses llama-index for LLM integration.",
            )
        ],
        summary="Added dependencies section",
        preserved_sections=["Purpose & Scope"],
    )

    result = apply_incremental_fixes(current_doc=simple_module_doc, fixes=fixes)

    assert "External Dependencies" in result
    assert "llama-index" in result
    assert "Purpose content" in result  # Preserved


def test_apply_incremental_fixes_remove(module_doc_with_deprecated):
    """Test removing an obsolete section."""
    fixes = IncrementalDocumentationFix(
        changes=[
            DocumentationChange(
                section="Deprecated Feature",
                change_type="remove",
                rationale="Feature was removed from codebase",
                updated_content="",
            )
        ],
        summary="Removed deprecated section",
        preserved_sections=["Purpose & Scope"],
    )

    result = apply_incremental_fixes(
        current_doc=module_doc_with_deprecated, fixes=fixes
    )

    assert "Deprecated Feature" not in result
    assert "Purpose content" in result  # Preserved


def test_apply_incremental_fixes_multiple_changes(simple_two_section_doc):
    """Test applying multiple changes at once."""
    fixes = IncrementalDocumentationFix(
        changes=[
            DocumentationChange(
                section="Purpose & Scope",
                change_type="update",
                rationale="Updated purpose",
                updated_content="New purpose.",
            ),
            DocumentationChange(
                section="Architecture",
                change_type="update",
                rationale="Updated architecture",
                updated_content="New architecture.",
            ),
        ],
        summary="Updated multiple sections",
        preserved_sections=[],
    )

    result = apply_incremental_fixes(current_doc=simple_two_section_doc, fixes=fixes)

    assert "New purpose" in result
    assert "New architecture" in result
    assert "Old purpose" not in result
    assert "Old architecture" not in result


def test_apply_incremental_fixes_empty_changes_raises_validation_error():
    """Test that empty changes list is rejected by Pydantic validation."""
    # Pydantic should reject empty changes list before apply_incremental_fixes is called
    with pytest.raises(ValidationError, match="at least 1 item"):
        IncrementalDocumentationFix(
            changes=[],
            summary="No changes",
            preserved_sections=["Purpose"],
        )


def test_parse_sections_with_empty_sections(doc_with_empty_sections):
    """Test parsing document with sections that have minimal content."""
    sections = parse_sections(doc_with_empty_sections)

    assert "Section 1" in sections
    assert "Section 2" in sections
    # Section 1 should be empty except for header
    assert sections["Section 1"].strip() == "## Section 1"


def test_apply_incremental_fixes_maintains_section_order(module_doc_three_sections):
    """Test that section order is preserved after applying fixes."""
    fixes = IncrementalDocumentationFix(
        changes=[
            DocumentationChange(
                section="Second",
                change_type="update",
                rationale="Updated middle section",
                updated_content="Updated content 2",
            )
        ],
        summary="Updated middle section",
        preserved_sections=["First", "Third"],
    )

    result = apply_incremental_fixes(current_doc=module_doc_three_sections, fixes=fixes)

    # Check that sections appear in original order
    first_pos = result.index("## First")
    second_pos = result.index("## Second")
    third_pos = result.index("## Third")

    assert first_pos < second_pos < third_pos


def test_apply_incremental_fixes_add_to_empty_doc(empty_module_doc):
    """Test adding a section to a document with only a preamble."""
    fixes = IncrementalDocumentationFix(
        changes=[
            DocumentationChange(
                section="Purpose & Scope",
                change_type="add",
                rationale="Adding first section",
                updated_content="This module does X.",
            )
        ],
        summary="Added first section",
        preserved_sections=[],
    )

    result = apply_incremental_fixes(current_doc=empty_module_doc, fixes=fixes)

    assert "## Purpose & Scope" in result
    assert "This module does X" in result
    assert "# Module" in result  # Preamble preserved


def test_apply_incremental_fixes_mixed_change_types(module_doc_with_all_sections):
    """Test applying add, update, and remove changes together."""
    fixes = IncrementalDocumentationFix(
        changes=[
            DocumentationChange(
                section="Purpose & Scope",
                change_type="update",
                rationale="Updated purpose",
                updated_content="New purpose.",
            ),
            DocumentationChange(
                section="Deprecated Section",
                change_type="remove",
                rationale="No longer relevant",
                updated_content="",
            ),
            DocumentationChange(
                section="New Section",
                change_type="add",
                rationale="Added new content",
                updated_content="New content here.",
            ),
        ],
        summary="Mixed changes",
        preserved_sections=["Architecture"],
    )

    result = apply_incremental_fixes(
        current_doc=module_doc_with_all_sections, fixes=fixes
    )

    assert "New purpose" in result
    assert "Old purpose" not in result
    assert "Deprecated Section" not in result
    assert "New Section" in result
    assert "New content here" in result
    assert "Old architecture" in result  # Preserved


def test_apply_incremental_fixes_strips_trailing_whitespace(simple_module_doc):
    """Test that trailing whitespace in content is stripped to prevent extra
    newlines."""
    fixes = IncrementalDocumentationFix(
        changes=[
            DocumentationChange(
                section="Purpose & Scope",
                change_type="update",
                rationale="Updated with trailing whitespace",
                # Excessive trailing newlines
                updated_content="New purpose content.\n\n\n",
            )
        ],
        summary="Updated with trailing whitespace",
        preserved_sections=[],
    )

    result = apply_incremental_fixes(current_doc=simple_module_doc, fixes=fixes)

    # Should only have 2 newlines between sections, not more
    # Count newlines after "New purpose content" and before end
    assert "New purpose content.\n" in result
    # Should not have 4+ consecutive newlines
    assert "\n\n\n\n" not in result


def test_apply_incremental_fixes_removes_duplicate_header(simple_module_doc):
    """Test that duplicate section headers are removed if LLM includes them."""
    fixes = IncrementalDocumentationFix(
        changes=[
            DocumentationChange(
                section="Purpose & Scope",
                change_type="update",
                rationale="LLM included header in content",
                # LLM mistakenly included the header in the content
                updated_content="## Purpose & Scope\n\nNew purpose with header.",
            )
        ],
        summary="Updated with duplicate header",
        preserved_sections=[],
    )

    result = apply_incremental_fixes(current_doc=simple_module_doc, fixes=fixes)

    # Should only have one occurrence of the header, not two
    header_count = result.count("## Purpose & Scope")
    assert header_count == 1, f"Expected 1 header, found {header_count}"
    assert "New purpose with header" in result
