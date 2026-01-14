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


# Edge case tests for markdown parsing robustness


def test_parse_sections_with_special_characters_in_headers():
    """Test parsing sections with special characters, symbols, and punctuation."""
    doc = """# Module

## Section: Overview & Setup

Content with colon and ampersand.

## Section (Deprecated)

Content with parentheses.

## Section #1 - First

Content with hash and dash.

## Section "Quotes" & More!

Content with quotes, ampersand, and exclamation."""

    sections = parse_sections(doc)

    assert "Section: Overview & Setup" in sections
    assert "Section (Deprecated)" in sections
    assert "Section #1 - First" in sections
    assert 'Section "Quotes" & More!' in sections
    assert "colon and ampersand" in sections["Section: Overview & Setup"]


def test_parse_sections_with_malformed_markdown_inconsistent_spacing():
    """Test parsing markdown with inconsistent spacing and formatting."""
    doc = """# Module
## Section 1
Content without blank line after header.
## Section 2


Content with multiple blank lines.


## Section 3

Content with trailing spaces.   """

    sections = parse_sections(doc)

    assert "Section 1" in sections
    assert "Section 2" in sections
    assert "Section 3" in sections
    assert "Content without blank line" in sections["Section 1"]
    assert "Content with multiple blank lines" in sections["Section 2"]


def test_parse_sections_with_missing_headers():
    """Test parsing document with only non-header content (malformed)."""
    doc = """# Title

Some content but no section headers.

More content here.

Even more content."""

    sections = parse_sections(doc)

    # All content should be in preamble
    assert "_preamble" in sections
    assert "Some content but no section headers" in sections["_preamble"]
    assert "More content here" in sections["_preamble"]
    # No actual sections should exist
    assert len([k for k in sections if k != "_preamble"]) == 0


def test_parse_sections_with_deeply_nested_headers():
    """Test parsing document with mixed header levels (##, ###, ####)."""
    doc = """# Module

## Section 1

Content in section 1.

### Subsection 1.1

Nested content.

#### Deeply nested 1.1.1

Very nested content.

## Section 2

Content in section 2."""

    sections = parse_sections(doc)

    # Only level-2 headers (##) should create sections
    assert "Section 1" in sections
    assert "Section 2" in sections

    # Nested headers (###, ####) should be part of parent section content
    section1_content = sections["Section 1"]
    assert "### Subsection 1.1" in section1_content
    assert "#### Deeply nested 1.1.1" in section1_content
    assert "Nested content" in section1_content
    assert "Very nested content" in section1_content


def test_parse_sections_with_empty_sections_between_headers():
    """Test parsing document with multiple consecutive headers without content."""
    doc = """# Module

## Section 1

## Section 2

## Section 3

Some content finally."""

    sections = parse_sections(doc)

    assert "Section 1" in sections
    assert "Section 2" in sections
    assert "Section 3" in sections

    # Section 1 and 2 should be empty (except for header)
    assert sections["Section 1"].strip() == "## Section 1"
    assert sections["Section 2"].strip() == "## Section 2"
    assert "Some content finally" in sections["Section 3"]


def test_parse_sections_with_header_like_content():
    """Test parsing document with ## in content that aren't headers."""
    doc = """# Module

## Real Section

This section discusses ## as a markdown symbol.
When you write ## at the start of a line, it creates a header.

## Another Real Section

More content."""

    sections = parse_sections(doc)

    assert "Real Section" in sections
    assert "Another Real Section" in sections

    # The ## in content should be preserved, not treated as header
    assert "## as a markdown symbol" in sections["Real Section"]
    # But only if it's not at the start of a line - this one IS at start
    # So it would be treated as a header. Let's verify the actual behavior.


def test_parse_sections_only_preamble_no_sections():
    """Test parsing document with only preamble content, no sections at all."""
    doc = """# My Module Title

This is a description of the module.

It has multiple paragraphs but no level-2 headers.

So all of this should be treated as preamble."""

    sections = parse_sections(doc)

    assert "_preamble" in sections
    assert "My Module Title" in sections["_preamble"]
    assert "multiple paragraphs" in sections["_preamble"]

    # Should have no sections other than preamble
    assert len(sections) == 1


def test_parse_sections_with_headers_with_extra_whitespace():
    """Test parsing headers with trailing/leading whitespace."""
    doc = """# Module

##   Section With Leading Spaces

Content.

## Trailing Spaces Section

More content.

##Section Without Space

Even more content."""

    sections = parse_sections(doc)

    # Headers should be stripped of leading/trailing whitespace
    assert "Section With Leading Spaces" in sections
    assert "Trailing Spaces Section" in sections

    # ##Section (without space after ##) should NOT be treated as a header
    # because it doesn't match "## " pattern (requires space)
    # It should be part of the previous section's content
    assert "##Section Without Space" in sections["Trailing Spaces Section"]
    assert "Even more content" in sections["Trailing Spaces Section"]


def test_parse_sections_with_unicode_and_emoji_in_headers():
    """Test parsing sections with unicode characters and emoji."""
    doc = """# Module

## Configuration 🔧

Setup content.

## Error Handling ⚠️

Error content.

## 中文 Section

Chinese characters.

## Übersicht

German umlaut."""

    sections = parse_sections(doc)

    assert "Configuration 🔧" in sections
    assert "Error Handling ⚠️" in sections
    assert "中文 Section" in sections
    assert "Übersicht" in sections


def test_apply_incremental_fixes_with_empty_sections():
    """Test applying fixes to document with empty sections."""
    doc = """# Module

## Section 1

## Section 2

Some content.

## Section 3"""

    fixes = IncrementalDocumentationFix(
        changes=[
            DocumentationChange(
                section="Section 1",
                change_type="update",
                rationale="Adding content to empty section",
                updated_content="New content for section 1.",
            )
        ],
        summary="Updated empty section",
        preserved_sections=["Section 2", "Section 3"],
    )

    result = apply_incremental_fixes(current_doc=doc, fixes=fixes)

    assert "New content for section 1" in result
    assert "Some content" in result  # Section 2 preserved


def test_apply_incremental_fixes_with_malformed_markdown():
    """Test applying fixes to document with inconsistent formatting."""
    doc = """# Module
## Section 1
Content without proper spacing.
## Section 2


Multiple blank lines everywhere.


"""

    fixes = IncrementalDocumentationFix(
        changes=[
            DocumentationChange(
                section="Section 1",
                change_type="update",
                rationale="Fixing formatting",
                updated_content="Properly formatted content.",
            )
        ],
        summary="Fixed formatting",
        preserved_sections=["Section 2"],
    )

    result = apply_incremental_fixes(current_doc=doc, fixes=fixes)

    # Should produce well-formatted output despite malformed input
    assert "## Section 1" in result
    assert "Properly formatted content" in result
    assert "## Section 2" in result


def test_reconstruct_document_preserves_unusual_formatting():
    """Test that reconstruction maintains structure even with unusual formatting."""
    doc = """# Module

Preamble with weird spacing.


## Section 1

Content.

## Section 2

More content."""

    # Apply a no-op fix (add then remove same section)
    fixes = IncrementalDocumentationFix(
        changes=[
            DocumentationChange(
                section="Section 1",
                change_type="update",
                rationale="Testing reconstruction",
                updated_content="Content.",
            )
        ],
        summary="Testing",
        preserved_sections=["Section 2"],
    )

    result = apply_incremental_fixes(current_doc=doc, fixes=fixes)

    # Preamble should be preserved
    assert "Preamble with weird spacing" in result
    # Sections should be in order
    assert result.index("## Section 1") < result.index("## Section 2")


def test_parse_sections_with_code_blocks_containing_headers():
    """Test behavior when ## appears inside code blocks.

    Note: The parser does NOT understand code blocks and will treat any line
    starting with '## ' as a section header, even inside code blocks. This test
    documents this current limitation.
    """
    doc = """# Module

## Configuration

Example config:

```python
## This is treated as a header
text = "## Neither is this"
```

More content.

## Next Section

Content."""

    sections = parse_sections(doc)

    # The parser creates a section for "This is treated as a header"
    # because it doesn't understand code block context
    assert "Configuration" in sections
    assert "This is treated as a header" in sections
    assert "Next Section" in sections

    # Configuration section ends at the first ## in the code block
    assert "Example config:" in sections["Configuration"]
    assert "```python" in sections["Configuration"]

    # Content after the fake header is part of that section
    assert "## Neither is this" in sections["This is treated as a header"]
    assert "More content" in sections["This is treated as a header"]
