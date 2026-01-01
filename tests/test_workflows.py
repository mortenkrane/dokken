"""Tests for src/workflows.py"""

from dataclasses import replace
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from src.config import DokkenConfig
from src.config.models import CustomPrompts
from src.doc_configs import DOC_CONFIGS
from src.doc_types import DocType
from src.exceptions import DocumentationDriftError
from src.records import (
    DocumentationChange,
    DocumentationDriftCheck,
    IncrementalDocumentationFix,
    ModuleDocumentation,
)
from src.workflows import (
    check_documentation_drift,
    check_multiple_modules_drift,
    fix_documentation_drift,
    generate_documentation,
)


def test_check_documentation_drift_invalid_directory(
    mock_workflows_console, tmp_path: Path
) -> None:
    """Test check_documentation_drift exits when given invalid directory."""
    invalid_path = str(tmp_path / "nonexistent")

    with pytest.raises(SystemExit) as exc_info:
        check_documentation_drift(target_module_path=invalid_path)

    assert isinstance(exc_info.value, SystemExit)
    assert exc_info.value.code == 1


def test_check_documentation_drift_no_git_for_project_readme(
    mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test check_documentation_drift raises ValueError when using PROJECT_README
    without git."""
    # PROJECT_README requires git root
    with pytest.raises(ValueError, match="not in a git repository"):
        check_documentation_drift(
            target_module_path=str(temp_module_dir), doc_type=DocType.PROJECT_README
        )


def test_check_documentation_drift_no_code_context(
    mock_workflows_console, mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test check_documentation_drift returns early when no code context."""
    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="")

    # When: Checking drift with no code context
    # Then: Should return without raising (early return)
    check_documentation_drift(target_module_path=str(temp_module_dir))


def test_check_documentation_drift_no_readme_raises_error(
    mock_workflows_console, mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test check_documentation_drift raises error when README.md doesn't exist."""
    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code context")

    with pytest.raises(DocumentationDriftError) as exc_info:
        check_documentation_drift(target_module_path=str(temp_module_dir))

    assert "No documentation exists" in str(exc_info.value)


def test_check_documentation_drift_no_drift_detected(
    mock_workflows_console,
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

    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code context")
    mocker.patch("src.workflows.check_drift", return_value=sample_drift_check_no_drift)

    # When: Checking drift with up-to-date documentation
    # Then: Should complete without raising error
    check_documentation_drift(target_module_path=str(module_dir))


def test_check_documentation_drift_with_drift_raises_error(
    mock_workflows_console,
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

    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code context")
    mocker.patch(
        "src.workflows.check_drift", return_value=sample_drift_check_with_drift
    )

    with pytest.raises(DocumentationDriftError) as exc_info:
        check_documentation_drift(target_module_path=str(module_dir))

    assert sample_drift_check_with_drift.rationale in str(exc_info.value)


def test_generate_documentation_invalid_directory(
    mock_workflows_console, tmp_path: Path
) -> None:
    """Test generate_documentation exits when given invalid directory."""
    invalid_path = str(tmp_path / "nonexistent")

    with pytest.raises(SystemExit) as exc_info:
        generate_documentation(target_module_path=invalid_path)

    assert isinstance(exc_info.value, SystemExit)
    assert exc_info.value.code == 1


def test_generate_documentation_no_code_context(
    mock_workflows_console, mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test generate_documentation returns early when no code context."""
    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="")

    # When: Generating documentation with no code context
    result = generate_documentation(target_module_path=str(temp_module_dir))

    # Then: Should return None (early return)
    assert result is None


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
    mocker.patch("src.workflows.generate_doc")

    # When: Generating documentation with no drift detected
    result = generate_documentation(target_module_path=str(module_dir))

    # Then: Should skip generation and return None
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
    mocker.patch(
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

    # When: Generating documentation with drift detected
    result = generate_documentation(target_module_path=str(module_dir))

    # Then: Should generate and return formatted markdown
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
    """Test fix_documentation_drift uses incremental fixes to update documentation."""

    readme_path = tmp_path / "README.md"
    current_doc_content = """# Old Documentation

## Purpose & Scope

Old purpose description."""
    readme_path.write_text(current_doc_content)

    mocker.patch("src.workflows.console")

    # Mock config with custom_prompts

    mock_config = mocker.Mock()
    mock_config.custom_prompts = CustomPrompts()
    mocker.patch("src.workflows.load_config", return_value=mock_config)

    # Mock incremental fix response
    mock_fixes = IncrementalDocumentationFix(
        changes=[
            DocumentationChange(
                section="Purpose & Scope",
                change_type="update",
                rationale="Updated to reflect new features",
                updated_content="New purpose description.",
            )
        ],
        summary="Updated purpose section",
        preserved_sections=[],
    )
    mocker.patch("src.workflows.fix_doc_incrementally", return_value=mock_fixes)

    # Create a documentation context
    from src.records import DocumentationContext

    test_doc_config = DOC_CONFIGS[DocType.MODULE_README]
    ctx = DocumentationContext(
        doc_config=test_doc_config,
        output_path=str(readme_path),
        analysis_path=str(tmp_path),
        analysis_depth=0,
    )

    # When: Fixing documentation drift
    fix_documentation_drift(
        llm_client=mock_llm_client,
        ctx=ctx,
        code_context="code context",
        drift_rationale="Test drift rationale",
        doc_type=DocType.MODULE_README,
        module_path=str(tmp_path),
        current_doc=current_doc_content,
    )

    # Then: README should be updated with incremental fixes
    updated_content = readme_path.read_text()
    assert "New purpose description" in updated_content
    assert "Old purpose description" not in updated_content


def test_check_documentation_drift_fix_with_drift(
    mocker: MockerFixture,
    tmp_path: Path,
    sample_drift_check_with_drift: DocumentationDriftCheck,
) -> None:
    """
    Test check_documentation_drift with fix=True auto-fixes drift without raising.
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
    mocker.patch("src.workflows.fix_documentation_drift")

    # When: Checking drift with fix=True and drift is detected
    # Then: Should not raise error (auto-fix mode)
    check_documentation_drift(target_module_path=str(module_dir), fix=True)


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
    mocker.patch("src.workflows.generate_doc")

    # Mock formatter
    mock_formatter = mocker.Mock(return_value="# Project Docs")
    test_doc_config = replace(
        DOC_CONFIGS[DocType.PROJECT_README], formatter=mock_formatter
    )
    mocker.patch.dict(
        "src.workflows.DOC_CONFIGS", {DocType.PROJECT_README: test_doc_config}
    )

    # When: Generating project README
    generate_documentation(
        target_module_path=str(repo_dir), doc_type=DocType.PROJECT_README
    )

    # Then: Should create README.md in repo root
    readme_path = repo_dir / "README.md"
    assert readme_path.exists()


def test_generate_documentation_project_readme_no_git_exits(
    mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test generate_documentation raises ValueError for PROJECT_README outside git."""
    mocker.patch("src.workflows.console")

    # When: Generating PROJECT_README outside git repository
    # Then: Should raise ValueError
    with pytest.raises(ValueError, match="not in a git repository"):
        generate_documentation(
            target_module_path=str(temp_module_dir), doc_type=DocType.PROJECT_README
        )


def test_prepare_documentation_context_analyze_repo_no_git_exits(
    mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test prepare_documentation_context exits for analyze_entire_repo without git."""
    from src.workflows import prepare_documentation_context

    mocker.patch("src.workflows.console")

    # Mock resolve_output_path to return successfully (bypass early check)
    mocker.patch(
        "src.workflows.resolve_output_path", return_value="/fake/path/README.md"
    )

    # Mock find_repo_root to return None (simulating no git repo found)
    mocker.patch("src.workflows.find_repo_root", return_value=None)

    # When: Preparing context for doc type with analyze_entire_repo=True but no git
    # Then: Should exit with code 1
    with pytest.raises(SystemExit) as exc_info:
        prepare_documentation_context(
            target_module_path=str(temp_module_dir),
            doc_type=DocType.PROJECT_README,
            depth=None,
        )

    assert exc_info.value.code == 1


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
    mocker.patch("src.workflows.generate_doc")

    # Mock formatter
    mock_formatter = mocker.Mock(return_value="# Style Guide")
    test_doc_config = replace(
        DOC_CONFIGS[DocType.STYLE_GUIDE], formatter=mock_formatter
    )
    mocker.patch.dict(
        "src.workflows.DOC_CONFIGS", {DocType.STYLE_GUIDE: test_doc_config}
    )

    # When: Generating style guide
    generate_documentation(
        target_module_path=str(repo_dir), doc_type=DocType.STYLE_GUIDE
    )

    # Then: Should create docs/style-guide.md
    style_guide_path = repo_dir / "docs" / "style-guide.md"
    assert style_guide_path.exists()
    assert (repo_dir / "docs").is_dir()


def test_generate_documentation_with_cli_depth_parameter(
    mocker: MockerFixture,
    tmp_path: Path,
    sample_drift_check_with_drift: DocumentationDriftCheck,
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test generate_documentation uses CLI depth parameter when provided."""
    # Create module dir with README
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    (module_dir / "README.md").write_text("# Old Docs")

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.initialize_llm")

    # Mock get_module_context to capture the depth parameter
    mock_get_context = mocker.patch(
        "src.workflows.get_module_context", return_value="code context"
    )
    mocker.patch(
        "src.workflows.check_drift", return_value=sample_drift_check_with_drift
    )
    mocker.patch("src.workflows.ask_human_intent", return_value=None)
    mocker.patch(
        "src.workflows.generate_doc", return_value=sample_component_documentation
    )

    # Mock formatter
    mock_formatter = mocker.Mock(return_value="# New Docs")
    test_doc_config = replace(
        DOC_CONFIGS[DocType.MODULE_README], formatter=mock_formatter
    )
    mocker.patch.dict(
        "src.workflows.DOC_CONFIGS", {DocType.MODULE_README: test_doc_config}
    )

    # When: Generating documentation with explicit depth parameter
    generate_documentation(target_module_path=str(module_dir), depth=2)

    # Then: get_module_context should be called with depth=2
    mock_get_context.assert_called_once()
    call_args = mock_get_context.call_args[1]
    assert call_args["depth"] == 2


def test_generate_documentation_with_config_file_depth(
    mocker: MockerFixture,
    tmp_path: Path,
    sample_drift_check_with_drift: DocumentationDriftCheck,
    sample_component_documentation: ModuleDocumentation,
) -> None:
    """Test generate_documentation uses config file_depth when CLI depth is None."""
    # Create module dir with README
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    (module_dir / "README.md").write_text("# Old Docs")

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.initialize_llm")

    # Mock config with file_depth setting
    mock_config = mocker.Mock()
    mock_config.file_depth = 3
    mocker.patch("src.workflows.load_config", return_value=mock_config)

    # Mock get_module_context to capture the depth parameter
    mock_get_context = mocker.patch(
        "src.workflows.get_module_context", return_value="code context"
    )
    mocker.patch(
        "src.workflows.check_drift", return_value=sample_drift_check_with_drift
    )
    mocker.patch("src.workflows.ask_human_intent", return_value=None)
    mocker.patch(
        "src.workflows.generate_doc", return_value=sample_component_documentation
    )

    # Mock formatter
    mock_formatter = mocker.Mock(return_value="# New Docs")
    test_doc_config = replace(
        DOC_CONFIGS[DocType.MODULE_README], formatter=mock_formatter
    )
    mocker.patch.dict(
        "src.workflows.DOC_CONFIGS", {DocType.MODULE_README: test_doc_config}
    )

    # When: Generating documentation without CLI depth (should use config)
    generate_documentation(target_module_path=str(module_dir))

    # Then: get_module_context should be called with depth=3 from config
    mock_get_context.assert_called_once()
    call_args = mock_get_context.call_args[1]
    assert call_args["depth"] == 3


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

    mocker.patch("src.workflows.load_config", return_value=DokkenConfig(modules=[]))

    with pytest.raises(SystemExit) as exc_info:
        check_multiple_modules_drift()

    assert exc_info.value.code == 1


def test_check_multiple_modules_drift_all_modules_pass(
    mocker: MockerFixture,
    tmp_path: Path,
    sample_drift_check_no_drift: DocumentationDriftCheck,
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

    mocker.patch(
        "src.workflows.load_config",
        return_value=DokkenConfig(modules=["src/module1", "src/module2"]),
    )

    # Mock check_documentation_drift to succeed (no exception)
    mocker.patch("src.workflows.check_documentation_drift")

    # When: Checking all modules with no drift
    # Then: Should complete without raising
    check_multiple_modules_drift()


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

    mocker.patch(
        "src.workflows.check_documentation_drift", side_effect=check_side_effect
    )

    # When: Checking all modules with one having drift
    # Then: Should raise DocumentationDriftError with details
    with pytest.raises(DocumentationDriftError) as exc_info:
        check_multiple_modules_drift()

    error_msg = str(exc_info.value)
    assert "1 module(s) have documentation drift" in error_msg
    assert "src/module2" in error_msg  # Module name in rationale
    assert "Test drift" in error_msg  # Individual rationale in error message


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

    mocker.patch(
        "src.workflows.load_config",
        return_value=DokkenConfig(modules=["src/module1", "src/nonexistent"]),
    )

    mocker.patch("src.workflows.check_documentation_drift")

    # When: Checking all modules with one nonexistent
    # Then: Should complete without raising (skips nonexistent)
    check_multiple_modules_drift()


def test_check_multiple_modules_drift_with_fix(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    """Test check_multiple_modules_drift with fix=True auto-fixes drift."""
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

    mocker.patch(
        "src.workflows.load_config",
        return_value=DokkenConfig(modules=["src/module1"]),
    )

    mocker.patch("src.workflows.check_documentation_drift")

    # When: Checking all modules with fix=True
    # Then: Should complete without raising (auto-fix mode)
    check_multiple_modules_drift(fix=True)


# Tests for error recovery and resilience


def test_generate_documentation_handles_write_errors(
    mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test generate_documentation handles file write errors."""
    import pytest

    # Mock LLM
    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code")

    mock_drift_check = DocumentationDriftCheck(drift_detected=True, rationale="No docs")
    mock_doc = ModuleDocumentation(
        component_name="Test",
        purpose_and_scope="Test",
        architecture_overview="Test",
        main_entry_points="Test",
        control_flow="Test",
        key_design_decisions="Test",
        external_dependencies="None",
    )

    mocker.patch("src.workflows.check_drift", return_value=mock_drift_check)
    mocker.patch("src.workflows.generate_doc", return_value=mock_doc)
    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.ask_human_intent", return_value=None)

    # Simulate write failure (permission denied)
    mocker.patch("builtins.open", side_effect=PermissionError("Permission denied"))

    # When: Generating documentation
    # Then: Should propagate the error
    with pytest.raises(PermissionError, match="Permission denied"):
        generate_documentation(target_module_path=str(temp_module_dir))


def test_check_documentation_drift_handles_corrupted_readme(
    mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test check_documentation_drift handles corrupted README files."""
    # Create a corrupted README (binary data)
    readme = temp_module_dir / "README.md"
    readme.write_bytes(b"\xff\xfe\x00\x01Invalid UTF-8")

    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code")
    mocker.patch("src.workflows.console")

    # When: Checking drift with corrupted README
    # Then: Should raise an error during file read
    import pytest

    with pytest.raises(UnicodeDecodeError):
        check_documentation_drift(target_module_path=str(temp_module_dir))


def test_generate_documentation_handles_llm_init_failure(
    mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test generate_documentation handles LLM initialization failure."""
    import pytest

    # Mock LLM initialization to fail
    mocker.patch(
        "src.workflows.initialize_llm",
        side_effect=ValueError("No API key found"),
    )
    mocker.patch("src.workflows.console")

    # When: Generating documentation
    # Then: Should propagate the error
    with pytest.raises(ValueError, match="No API key found"):
        generate_documentation(target_module_path=str(temp_module_dir))


def test_check_multiple_modules_drift_partial_failures(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    """Test check_multiple_modules_drift handles partial failures correctly."""
    import pytest

    # Create a git repo with multiple modules
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    # Create three modules
    for i in range(1, 4):
        module = repo_dir / f"module{i}"
        module.mkdir()
        (module / "README.md").write_text(f"# Module {i}")

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.find_repo_root", return_value=str(repo_dir))
    mocker.patch(
        "src.workflows.load_config",
        return_value=DokkenConfig(modules=["module1", "module2", "module3"]),
    )

    # Simulate different failures
    def check_side_effect(*args, **kwargs):
        module_path = kwargs["target_module_path"]
        if "module1" in module_path:
            # Module 1 passes
            return
        if "module2" in module_path:
            # Module 2 has drift
            raise DocumentationDriftError(
                rationale="Drift detected", module_path=module_path
            )
        # Module 3 has unexpected error
        raise RuntimeError("Unexpected LLM error")

    mocker.patch(
        "src.workflows.check_documentation_drift", side_effect=check_side_effect
    )

    # When: Checking all modules with mixed results
    # Then: Should stop at first unexpected error (not drift)
    with pytest.raises(RuntimeError, match="Unexpected LLM error"):
        check_multiple_modules_drift()


def test_generate_documentation_disk_full_error(
    mocker: MockerFixture, temp_module_dir: Path
) -> None:
    """Test generate_documentation handles disk full errors."""
    import pytest

    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code")
    mocker.patch("src.workflows.console")

    mock_drift = DocumentationDriftCheck(drift_detected=True, rationale="No docs")
    mock_doc = ModuleDocumentation(
        component_name="Test",
        purpose_and_scope="Test",
        architecture_overview="Test",
        main_entry_points="Test",
        control_flow="Test",
        key_design_decisions="Test",
        external_dependencies="None",
    )

    mocker.patch("src.workflows.check_drift", return_value=mock_drift)
    mocker.patch("src.workflows.generate_doc", return_value=mock_doc)
    mocker.patch("src.workflows.ask_human_intent", return_value=None)

    # Simulate disk full error
    mocker.patch("builtins.open", side_effect=OSError(28, "No space left on device"))

    # When: Generating documentation
    # Then: Should propagate the OSError
    with pytest.raises(OSError, match="No space left on device"):
        generate_documentation(target_module_path=str(temp_module_dir))
