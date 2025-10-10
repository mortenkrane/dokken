from typing import Dict, Optional

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
    design_decisions: Dict[str, str] = Field(
        ...,
        description=(
            "Key architectural decisions and the 'why' behind them, mapped to a short "
            "identifier (e.g., 'DB_CHOICE': 'We chose MongoDB over SQL for flexible "
            "schema management in the early phase.')."
        ),
    )
    external_dependencies: Optional[str] = Field(
        None,
        description=(
            "A list or summary of external systems/APIs this component interacts with."
        ),
    )
