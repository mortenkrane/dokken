"""Tests for Pydantic models in src/records.py."""

import pytest
from pydantic import ValidationError

from src.records import (
    DocumentationDriftCheck,
    ModuleDocumentation,
    ModuleIntent,
    ProjectDocumentation,
    ProjectIntent,
    StyleGuideDocumentation,
    StyleGuideIntent,
)

# DocumentationDriftCheck Tests


def test_documentation_drift_check_valid_creation() -> None:
    """Test that DocumentationDriftCheck can be created with valid data."""
    drift_check = DocumentationDriftCheck(
        drift_detected=True,
        rationale="The function signature changed from foo(x) to foo(x, y).",
    )
    assert drift_check.drift_detected is True
    assert (
        drift_check.rationale
        == "The function signature changed from foo(x) to foo(x, y)."
    )


def test_documentation_drift_check_no_drift() -> None:
    """Test DocumentationDriftCheck with no drift detected."""
    drift_check = DocumentationDriftCheck(
        drift_detected=False,
        rationale="Documentation accurately reflects the current implementation.",
    )
    assert drift_check.drift_detected is False
    assert "accurately reflects" in drift_check.rationale


def test_documentation_drift_check_missing_drift_detected() -> None:
    """Test that DocumentationDriftCheck requires drift_detected field."""
    with pytest.raises(ValidationError) as exc_info:
        DocumentationDriftCheck(rationale="Missing drift_detected field")

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("drift_detected",) for error in errors)
    assert any(error["type"] == "missing" for error in errors)


def test_documentation_drift_check_missing_rationale() -> None:
    """Test that DocumentationDriftCheck requires rationale field."""
    with pytest.raises(ValidationError) as exc_info:
        DocumentationDriftCheck(drift_detected=True)

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("rationale",) for error in errors)
    assert any(error["type"] == "missing" for error in errors)


def test_documentation_drift_check_invalid_drift_detected_type() -> None:
    """Test that DocumentationDriftCheck validates drift_detected type."""
    with pytest.raises(ValidationError) as exc_info:
        DocumentationDriftCheck(
            drift_detected=["not", "a", "bool"],  # type: ignore[arg-type]
            rationale="Test rationale",
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("drift_detected",) for error in errors)


def test_documentation_drift_check_invalid_rationale_type() -> None:
    """Test that DocumentationDriftCheck validates rationale type."""
    with pytest.raises(ValidationError) as exc_info:
        DocumentationDriftCheck(
            drift_detected=True,
            rationale=123,  # type: ignore[arg-type]
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("rationale",) for error in errors)


# ModuleDocumentation Tests


def test_module_documentation_valid_creation() -> None:
    """Test that ModuleDocumentation can be created with all required fields."""
    doc = ModuleDocumentation(
        component_name="User Authentication Service",
        purpose_and_scope="Handles user login and session management.",
        architecture_overview="Uses JWT tokens with Redis for session storage.",
        main_entry_points="authenticate(), create_session(), verify_token()",
        control_flow="Request → Validate credentials → Generate token → Store session",
        key_design_decisions="We chose JWT for stateless authentication.",
    )
    assert doc.component_name == "User Authentication Service"
    assert doc.purpose_and_scope == "Handles user login and session management."
    assert doc.control_flow_diagram is None  # Optional field
    assert doc.external_dependencies is None  # Optional field


def test_module_documentation_with_optional_fields() -> None:
    """Test that ModuleDocumentation accepts optional fields."""
    doc = ModuleDocumentation(
        component_name="User Auth",
        purpose_and_scope="Handles auth",
        architecture_overview="JWT-based",
        main_entry_points="authenticate()",
        control_flow="Request → Validate → Token",
        key_design_decisions="JWT for stateless auth",
        control_flow_diagram="graph TD; A-->B;",
        external_dependencies="Redis, PyJWT",
    )
    assert doc.control_flow_diagram == "graph TD; A-->B;"
    assert doc.external_dependencies == "Redis, PyJWT"


def test_module_documentation_missing_required_field() -> None:
    """Test that ModuleDocumentation requires all mandatory fields."""
    with pytest.raises(ValidationError) as exc_info:
        ModuleDocumentation(
            component_name="User Auth",
            purpose_and_scope="Handles auth",
            # Missing architecture_overview
            main_entry_points="authenticate()",
            control_flow="Request → Validate",
            key_design_decisions="JWT",
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("architecture_overview",) for error in errors)
    assert any(error["type"] == "missing" for error in errors)


@pytest.mark.parametrize(
    "field_name",
    [
        "component_name",
        "purpose_and_scope",
        "architecture_overview",
        "main_entry_points",
        "control_flow",
        "key_design_decisions",
    ],
)
def test_module_documentation_all_required_fields(field_name: str) -> None:
    """Test that each required field in ModuleDocumentation is validated."""
    valid_data = {
        "component_name": "Test Component",
        "purpose_and_scope": "Test purpose",
        "architecture_overview": "Test architecture",
        "main_entry_points": "Test entry points",
        "control_flow": "Test flow",
        "key_design_decisions": "Test decisions",
    }

    # Remove one field at a time
    invalid_data = {k: v for k, v in valid_data.items() if k != field_name}

    with pytest.raises(ValidationError) as exc_info:
        ModuleDocumentation(**invalid_data)

    errors = exc_info.value.errors()
    assert any(error["loc"] == (field_name,) for error in errors)
    assert any(error["type"] == "missing" for error in errors)


def test_module_documentation_invalid_type() -> None:
    """Test that ModuleDocumentation validates field types."""
    with pytest.raises(ValidationError) as exc_info:
        ModuleDocumentation(
            component_name=123,  # type: ignore[arg-type]
            purpose_and_scope="Test",
            architecture_overview="Test",
            main_entry_points="Test",
            control_flow="Test",
            key_design_decisions="Test",
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("component_name",) for error in errors)


# ProjectDocumentation Tests


def test_project_documentation_valid_creation() -> None:
    """Test that ProjectDocumentation can be created with valid data."""
    doc = ProjectDocumentation(
        project_name="Dokken",
        project_purpose="AI-powered documentation generation tool.",
        key_features="- Drift detection\n- Auto-generation",
        installation="pip install dokken",
        development_setup="uv sync --all-groups",
        usage_examples="dokken check src/",
        project_structure="src/ - Source code\ntests/ - Tests",
    )
    assert doc.project_name == "Dokken"
    assert doc.contributing is None  # Optional field


def test_project_documentation_with_contributing() -> None:
    """Test ProjectDocumentation with optional contributing field."""
    doc = ProjectDocumentation(
        project_name="Dokken",
        project_purpose="Tool",
        key_features="Features",
        installation="Install",
        development_setup="Setup",
        usage_examples="Examples",
        project_structure="Structure",
        contributing="See CONTRIBUTING.md",
    )
    assert doc.contributing == "See CONTRIBUTING.md"


def test_project_documentation_missing_required_field() -> None:
    """Test that ProjectDocumentation requires all mandatory fields."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectDocumentation(
            project_name="Dokken",
            project_purpose="Tool",
            # Missing key_features
            installation="Install",
            development_setup="Setup",
            usage_examples="Examples",
            project_structure="Structure",
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("key_features",) for error in errors)


# StyleGuideDocumentation Tests


def test_style_guide_documentation_valid_creation() -> None:
    """Test that StyleGuideDocumentation can be created with valid data."""
    doc = StyleGuideDocumentation(
        project_name="Dokken",
        languages=["Python"],
        code_style_patterns="PEP 8 compliant",
        architectural_patterns="Dependency injection",
        testing_conventions="Function-based tests",
        git_workflow="Conventional commits",
        module_organization="Flat structure",
        dependencies_management="UV for package management",
    )
    assert doc.project_name == "Dokken"
    assert doc.languages == ["Python"]
    assert len(doc.languages) == 1


def test_style_guide_documentation_multiple_languages() -> None:
    """Test StyleGuideDocumentation with multiple languages."""
    doc = StyleGuideDocumentation(
        project_name="MultiLang",
        languages=["Python", "TypeScript", "Rust"],
        code_style_patterns="Patterns",
        architectural_patterns="Patterns",
        testing_conventions="Conventions",
        git_workflow="Workflow",
        module_organization="Organization",
        dependencies_management="Management",
    )
    assert len(doc.languages) == 3
    assert "TypeScript" in doc.languages


def test_style_guide_documentation_invalid_languages_type() -> None:
    """Test that StyleGuideDocumentation validates languages type."""
    with pytest.raises(ValidationError) as exc_info:
        StyleGuideDocumentation(
            project_name="Test",
            languages="Python",  # type: ignore[arg-type]
            code_style_patterns="Patterns",
            architectural_patterns="Patterns",
            testing_conventions="Conventions",
            git_workflow="Workflow",
            module_organization="Organization",
            dependencies_management="Management",
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("languages",) for error in errors)


def test_style_guide_documentation_empty_languages() -> None:
    """Test StyleGuideDocumentation with empty languages list."""
    doc = StyleGuideDocumentation(
        project_name="Test",
        languages=[],  # Empty list is valid
        code_style_patterns="Patterns",
        architectural_patterns="Patterns",
        testing_conventions="Conventions",
        git_workflow="Workflow",
        module_organization="Organization",
        dependencies_management="Management",
    )
    assert doc.languages == []


# Intent Model Tests


def test_module_intent_all_fields_optional() -> None:
    """Test that ModuleIntent can be created with no fields."""
    intent = ModuleIntent()
    assert intent.problems_solved is None
    assert intent.core_responsibilities is None
    assert intent.non_responsibilities is None
    assert intent.system_context is None


def test_module_intent_with_all_fields() -> None:
    """Test that ModuleIntent can be created with all fields populated."""
    intent = ModuleIntent(
        problems_solved="Solves auth issues",
        core_responsibilities="Handle login",
        non_responsibilities="Does not handle billing",
        system_context="Part of user service",
    )
    assert intent.problems_solved == "Solves auth issues"
    assert intent.core_responsibilities == "Handle login"
    assert intent.non_responsibilities == "Does not handle billing"
    assert intent.system_context == "Part of user service"


def test_module_intent_partial_fields() -> None:
    """Test that ModuleIntent can be created with partial fields."""
    intent = ModuleIntent(
        problems_solved="Solves auth",
        system_context="User service",
    )
    assert intent.problems_solved == "Solves auth"
    assert intent.core_responsibilities is None
    assert intent.system_context == "User service"


def test_project_intent_all_fields_optional() -> None:
    """Test that ProjectIntent can be created with no fields."""
    intent = ProjectIntent()
    assert intent.project_type is None
    assert intent.target_audience is None
    assert intent.key_problem is None
    assert intent.setup_notes is None


def test_project_intent_with_all_fields() -> None:
    """Test that ProjectIntent can be created with all fields populated."""
    intent = ProjectIntent(
        project_type="CLI tool",
        target_audience="Developers",
        key_problem="Documentation drift",
        setup_notes="Requires API key",
    )
    assert intent.project_type == "CLI tool"
    assert intent.target_audience == "Developers"
    assert intent.key_problem == "Documentation drift"
    assert intent.setup_notes == "Requires API key"


def test_style_guide_intent_all_fields_optional() -> None:
    """Test that StyleGuideIntent can be created with no fields."""
    intent = StyleGuideIntent()
    assert intent.unique_conventions is None
    assert intent.organization_notes is None
    assert intent.patterns is None


def test_style_guide_intent_with_all_fields() -> None:
    """Test that StyleGuideIntent can be created with all fields populated."""
    intent = StyleGuideIntent(
        unique_conventions="Use ruff for linting",
        organization_notes="Flat module structure",
        patterns="Dependency injection preferred",
    )
    assert intent.unique_conventions == "Use ruff for linting"
    assert intent.organization_notes == "Flat module structure"
    assert intent.patterns == "Dependency injection preferred"


# Type coercion tests


def test_module_documentation_optional_field_type_validation() -> None:
    """Test that optional fields still validate types when provided."""
    with pytest.raises(ValidationError) as exc_info:
        ModuleDocumentation(
            component_name="Test",
            purpose_and_scope="Test",
            architecture_overview="Test",
            main_entry_points="Test",
            control_flow="Test",
            key_design_decisions="Test",
            control_flow_diagram=123,  # Should be str | None  # type: ignore[arg-type]
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("control_flow_diagram",) for error in errors)


def test_project_documentation_optional_field_type_validation() -> None:
    """Test that optional fields still validate types when provided."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectDocumentation(
            project_name="Test",
            project_purpose="Test",
            key_features="Test",
            installation="Test",
            development_setup="Test",
            usage_examples="Test",
            project_structure="Test",
            contributing=[
                "Not",
                "a",
                "string",
            ],  # Should be str | None  # type: ignore[arg-type]
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("contributing",) for error in errors)


def test_intent_model_type_validation() -> None:
    """Test that Intent models validate field types."""
    with pytest.raises(ValidationError) as exc_info:
        ModuleIntent(
            problems_solved=123,  # Should be str | None  # type: ignore[arg-type]
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("problems_solved",) for error in errors)


# Edge case tests


def test_module_documentation_with_empty_strings() -> None:
    """Test that ModuleDocumentation accepts empty strings for required fields."""
    # Pydantic by default accepts empty strings unless we add min_length validator
    doc = ModuleDocumentation(
        component_name="",  # Empty string is currently valid
        purpose_and_scope="",
        architecture_overview="",
        main_entry_points="",
        control_flow="",
        key_design_decisions="",
    )
    assert doc.component_name == ""
    assert doc.purpose_and_scope == ""


def test_style_guide_documentation_languages_with_numbers() -> None:
    """Test that languages list can contain language names with numbers."""
    doc = StyleGuideDocumentation(
        project_name="Test",
        languages=["Python3", "C++17", "ES2020"],
        code_style_patterns="Patterns",
        architectural_patterns="Patterns",
        testing_conventions="Conventions",
        git_workflow="Workflow",
        module_organization="Organization",
        dependencies_management="Management",
    )
    assert "C++17" in doc.languages
    assert len(doc.languages) == 3


def test_documentation_drift_check_with_unicode() -> None:
    """Test that DocumentationDriftCheck handles Unicode in rationale."""
    drift_check = DocumentationDriftCheck(
        drift_detected=True,
        rationale="The function was renamed: café → coffee ☕",
    )
    assert "☕" in drift_check.rationale
    assert "café" in drift_check.rationale


def test_module_documentation_serialization() -> None:
    """Test that ModuleDocumentation can be serialized to dict."""
    doc = ModuleDocumentation(
        component_name="Test",
        purpose_and_scope="Test purpose",
        architecture_overview="Test arch",
        main_entry_points="Test entry",
        control_flow="Test flow",
        key_design_decisions="Test decisions",
    )
    doc_dict = doc.model_dump()
    assert isinstance(doc_dict, dict)
    assert doc_dict["component_name"] == "Test"
    assert doc_dict["control_flow_diagram"] is None


def test_style_guide_documentation_json_serialization() -> None:
    """Test that StyleGuideDocumentation can be serialized to JSON."""
    doc = StyleGuideDocumentation(
        project_name="Test",
        languages=["Python", "Rust"],
        code_style_patterns="Patterns",
        architectural_patterns="Patterns",
        testing_conventions="Conventions",
        git_workflow="Workflow",
        module_organization="Organization",
        dependencies_management="Management",
    )
    json_str = doc.model_dump_json()
    assert isinstance(json_str, str)
    assert "Python" in json_str
    assert "Rust" in json_str
