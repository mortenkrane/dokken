from pydantic import BaseModel, Field


class DocumentationDriftCheck(BaseModel):
    """
    Structured response for determining if documentation needs an update.
    """

    drift_detected: bool = Field(
        ...,
        description=(
            "True if the code changes (diff) make the current documentation obsolete "
            "or inaccurate. False otherwise."
        ),
    )
    rationale: str = Field(
        ...,
        description=(
            "A concise explanation of why drift was detected or why the existing "
            "documentation remains adequate."
        ),
    )


class ComponentDocumentation(BaseModel):
    """
    Structured documentation for a single code component.
    """

    component_name: str = Field(
        ...,
        description=(
            "The official, human-readable name of the component (e.g., 'User Auth "
            "Service')."
        ),
    )
    purpose_and_scope: str = Field(
        ...,
        description=(
            "A high-level explanation of what the component does and its system "
            "boundaries (the 'what')."
        ),
    )
    design_decisions: dict[str, str] = Field(
        ...,
        description=(
            "Key architectural decisions and the 'why' behind them, mapped to a short "
            "identifier (e.g., 'DB_CHOICE': 'We chose MongoDB over SQL for flexible "
            "schema management in the early phase.')."
        ),
    )
    external_dependencies: str | None = Field(
        None,
        description=(
            "A list or summary of external systems/APIs this component interacts with."
        ),
    )


class HumanIntent(BaseModel):
    """
    Human-provided intent and context for module documentation.
    Captures information that AI cannot infer from code alone.
    """

    problems_solved: str | None = Field(
        None,
        description="What problems does this module solve?",
    )
    core_responsibilities: str | None = Field(
        None,
        description="What are the module's core responsibilities?",
    )
    non_responsibilities: str | None = Field(
        None,
        description="What is not this module's responsibility?",
    )
    system_context: str | None = Field(
        None,
        description="How does the module fit into the larger system?",
    )
    entry_points: str | None = Field(
        None,
        description="What are the main entry points in the module?",
    )
    invariants: str | None = Field(
        None,
        description="What are the important invariants, assumptions, or contracts?",
    )
    limitations: str | None = Field(
        None,
        description="What are the module's known limitations?",
    )
    common_pitfalls: str | None = Field(
        None,
        description="What are common pitfalls for contributors?",
    )
