from pydantic import BaseModel, Field


class DocumentationDriftCheck(BaseModel):
    """
    Structured response for determining if documentation needs an update.
    """

    drift_detected: bool = Field(
        ...,
        description=(
            "True if ANY criteria-based checklist item applies (see "
            "DRIFT_CHECK_PROMPT). False if the documentation still accurately reflects "
            "the code."
        ),
    )
    rationale: str = Field(
        ...,
        description=(
            "A concise explanation referencing which specific checklist items "
            "triggered drift detection, or why the existing documentation remains "
            "adequate. Be specific about what changed."
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
            "boundaries (the 'what'). 2-3 paragraphs maximum."
        ),
    )
    architecture_overview: str = Field(
        ...,
        description=(
            "Description of the component's architecture: key modules, how they "
            "interact, data flow patterns, and overall structure. Focus on helping "
            "developers understand the system design."
        ),
    )
    main_entry_points: str = Field(
        ...,
        description=(
            "The primary functions, classes, or CLI commands that serve as entry "
            "points to this component. Explain what each entry point does and "
            "when developers would use it."
        ),
    )
    control_flow: str = Field(
        ...,
        description=(
            "How the component processes requests or executes operations from "
            "start to finish. Describe the key steps, decision points, and how "
            "data flows through the system. This helps developers trace "
            "execution paths."
        ),
    )
    key_design_decisions: str = Field(
        ...,
        description=(
            "The most important architectural and design choices made in this "
            "component, explained as a cohesive narrative. Focus on the 'why' "
            "behind patterns, technologies, or approaches used. Write in flowing "
            "prose, not bullet points or lists with prefixes."
        ),
    )
    external_dependencies: str | None = Field(
        None,
        description=(
            "External libraries, APIs, or systems this component depends on. Explain "
            "what each dependency is used for."
        ),
    )
