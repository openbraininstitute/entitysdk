"""Contribution models."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.agent import AgentUnion
from entitysdk.models.core import Identifiable


class Role(Identifiable):
    """Role model."""

    name: Annotated[
        str,
        Field(
            description="The name of the role.",
        ),
    ]
    role_id: Annotated[
        str,
        Field(
            description="The role id.",
        ),
    ]


class Contribution(Identifiable):
    """Contribution model."""

    agent: Annotated[
        AgentUnion,
        Field(
            description="The agent of the contribution.",
        ),
    ]
    role: Annotated[
        Role,
        Field(
            description="The role of the contribution.",
        ),
    ]
    entity: Annotated[
        "Entity | None",
        Field(description="The entity that resulted in this contribution."),
    ] = None


# Update forward reference for Entity
from entitysdk.models.entity import Entity  # noqa: E402

Contribution.model_rebuild(force=True)
