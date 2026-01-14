"""Tests for doc_configs module."""

from src.doctypes import DOC_CONFIGS, DocConfig, DocType
from src.llm import (
    MODULE_GENERATION_PROMPT,
    PROJECT_README_GENERATION_PROMPT,
    STYLE_GUIDE_GENERATION_PROMPT,
)
from src.output import (
    format_module_documentation,
    format_project_documentation,
    format_style_guide,
)
from src.records import (
    ModuleDocumentation,
    ModuleIntent,
    ProjectDocumentation,
    ProjectIntent,
    StyleGuideDocumentation,
    StyleGuideIntent,
)


def test_all_doc_types_have_valid_configs() -> None:
    """Test that all doc types have properly configured DocConfigs."""
    # Check registry has all doc types
    assert len(DOC_CONFIGS) == 3
    assert DocType.MODULE_README in DOC_CONFIGS
    assert DocType.PROJECT_README in DOC_CONFIGS
    assert DocType.STYLE_GUIDE in DOC_CONFIGS

    # Validate all configs
    for doc_type in DocType:
        config = DOC_CONFIGS[doc_type]

        # Check it's a DocConfig instance
        assert isinstance(config, DocConfig)

        # Check all required fields exist and have correct types
        assert callable(config.formatter)
        assert isinstance(config.prompt, str) and len(config.prompt) > 0
        assert isinstance(config.default_depth, int)
        assert isinstance(config.analyze_entire_repo, bool)
        assert isinstance(config.intent_questions, list)


def test_specific_config_values() -> None:
    """Test that specific configs have expected values."""
    # MODULE_README
    module_config = DOC_CONFIGS[DocType.MODULE_README]
    assert module_config.model == ModuleDocumentation
    assert module_config.prompt == MODULE_GENERATION_PROMPT
    assert module_config.formatter == format_module_documentation
    assert module_config.intent_model == ModuleIntent
    assert module_config.default_depth == 0
    assert module_config.analyze_entire_repo is False

    # PROJECT_README
    project_config = DOC_CONFIGS[DocType.PROJECT_README]
    assert project_config.model == ProjectDocumentation
    assert project_config.prompt == PROJECT_README_GENERATION_PROMPT
    assert project_config.formatter == format_project_documentation
    assert project_config.intent_model == ProjectIntent
    assert project_config.default_depth == 1
    assert project_config.analyze_entire_repo is True

    # STYLE_GUIDE
    style_config = DOC_CONFIGS[DocType.STYLE_GUIDE]
    assert style_config.model == StyleGuideDocumentation
    assert style_config.prompt == STYLE_GUIDE_GENERATION_PROMPT
    assert style_config.formatter == format_style_guide
    assert style_config.intent_model == StyleGuideIntent
    assert style_config.default_depth == -1
    assert style_config.analyze_entire_repo is True


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
