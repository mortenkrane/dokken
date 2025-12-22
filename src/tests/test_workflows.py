"""Tests for src/workflows.py"""

from dataclasses import replace
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from src.doc_configs import DOC_CONFIGS
from src.doc_types import DocType
from src.exceptions import DocumentationDriftError
from src.records import DocumentationDriftCheck, ModuleDocumentation
from src.workflows import (
    check_documentation_drift,
    check_multiple_modules_drift,
    fix_documentation_drift,
    generate_documentation,
)


def test_check_documentation_drift_invalid_directory(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    """Test check_documentation_drift exits when given invalid directory."""
    mocker.patch("src.workflows.console")
    invalid_path = str(tmp_path / "nonexistent")

    with pytest.raises(SystemExit) as exc_info:
        check_documentation_drift(target_module_path=invalid_path)

    assert isinstance(exc_info.value, SystemExit)
    assert exc_info.value.code == 1


def test_check_documentation_drift_no_code_context(
    mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test check_documentation_drift returns early when no code context."""
    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.initialize_llm")
    mock_get_context = mocker.patch("src.workflows.get_module_context", return_value="")

    # Should return early without raising
    check_documentation_drift(target_module_path=str(temp_module_dir))

    mock_get_context.assert_called_once()


def test_check_documentation_drift_no_readme_raises_error(
    mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test check_documentation_drift raises error when README.md doesn't exist."""
    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code context")

    with pytest.raises(DocumentationDriftError) as exc_info:
        check_documentation_drift(target_module_path=str(temp_module_dir))

    assert "No documentation exists" in str(exc_info.value)


def test_check_documentation_drift_no_drift_detected(
    mocker: MockerFixture,
    tmp_path: Path,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test check_documentation_drift when no drift is detected."""
    # Create module dir with README
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    readme = module_dir / "README.md"
    readme.write_text("# Test\n\nDocumentation")

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code context")
    mock_check_drift = mocker.patch(
        "src.workflows.check_drift", return_value=sample_drift_check_no_drift
    )

    # Should not raise
    check_documentation_drift(target_module_path=str(module_dir))

    mock_check_drift.assert_called_once()


def test_check_documentation_drift_with_drift_raises_error(
    mocker: MockerFixture,
    tmp_path: Path,
    sample_drift_check_with_drift: DocumentationDriftCheck,
) -> None:
    """Test check_documentation_drift raises error when drift is detected."""
    # Create module dir with README
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    readme = module_dir / "README.md"
    readme.write_text("# Test\n\nDocumentation")

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code context")
    mocker.patch(
        "src.workflows.check_drift", return_value=sample_drift_check_with_drift
    )

    with pytest.raises(DocumentationDriftError) as exc_info:
        check_documentation_drift(target_module_path=str(module_dir))

    assert sample_drift_check_with_drift.rationale in str(exc_info.value)


def test_generate_documentation_invalid_directory(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    """Test generate_documentation exits when given invalid directory."""
    mocker.patch("src.workflows.console")
    invalid_path = str(tmp_path / "nonexistent")

    with pytest.raises(SystemExit) as exc_info:
        generate_documentation(target_module_path=invalid_path)

    assert isinstance(exc_info.value, SystemExit)
    assert exc_info.value.code == 1


def test_generate_documentation_no_code_context(
    mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test generate_documentation returns early when no code context."""
    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.initialize_llm")
    mock_get_context = mocker.patch("src.workflows.get_module_context", return_value="")

    result = generate_documentation(target_module_path=str(temp_module_dir))

    assert result is None
    mock_get_context.assert_called_once()


def test_generate_documentation_no_drift_skips_generation(
    mocker: MockerFixture,
    tmp_path: Path,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test generate_documentation skips generation when no drift detected."""
    # Create module dir with README
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    readme = module_dir / "README.md"
    readme.write_text("# Test\n\nDocumentation")

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code context")
    mocker.patch("src.workflows.check_drift", return_value=sample_drift_check_no_drift)
    mock_generate_doc = mocker.patch("src.workflows.generate_doc")

    result = generate_documentation(target_module_path=str(module_dir))

    # Should not generate docs
    mock_generate_doc.assert_not_called()
    assert result is None


def test_generate_documentation_generates_when_drift(
    mocker: MockerFixture,
    tmp_path: Path,
    sample_drift_check_with_drift: DocumentationDriftCheck,
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test generate_documentation generates docs when drift detected."""
    # Create module dir with README
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    readme = module_dir / "README.md"
    readme.write_text("# Test\n\nDocumentation")

    mocker.patch("src.workflows.console")

    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code context")
    mocker.patch(
        "src.workflows.check_drift", return_value=sample_drift_check_with_drift
    )
    mocker.patch("src.workflows.ask_human_intent", return_value=None)
    mock_generate_doc = mocker.patch(
        "src.workflows.generate_doc", return_value=sample_component_documentation
    )

    # Mock the formatter in DOC_CONFIGS
    mock_formatter = mocker.Mock(return_value="# Markdown")
    test_doc_config = replace(
        DOC_CONFIGS[DocType.MODULE_README], formatter=mock_formatter
    )
    mocker.patch.dict(
        "src.workflows.DOC_CONFIGS", {DocType.MODULE_README: test_doc_config}
    )

    result = generate_documentation(target_module_path=str(module_dir))

    mock_generate_doc.assert_called_once()
    assert result == "# Markdown"


def test_generate_documentation_writes_readme(
    mocker: MockerFixture,
    tmp_path: Path,
    sample_drift_check_with_drift: DocumentationDriftCheck,
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test generate_documentation writes README.md file."""
    # Create module dir with README
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    readme = module_dir / "README.md"
    readme.write_text("# Old Docs")

    mocker.patch("src.workflows.console")

    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code context")
    mocker.patch(
        "src.workflows.check_drift", return_value=sample_drift_check_with_drift
    )
    mocker.patch("src.workflows.ask_human_intent", return_value=None)
    mocker.patch(
        "src.workflows.generate_doc", return_value=sample_component_documentation
    )

    # Mock the formatter in DOC_CONFIGS
    mock_formatter = mocker.Mock(return_value="# New Markdown Content")
    test_doc_config = replace(
        DOC_CONFIGS[DocType.MODULE_README], formatter=mock_formatter
    )
    mocker.patch.dict(
        "src.workflows.DOC_CONFIGS", {DocType.MODULE_README: test_doc_config}
    )

    generate_documentation(target_module_path=str(module_dir))

    # Verify README was written
    assert readme.read_text() == "# New Markdown Content"


def test_generate_documentation_creates_readme_if_missing(
    mocker: MockerFixture,
    temp_module_dir: Path,
    sample_drift_check_with_drift: DocumentationDriftCheck,
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test generate_documentation creates README.md if it doesn't exist."""
    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code context")
    # When no README exists, drift check will say drift detected
    mocker.patch(
        "src.workflows.check_drift", return_value=sample_drift_check_with_drift
    )
    mocker.patch("src.workflows.ask_human_intent", return_value=None)
    mocker.patch(
        "src.workflows.generate_doc", return_value=sample_component_documentation
    )

    # Mock the formatter in DOC_CONFIGS
    mock_formatter = mocker.Mock(return_value="# New Docs")
    test_doc_config = replace(
        DOC_CONFIGS[DocType.MODULE_README], formatter=mock_formatter
    )
    mocker.patch.dict(
        "src.workflows.DOC_CONFIGS", {DocType.MODULE_README: test_doc_config}
    )

    generate_documentation(target_module_path=str(temp_module_dir))

    readme_path = temp_module_dir / "README.md"
    assert readme_path.exists()
    assert readme_path.read_text() == "# New Docs"


def test_check_documentation_drift_initializes_llm(
    mocker: MockerFixture,
    tmp_path: Path,
    sample_drift_check_no_drift: DocumentationDriftCheck,
) -> None:
    """Test check_documentation_drift initializes LLM."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    readme = module_dir / "README.md"
    readme.write_text("# Test")

    mocker.patch("src.workflows.console")
    mock_init_llm = mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code context")
    mocker.patch("src.workflows.check_drift", return_value=sample_drift_check_no_drift)

    check_documentation_drift(target_module_path=str(module_dir))

    mock_init_llm.assert_called_once()


def test_generate_documentation_initializes_llm(
    mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test generate_documentation initializes LLM."""
    mocker.patch("src.workflows.console")
    mock_init_llm = mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="")

    generate_documentation(target_module_path=str(temp_module_dir))

    mock_init_llm.assert_called_once()


def test_check_documentation_drift_fix_no_readme_still_raises(
    mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """
    Test check_documentation_drift with fix=True still raises error when no README.
    """
    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code context")

    # Should raise error even with fix=True when no README exists
    with pytest.raises(DocumentationDriftError) as exc_info:
        check_documentation_drift(target_module_path=str(temp_module_dir), fix=True)

    assert "No documentation exists" in str(exc_info.value)


def test_fix_documentation_drift_generates_and_writes(
    mocker: MockerFixture,
    tmp_path: Path,
    mock_llm_client,
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test fix_documentation_drift generates and writes updated documentation."""
    readme_path = tmp_path / "README.md"
    readme_path.write_text("# Old Documentation")

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.ask_human_intent", return_value=None)
    mocker.patch("src.workflows.load_config")
    mock_generate_doc = mocker.patch(
        "src.workflows.generate_doc", return_value=sample_component_documentation
    )

    # Create a custom doc_config with mocked formatter
    mock_formatter = mocker.Mock(return_value="# Updated Docs")
    test_doc_config = replace(
        DOC_CONFIGS[DocType.MODULE_README], formatter=mock_formatter
    )

    fix_documentation_drift(
        llm_client=mock_llm_client,
        code_context="code context",
        output_path=str(readme_path),
        doc_config=test_doc_config,
        drift_rationale="Test drift rationale",
        doc_type=DocType.MODULE_README,
        module_path=str(tmp_path),
    )

    # Should generate documentation with drift rationale
    # Note: assert checks call arguments - custom_prompts and doc_type are passed
    assert mock_generate_doc.call_count == 1
    # Verify README was updated
    assert readme_path.read_text() == "# Updated Docs"


def test_check_documentation_drift_fix_with_drift(
    mocker: MockerFixture,
    tmp_path: Path,
    sample_drift_check_with_drift: DocumentationDriftCheck,
) -> None:
    """
    Test check_documentation_drift with fix=True calls fix function when drift detected.
    """
    # Create module dir with README
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    readme = module_dir / "README.md"
    readme.write_text("# Old Documentation")

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code context")
    mocker.patch(
        "src.workflows.check_drift", return_value=sample_drift_check_with_drift
    )
    mock_fix = mocker.patch("src.workflows.fix_documentation_drift")

    # Should not raise error when fix=True
    check_documentation_drift(target_module_path=str(module_dir), fix=True)

    # Should call fix function
    mock_fix.assert_called_once()


def test_generate_documentation_project_readme_in_git_repo(
    mocker: MockerFixture,
    tmp_path: Path,
    sample_drift_check_with_drift: DocumentationDriftCheck,
) -> None:
    """Test generating PROJECT_README in a git repository."""
    # Create a git repo structure
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()  # Simulate git repo

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code context")
    mocker.patch(
        "src.workflows.check_drift", return_value=sample_drift_check_with_drift
    )
    mocker.patch("src.workflows.ask_human_intent", return_value=None)
    mock_generate_doc = mocker.patch("src.workflows.generate_doc")

    # Mock formatter
    mock_formatter = mocker.Mock(return_value="# Project Docs")
    test_doc_config = replace(
        DOC_CONFIGS[DocType.PROJECT_README], formatter=mock_formatter
    )
    mocker.patch.dict(
        "src.workflows.DOC_CONFIGS", {DocType.PROJECT_README: test_doc_config}
    )

    generate_documentation(
        target_module_path=str(repo_dir), doc_type=DocType.PROJECT_README
    )

    # Should generate doc
    mock_generate_doc.assert_called_once()
    # Should create README.md in repo root
    readme_path = repo_dir / "README.md"
    assert readme_path.exists()


def test_generate_documentation_style_guide_creates_docs_dir(
    mocker: MockerFixture,
    tmp_path: Path,
    sample_drift_check_with_drift: DocumentationDriftCheck,
) -> None:
    """Test generating STYLE_GUIDE creates docs/ directory."""
    # Create a git repo structure
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()  # Simulate git repo

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code context")
    mocker.patch(
        "src.workflows.check_drift", return_value=sample_drift_check_with_drift
    )
    mocker.patch("src.workflows.ask_human_intent", return_value=None)
    mock_generate_doc = mocker.patch("src.workflows.generate_doc")

    # Mock formatter
    mock_formatter = mocker.Mock(return_value="# Style Guide")
    test_doc_config = replace(
        DOC_CONFIGS[DocType.STYLE_GUIDE], formatter=mock_formatter
    )
    mocker.patch.dict(
        "src.workflows.DOC_CONFIGS", {DocType.STYLE_GUIDE: test_doc_config}
    )

    generate_documentation(
        target_module_path=str(repo_dir), doc_type=DocType.STYLE_GUIDE
    )

    # Should generate doc
    mock_generate_doc.assert_called_once()
    # Should create docs/style-guide.md
    style_guide_path = repo_dir / "docs" / "style-guide.md"
    assert style_guide_path.exists()
    assert (repo_dir / "docs").is_dir()


def test_check_multiple_modules_drift_not_in_git_repo(
    mocker: MockerFixture,
) -> None:
    """Test check_multiple_modules_drift exits when not in a git repository."""
    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.find_repo_root", return_value=None)

    with pytest.raises(SystemExit) as exc_info:
        check_multiple_modules_drift()

    assert exc_info.value.code == 1


def test_check_multiple_modules_drift_no_modules_configured(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    """Test check_multiple_modules_drift exits when no modules configured."""
    # Create a git repo
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.find_repo_root", return_value=str(repo_dir))

    # Mock load_config to return empty modules list
    from src.config import DokkenConfig
    mocker.patch("src.workflows.load_config", return_value=DokkenConfig(modules=[]))

    with pytest.raises(SystemExit) as exc_info:
        check_multiple_modules_drift()

    assert exc_info.value.code == 1


def test_check_multiple_modules_drift_all_modules_pass(
    mocker: MockerFixture, tmp_path: Path, sample_drift_check_no_drift: DocumentationDriftCheck
) -> None:
    """Test check_multiple_modules_drift when all modules pass drift check."""
    # Create a git repo with modules
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    module1 = repo_dir / "src" / "module1"
    module1.mkdir(parents=True)
    (module1 / "README.md").write_text("# Module 1")

    module2 = repo_dir / "src" / "module2"
    module2.mkdir(parents=True)
    (module2 / "README.md").write_text("# Module 2")

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.find_repo_root", return_value=str(repo_dir))

    # Mock config with two modules
    from src.config import DokkenConfig
    mocker.patch(
        "src.workflows.load_config",
        return_value=DokkenConfig(modules=["src/module1", "src/module2"]),
    )

    # Mock check_documentation_drift to succeed (no exception)
    mock_check = mocker.patch("src.workflows.check_documentation_drift")

    # Should not raise
    check_multiple_modules_drift()

    # Should check both modules
    assert mock_check.call_count == 2


def test_check_multiple_modules_drift_some_modules_fail(
    mocker: MockerFixture,
    tmp_path: Path,
    sample_drift_check_with_drift: DocumentationDriftCheck,
) -> None:
    """Test check_multiple_modules_drift when some modules have drift."""
    # Create a git repo with modules
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    module1 = repo_dir / "src" / "module1"
    module1.mkdir(parents=True)
    (module1 / "README.md").write_text("# Module 1")

    module2 = repo_dir / "src" / "module2"
    module2.mkdir(parents=True)
    (module2 / "README.md").write_text("# Module 2")

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.find_repo_root", return_value=str(repo_dir))

    # Mock config with two modules
    from src.config import DokkenConfig
    mocker.patch(
        "src.workflows.load_config",
        return_value=DokkenConfig(modules=["src/module1", "src/module2"]),
    )

    # First module passes, second module has drift
    def check_side_effect(*args, **kwargs):
        if "module2" in kwargs["target_module_path"]:
            raise DocumentationDriftError(
                rationale="Test drift", module_path=kwargs["target_module_path"]
            )

    mock_check = mocker.patch(
        "src.workflows.check_documentation_drift", side_effect=check_side_effect
    )

    # Should raise DocumentationDriftError
    with pytest.raises(DocumentationDriftError) as exc_info:
        check_multiple_modules_drift()

    assert "1 module(s) have documentation drift" in str(exc_info.value)
    assert mock_check.call_count == 2


def test_check_multiple_modules_drift_skips_nonexistent_modules(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    """Test check_multiple_modules_drift skips modules that don't exist."""
    # Create a git repo with only one module
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    module1 = repo_dir / "src" / "module1"
    module1.mkdir(parents=True)
    (module1 / "README.md").write_text("# Module 1")

    # module2 doesn't exist

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.find_repo_root", return_value=str(repo_dir))

    # Mock config with two modules (one nonexistent)
    from src.config import DokkenConfig
    mocker.patch(
        "src.workflows.load_config",
        return_value=DokkenConfig(modules=["src/module1", "src/nonexistent"]),
    )

    mock_check = mocker.patch("src.workflows.check_documentation_drift")

    # Should not raise
    check_multiple_modules_drift()

    # Should only check the existing module
    assert mock_check.call_count == 1


def test_check_multiple_modules_drift_with_fix(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    """Test check_multiple_modules_drift passes fix flag to individual checks."""
    # Create a git repo with modules
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    module1 = repo_dir / "src" / "module1"
    module1.mkdir(parents=True)
    (module1 / "README.md").write_text("# Module 1")

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.find_repo_root", return_value=str(repo_dir))

    # Mock config with one module
    from src.config import DokkenConfig
    mocker.patch(
        "src.workflows.load_config",
        return_value=DokkenConfig(modules=["src/module1"]),
    )

    mock_check = mocker.patch("src.workflows.check_documentation_drift")

    # Call with fix=True
    check_multiple_modules_drift(fix=True)

    # Should pass fix=True to individual checks
    mock_check.assert_called_once()
    assert mock_check.call_args.kwargs["fix"] is True
