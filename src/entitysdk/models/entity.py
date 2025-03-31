"""Entity model."""

from typing import Annotated
from uuid import UUID

from pydantic import Field

from entitysdk.models.agent import AgentUnion
from entitysdk.models.core import Identifiable


class Entity(Identifiable):
    """Entity is a model with id and authorization."""

    createdBy: Annotated[
        AgentUnion | None,
        Field(description="The agent that created this entity."),
    ] = None
    updatedBy: Annotated[
        AgentUnion | None,
        Field(
            description="The agent that updated this entity.",
        ),
    ] = None
    authorized_public: Annotated[
        bool | None,
        Field(
            examples=[True, False],
            description="Whether the resource is authorized to be public.",
        ),
    ] = None
    authorized_project_id: Annotated[
        UUID | None,
        Field(
            examples=[UUID("12345678-1234-1234-1234-123456789012")],
            description="The project ID the resource is authorized to be public.",
        ),
    ] = None
