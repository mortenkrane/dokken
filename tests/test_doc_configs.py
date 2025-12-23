"""Tests for doc_configs module."""

from src.doc_configs import DOC_CONFIGS, DocConfig
from src.doc_types import DocType
from src.formatters import (
    format_module_documentation,
    format_project_documentation,
    format_style_guide,
)
from src.prompts import (
    MODULE_GENERATION_PROMPT,
    PROJECT_README_GENERATION_PROMPT,
    STYLE_GUIDE_GENERATION_PROMPT,
)
from src.records import (
    ModuleDocumentation,
    ModuleIntent,
    ProjectDocumentation,
    ProjectIntent,
    StyleGuideDocumentation,
    StyleGuideIntent,
)


def test_doc_config_dataclass_fields() -> None:
    """Test that DocConfig has expected fields."""
    config = DOC_CONFIGS[DocType.MODULE_README]
    assert hasattr(config, "model")
    assert hasattr(config, "prompt")
    assert hasattr(config, "formatter")
    assert hasattr(config, "intent_model")
    assert hasattr(config, "intent_questions")
    assert hasattr(config, "default_depth")
    assert hasattr(config, "analyze_entire_repo")


def test_doc_configs_registry_has_all_types() -> None:
    """Test that DOC_CONFIGS registry contains all doc types."""
    assert DocType.MODULE_README in DOC_CONFIGS
    assert DocType.PROJECT_README in DOC_CONFIGS
    assert DocType.STYLE_GUIDE in DOC_CONFIGS
    assert len(DOC_CONFIGS) == 3


def test_module_readme_config() -> None:
    """Test MODULE_README configuration."""
    config = DOC_CONFIGS[DocType.MODULE_README]
    assert config.model == ModuleDocumentation
    assert config.prompt == MODULE_GENERATION_PROMPT
    assert config.formatter == format_module_documentation
    assert config.intent_model == ModuleIntent
    assert config.default_depth == 0
    assert config.analyze_entire_repo is False
    assert isinstance(config.intent_questions, list)
    assert len(config.intent_questions) == 4


def test_project_readme_config() -> None:
    """Test PROJECT_README configuration."""
    config = DOC_CONFIGS[DocType.PROJECT_README]
    assert config.model == ProjectDocumentation
    assert config.prompt == PROJECT_README_GENERATION_PROMPT
    assert config.formatter == format_project_documentation
    assert config.intent_model == ProjectIntent
    assert config.default_depth == 1
    assert config.analyze_entire_repo is True
    assert isinstance(config.intent_questions, list)
    assert len(config.intent_questions) == 4


def test_style_guide_config() -> None:
    """Test STYLE_GUIDE configuration."""
    config = DOC_CONFIGS[DocType.STYLE_GUIDE]
    assert config.model == StyleGuideDocumentation
    assert config.prompt == STYLE_GUIDE_GENERATION_PROMPT
    assert config.formatter == format_style_guide
    assert config.intent_model == StyleGuideIntent
    assert config.default_depth == -1
    assert config.analyze_entire_repo is True
    assert isinstance(config.intent_questions, list)
    assert len(config.intent_questions) == 3


def test_intent_questions_structure() -> None:
    """Test that all intent questions have required fields."""
    for doc_type in DocType:
        config = DOC_CONFIGS[doc_type]
        for question in config.intent_questions:
            assert "key" in question
            assert "question" in question
            assert isinstance(question["key"], str)
            assert isinstance(question["question"], str)
            assert len(question["key"]) > 0
            assert len(question["question"]) > 0


def test_module_readme_intent_questions() -> None:
    """Test MODULE_README intent questions cover all expected keys."""
    config = DOC_CONFIGS[DocType.MODULE_README]
    keys = [q["key"] for q in config.intent_questions]
    assert "problems_solved" in keys
    assert "core_responsibilities" in keys
    assert "non_responsibilities" in keys
    assert "system_context" in keys


def test_project_readme_intent_questions() -> None:
    """Test PROJECT_README intent questions cover all expected keys."""
    config = DOC_CONFIGS[DocType.PROJECT_README]
    keys = [q["key"] for q in config.intent_questions]
    assert "project_type" in keys
    assert "target_audience" in keys
    assert "key_problem" in keys
    assert "setup_notes" in keys


def test_style_guide_intent_questions() -> None:
    """Test STYLE_GUIDE intent questions cover all expected keys."""
    config = DOC_CONFIGS[DocType.STYLE_GUIDE]
    keys = [q["key"] for q in config.intent_questions]
    assert "unique_conventions" in keys
    assert "organization_notes" in keys
    assert "patterns" in keys


def test_all_configs_are_doc_config_instances() -> None:
    """Test that all registry values are DocConfig instances."""
    for doc_type in DocType:
        config = DOC_CONFIGS[doc_type]
        assert isinstance(config, DocConfig)


def test_default_depths_are_integers() -> None:
    """Test that all default depths are integers."""
    for doc_type in DocType:
        config = DOC_CONFIGS[doc_type]
        assert isinstance(config.default_depth, int)


def test_analyze_entire_repo_is_boolean() -> None:
    """Test that analyze_entire_repo is boolean for all configs."""
    for doc_type in DocType:
        config = DOC_CONFIGS[doc_type]
        assert isinstance(config.analyze_entire_repo, bool)


def test_formatters_are_callable() -> None:
    """Test that all formatters are callable."""
    for doc_type in DocType:
        config = DOC_CONFIGS[doc_type]
        assert callable(config.formatter)


def test_prompts_are_strings() -> None:
    """Test that all prompts are strings."""
    for doc_type in DocType:
        config = DOC_CONFIGS[doc_type]
        assert isinstance(config.prompt, str)
        assert len(config.prompt) > 0
