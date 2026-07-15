"""Core models."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field

from entitysdk.models.base import BaseModel
from entitysdk.types import ID, AgentType
from entitysdk.utils.pydantic import RuntimeNullableField


class Struct(BaseModel):
    """Struct is a model with a frozen structure with no id."""


class Identifiable(BaseModel):
    """Identifiable is a model with an id."""

    id: Annotated[
        ID,
        RuntimeNullableField,
        Field(
            description="The primary key identifier of the resource.",
        ),
    ] = None  # type: ignore[assignment]
    creation_date: Annotated[
        datetime,
        RuntimeNullableField,
        Field(
            examples=[datetime(2025, 1, 1)],
            description="The date and time the resource was created.",
        ),
    ] = None  # type: ignore[assignment]
    update_date: Annotated[
        datetime,
        RuntimeNullableField,
        Field(
            examples=[datetime(2025, 1, 1)],
            description="The date and time the resource was last updated.",
        ),
    ] = None  # type: ignore[assignment]
    created_by: Annotated[
        "Person",
        RuntimeNullableField,
        Field(
            description="The agent that created this entity.",
        ),
    ] = None  # type: ignore[assignment]
    updated_by: Annotated[
        "Person",
        RuntimeNullableField,
        Field(
            description="The agent that updated this entity.",
        ),
    ] = None  # type: ignore[assignment]


class Agent(Identifiable):
    """Agent model."""

    type: Annotated[
        AgentType,
        Field(
            description="The type of this agent.",
        ),
    ]
    pref_label: Annotated[
        str,
        Field(
            description="The preferred label of the agent.",
        ),
    ]


class Person(Agent):
    """Person model."""

    type: Annotated[  # pyright: ignore[reportIncompatibleVariableOverride]
        Literal[AgentType.person],
        Field(
            description="The type of this agent. Should be 'agent'",
        ),
    ] = AgentType.person
    given_name: Annotated[
        str | None,
        Field(
            examples=["John", "Jane"],
            description="The given name of the person.",
        ),
    ] = None
    family_name: Annotated[
        str | None,
        Field(
            examples=["Doe", "Smith"],
            description="The family name of the person.",
        ),
    ] = None
    sub_id: Annotated[ID | None, Field(description="External subject id on Keycloak")] = None

    orcid: Annotated[str | None, Field(description="Open Researcher and Contributor ID")] = None


Identifiable.model_rebuild()


class Organization(Agent):
    """Organization model."""

    type: Annotated[  # pyright: ignore[reportIncompatibleVariableOverride]
        Literal[AgentType.organization],
        Field(
            description="The organization type. Should be 'organization'",
        ),
    ] = AgentType.organization
    alternative_name: Annotated[
        str | None,
        Field(
            examples=["Open Brain Institute"],
            description="The alternative name of the organization.",
        ),
    ] = None

    ror_id: Annotated[str | None, Field(description="Research Organization Registry Id")] = None


class Consortium(Agent):
    """Consortium model."""

    type: Annotated[  # pyright: ignore[reportIncompatibleVariableOverride]
        Literal[AgentType.consortium],
        Field(
            description="The Consortium type. Should be 'consortium'",
        ),
    ] = AgentType.consortium
    alternative_name: Annotated[
        str | None,
        Field(
            examples=["Open Brain Institute"],
            description="The alternative name of the consortium.",
        ),
    ] = None


AgentUnion = Annotated[Person | Organization | Consortium, Field(discriminator="type")]
