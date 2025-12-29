"""Tests for Claude Code configuration files."""

import json
from pathlib import Path


def test_code_review_specification_exists() -> None:
    """Test that code review specification file exists."""
    spec_file = Path(".claude/code-review-agent.md")
    assert spec_file.exists(), "Code review specification file should exist"
    assert spec_file.is_file(), "Code review specification should be a file"


def test_code_review_command_exists() -> None:
    """Test that code review slash command file exists."""
    command_file = Path(".claude/commands/review.md")
    assert command_file.exists(), "Code review command file should exist"
    assert command_file.is_file(), "Code review command should be a file"


def test_code_review_agent_config_exists() -> None:
    """Test that code review agent configuration exists."""
    agent_file = Path(".claude/agents/code-review.json")
    assert agent_file.exists(), "Code review agent config should exist"
    assert agent_file.is_file(), "Code review agent config should be a file"


def test_code_review_agent_config_valid_json() -> None:
    """Test that code review agent config is valid JSON."""
    agent_file = Path(".claude/agents/code-review.json")

    with open(agent_file) as f:
        config = json.load(f)

    # Verify required fields
    assert "name" in config, "Agent config should have 'name' field"
    assert "description" in config, "Agent config should have 'description' field"
    assert "instructions" in config, "Agent config should have 'instructions' field"

    # Verify field types
    assert isinstance(config["name"], str), "Agent name should be a string"
    assert isinstance(config["description"], str), (
        "Agent description should be a string"
    )
    assert isinstance(config["instructions"], str), (
        "Agent instructions should be a string"
    )


def test_code_review_command_has_frontmatter() -> None:
    """Test that code review command has valid frontmatter."""
    command_file = Path(".claude/commands/review.md")

    content = command_file.read_text()

    # Check for YAML frontmatter
    assert content.startswith("---\n"), "Command should start with YAML frontmatter"
    assert "name:" in content, "Command frontmatter should have 'name' field"
    assert "description:" in content, (
        "Command frontmatter should have 'description' field"
    )


def test_code_review_references_exist() -> None:
    """Test that all referenced files in code review documentation exist."""
    # Files referenced in the code review specification
    referenced_files = [
        Path("docs/style-guide.md"),
        Path("CLAUDE.md"),
        Path("pyproject.toml"),
        Path(".pre-commit-config.yaml"),
    ]

    for file_path in referenced_files:
        assert file_path.exists(), f"Referenced file {file_path} should exist"


def test_code_review_specification_has_required_sections() -> None:
    """Test that code review specification has all required sections."""
    spec_file = Path(".claude/code-review-agent.md")
    content = spec_file.read_text()

    # Required sections
    required_sections = [
        "# Code Review Agent Specification",
        "## Core Principles",
        "## Review Checklist",
        "## Review Process",
        "## Success Criteria",
        "## Agent Behavior",
    ]

    for section in required_sections:
        assert section in content, f"Specification should have '{section}' section"


def test_code_review_specification_mentions_core_principles() -> None:
    """Test that specification covers all core review principles."""
    spec_file = Path(".claude/code-review-agent.md")
    content = spec_file.read_text()

    # Core principles that should be mentioned
    core_principles = [
        "Separation of Concerns",
        "KISS",
        "DRY",
        "Readability",
        "Testability",
        "Test Quality",
        "Documentation",
    ]

    for principle in core_principles:
        assert principle in content, f"Specification should mention '{principle}'"
