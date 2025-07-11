"""Entity model."""

from typing import Annotated
from uuid import UUID

from pydantic import Field

from entitysdk.mixin import HasAssets
from entitysdk.models.agent import AgentUnion
from entitysdk.models.core import Identifiable
from entitysdk.types import ID, EntityType


class Entity(Identifiable, HasAssets):
    """Entity is a model with id and authorization."""

    name: Annotated[
        str | None,
        Field(
            examples=["Entity 1"],
            description="The name of the entity.",
        ),
    ] = None
    description: Annotated[
        str | None,
        Field(
            examples=["This is entity 1"],
            description="The description of the entity.",
        ),
    ] = None
    type: Annotated[
        EntityType | None,
        Field(
            examples=["license"],
            description="The type of this Entity.",
        ),
    ] = None
    created_by: Annotated[
        AgentUnion | None,
        Field(description="The agent that created this entity."),
    ] = None
    updated_by: Annotated[
        AgentUnion | None,
        Field(
            description="The agent that updated this entity.",
        ),
    ] = None
    authorized_public: Annotated[
        bool,
        Field(
            examples=[True, False],
            description="Whether the resource is authorized to be public.",
        ),
    ] = False
    authorized_project_id: Annotated[
        ID | None,
        Field(
            examples=[UUID("12345678-1234-1234-1234-123456789012")],
            description="The project ID the resource is authorized to be public.",
        ),
    ] = None
    contributions: Annotated[
        "list[Contribution] | None", Field(description="The constributions for this entity.")
    ] = None
    legacy_id: Annotated[
        list[str] | None,
        Field(description="Legacy NEXUS ids."),
    ] = None


# Update forward reference for Contribution
from entitysdk.models.contribution import Contribution  # noqa: E402

Entity.model_rebuild(force=True)
