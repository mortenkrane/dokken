"""Tests for src/workflows.py"""

import pytest

from src.exceptions import DocumentationDriftError
from src.workflows import check_documentation_drift, generate_documentation


def test_check_documentation_drift_invalid_directory(mocker, tmp_path):
    """Test check_documentation_drift exits when given invalid directory."""
    mock_console = mocker.patch("src.workflows.console")
    invalid_path = str(tmp_path / "nonexistent")

    with pytest.raises(SystemExit) as exc_info:
        check_documentation_drift(target_module_path=invalid_path)

    assert exc_info.value.code == 1
    mock_console.print.assert_called_once()


def test_check_documentation_drift_no_code_context(mocker, temp_module_dir):
    """Test check_documentation_drift returns early when no code context."""
    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.initialize_llm")
    mock_get_context = mocker.patch("src.workflows.get_module_context", return_value="")

    # Should return early without raising
    check_documentation_drift(target_module_path=str(temp_module_dir))

    mock_get_context.assert_called_once()


def test_check_documentation_drift_no_readme_raises_error(mocker, temp_module_dir):
    """Test check_documentation_drift raises error when README.md doesn't exist."""
    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code context")

    with pytest.raises(DocumentationDriftError) as exc_info:
        check_documentation_drift(target_module_path=str(temp_module_dir))

    assert "No documentation exists" in str(exc_info.value)


def test_check_documentation_drift_no_drift_detected(
    mocker, tmp_path, sample_drift_check_no_drift
):
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
    mocker, tmp_path, sample_drift_check_with_drift
):
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


def test_generate_documentation_invalid_directory(mocker, tmp_path):
    """Test generate_documentation exits when given invalid directory."""
    mock_console = mocker.patch("src.workflows.console")
    invalid_path = str(tmp_path / "nonexistent")

    with pytest.raises(SystemExit) as exc_info:
        generate_documentation(target_module_path=invalid_path)

    assert exc_info.value.code == 1
    mock_console.print.assert_called_once()


def test_generate_documentation_calls_setup_git(mocker, temp_module_dir):
    """Test generate_documentation calls git setup."""
    mocker.patch("src.workflows.console")
    mock_setup_git = mocker.patch("src.workflows.setup_git")
    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="")

    generate_documentation(target_module_path=str(temp_module_dir))

    mock_setup_git.assert_called_once()


def test_generate_documentation_no_code_context(mocker, temp_module_dir):
    """Test generate_documentation returns early when no code context."""
    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.setup_git")
    mocker.patch("src.workflows.initialize_llm")
    mock_get_context = mocker.patch("src.workflows.get_module_context", return_value="")

    result = generate_documentation(target_module_path=str(temp_module_dir))

    assert result is None
    mock_get_context.assert_called_once()


def test_generate_documentation_no_drift_skips_generation(
    mocker, tmp_path, sample_drift_check_no_drift
):
    """Test generate_documentation skips generation when no drift detected."""
    # Create module dir with README
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    readme = module_dir / "README.md"
    readme.write_text("# Test\n\nDocumentation")

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.setup_git")
    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code context")
    mocker.patch("src.workflows.check_drift", return_value=sample_drift_check_no_drift)
    mock_generate_doc = mocker.patch("src.workflows.generate_doc")

    result = generate_documentation(target_module_path=str(module_dir))

    # Should not generate docs
    mock_generate_doc.assert_not_called()
    assert result is None


def test_generate_documentation_generates_when_drift(
    mocker, tmp_path, sample_drift_check_with_drift, sample_component_documentation
):
    """Test generate_documentation generates docs when drift detected."""
    # Create module dir with README
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    readme = module_dir / "README.md"
    readme.write_text("# Test\n\nDocumentation")

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.setup_git")
    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code context")
    mocker.patch(
        "src.workflows.check_drift", return_value=sample_drift_check_with_drift
    )
    mock_generate_doc = mocker.patch(
        "src.workflows.generate_doc", return_value=sample_component_documentation
    )
    mocker.patch("src.workflows.generate_markdown", return_value="# Markdown")

    result = generate_documentation(target_module_path=str(module_dir))

    mock_generate_doc.assert_called_once()
    assert result == "# Markdown"


def test_generate_documentation_writes_readme(
    mocker, tmp_path, sample_drift_check_with_drift, sample_component_documentation
):
    """Test generate_documentation writes README.md file."""
    # Create module dir with README
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    readme = module_dir / "README.md"
    readme.write_text("# Old Docs")

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.setup_git")
    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code context")
    mocker.patch(
        "src.workflows.check_drift", return_value=sample_drift_check_with_drift
    )
    mocker.patch(
        "src.workflows.generate_doc", return_value=sample_component_documentation
    )
    mocker.patch(
        "src.workflows.generate_markdown", return_value="# New Markdown Content"
    )

    generate_documentation(target_module_path=str(module_dir))

    # Verify README was written
    assert readme.read_text() == "# New Markdown Content"


def test_generate_documentation_creates_readme_if_missing(
    mocker,
    temp_module_dir,
    sample_drift_check_with_drift,
    sample_component_documentation,
):
    """Test generate_documentation creates README.md if it doesn't exist."""
    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.setup_git")
    mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="code context")
    # When no README exists, drift check will say drift detected
    mock_check_drift = mocker.patch(
        "src.workflows.check_drift", return_value=sample_drift_check_with_drift
    )
    mocker.patch(
        "src.workflows.generate_doc", return_value=sample_component_documentation
    )
    mocker.patch("src.workflows.generate_markdown", return_value="# New Docs")

    generate_documentation(target_module_path=str(temp_module_dir))

    readme_path = temp_module_dir / "README.md"
    assert readme_path.exists()
    assert readme_path.read_text() == "# New Docs"


@pytest.mark.parametrize(
    "base_branch",
    ["main", "develop", "master"],
)
def test_check_documentation_drift_uses_base_branch(
    mocker, tmp_path, sample_drift_check_no_drift, base_branch
):
    """Test check_documentation_drift uses correct base branch."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()
    readme = module_dir / "README.md"
    readme.write_text("# Test")

    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.initialize_llm")
    mock_get_context = mocker.patch(
        "src.workflows.get_module_context", return_value="code context"
    )
    mocker.patch("src.workflows.check_drift", return_value=sample_drift_check_no_drift)

    # Temporarily change GIT_BASE_BRANCH
    mocker.patch("src.workflows.GIT_BASE_BRANCH", base_branch)
    check_documentation_drift(target_module_path=str(module_dir))

    # Verify get_module_context was called with correct base_branch
    mock_get_context.assert_called_once()
    call_kwargs = mock_get_context.call_args[1]
    assert call_kwargs["base_branch"] == base_branch


def test_check_documentation_drift_initializes_llm(
    mocker, tmp_path, sample_drift_check_no_drift
):
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


def test_generate_documentation_initializes_llm(mocker, temp_module_dir):
    """Test generate_documentation initializes LLM."""
    mocker.patch("src.workflows.console")
    mocker.patch("src.workflows.setup_git")
    mock_init_llm = mocker.patch("src.workflows.initialize_llm")
    mocker.patch("src.workflows.get_module_context", return_value="")

    generate_documentation(target_module_path=str(temp_module_dir))

    mock_init_llm.assert_called_once()
