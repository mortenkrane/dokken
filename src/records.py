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


class ModuleDocumentation(BaseModel):
    """
    Structured documentation for a module (architectural design).
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


class ProjectDocumentation(BaseModel):
    """
    Structured documentation for a top-level project README.
    """

    project_name: str = Field(
        ...,
        description="The name of the project.",
    )
    project_purpose: str = Field(
        ...,
        description=(
            "What problem does this project solve? Why does it exist? "
            "2-3 paragraphs introducing the project to new users."
        ),
    )
    key_features: str = Field(
        ...,
        description=(
            "Main capabilities of the project. Bulleted list of 3-7 features "
            "that users should know about."
        ),
    )
    installation: str = Field(
        ...,
        description=(
            "How users install and set up the project for usage. Include "
            "prerequisites, installation steps, and basic configuration."
        ),
    )
    development_setup: str = Field(
        ...,
        description=(
            "How contributors set up the project for development. Include "
            "installing dependencies, running tests, and any dev tools."
        ),
    )
    usage_examples: str = Field(
        ...,
        description=(
            "Basic usage patterns and commands. Show the most common use "
            "cases with concrete examples."
        ),
    )
    project_structure: str = Field(
        ...,
        description=(
            "High-level overview of directory organization. Help users "
            "understand where to find different components."
        ),
    )
    contributing: str | None = Field(
        None,
        description=(
            "How to contribute to the project (optional). Include PR process, "
            "coding standards, or link to CONTRIBUTING.md if applicable."
        ),
    )


class StyleGuideDocumentation(BaseModel):
    """
    Structured documentation for code style and conventions.
    """

    project_name: str = Field(
        ...,
        description="The name of the project.",
    )
    languages: list[str] = Field(
        ...,
        description="Programming languages used in this project.",
    )
    code_style_patterns: str = Field(
        ...,
        description=(
            "Formatting, naming conventions, and code structure patterns "
            "consistently used across the codebase. Include specific examples."
        ),
    )
    architectural_patterns: str = Field(
        ...,
        description=(
            "Design patterns, abstractions, and architectural approaches "
            "used in the codebase. Explain dependency injection, data flow, "
            "separation of concerns, etc."
        ),
    )
    testing_conventions: str = Field(
        ...,
        description=(
            "Test structure, mocking patterns, fixtures, and testing practices. "
            "Explain how tests are organized and what patterns to follow."
        ),
    )
    git_workflow: str = Field(
        ...,
        description=(
            "Branching strategy, commit message format, PR process, and "
            "version control practices. Include any commit conventions."
        ),
    )
    module_organization: str = Field(
        ...,
        description=(
            "How code is organized into modules, packages, and files. "
            "Explain the directory structure and module responsibilities."
        ),
    )
    dependencies_management: str = Field(
        ...,
        description=(
            "How dependencies are declared, managed, and versioned. "
            "Include package management tools and practices."
        ),
    )


# Intent models for human-in-the-loop


class ModuleIntent(BaseModel):
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


class ProjectIntent(BaseModel):
    """
    Human-provided intent and context for project README documentation.
    """

    project_type: str | None = Field(
        None,
        description="Is this a library/tool/application/framework?",
    )
    target_audience: str | None = Field(
        None,
        description="Who is the primary audience?",
    )
    key_problem: str | None = Field(
        None,
        description="What problem does this project solve?",
    )
    setup_notes: str | None = Field(
        None,
        description="Any special setup considerations?",
    )


class StyleGuideIntent(BaseModel):
    """
    Human-provided intent and context for style guide documentation.
    """

    unique_conventions: str | None = Field(
        None,
        description="Are there any unique conventions in this codebase?",
    )
    organization_notes: str | None = Field(
        None,
        description="What should new contributors know about code organization?",
    )
    patterns: str | None = Field(
        None,
        description="Are there specific patterns to follow or avoid?",
    )


# Backward compatibility aliases
ComponentDocumentation = ModuleDocumentation  # Deprecated: use ModuleDocumentation
HumanIntent = ModuleIntent  # Deprecated: use ModuleIntent
