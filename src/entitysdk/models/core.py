"""Core models."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field

from entitysdk.models.base import BaseModel
from entitysdk.types import ID


class Struct(BaseModel):
    """Struct is a model with a frozen structure with no id."""


class Identifiable(BaseModel):
    """Identifiable is a model with an id."""

    id: Annotated[
        ID | None,
        Field(
            description="The primary key identifier of the resource.",
        ),
    ] = None
    creation_date: Annotated[
        datetime | None,
        Field(
            examples=[datetime(2025, 1, 1)],
            description="The date and time the resource was created.",
        ),
    ] = None
    update_date: Annotated[
        datetime | None,
        Field(
            examples=[datetime(2025, 1, 1)],
            description="The date and time the resource was last updated.",
        ),
    ] = None
    created_by: Annotated[
        "Person | None",
        Field(description="The agent that created this entity."),
    ] = None
    updated_by: Annotated[
        "Person | None",
        Field(
            description="The agent that updated this entity.",
        ),
    ] = None


class Agent(Identifiable):
    """Agent model."""

    type: Annotated[
        str,
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

    type: Annotated[
        Literal["person"],
        Field(
            description="The type of this agent. Should be 'agent'",
        ),
    ] = "person"
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


# update forward reference in Identifiable's created_by/uodated_by
Identifiable.model_rebuild()


class Organization(Agent):
    """Organization model."""

    type: Annotated[
        Literal["organization"],
        Field(
            description="The organization type. Should be 'organization'",
        ),
    ] = "organization"
    alternative_name: Annotated[
        str | None,
        Field(
            examples=["Open Brain Institute"],
            description="The alternative name of the organization.",
        ),
    ] = None


class Consortium(Agent):
    """Consortium model."""

    type: Annotated[
        Literal["consortium"],
        Field(
            description="The Consortium type. Should be 'consortium'",
        ),
    ] = "consortium"
    alternative_name: Annotated[
        str | None,
        Field(
            examples=["Open Brain Institute"],
            description="The alternative name of the consortium.",
        ),
    ] = None


AgentUnion = Annotated[Person | Organization | Consortium, Field(discriminator="type")]
