"""Core models."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field

from entitysdk.models.base import BaseModel

# Identifiable models use a single Pydantic class for every lifecycle stage (staging,
# registration, fetch, update). At runtime, ``id`` is often unset:
#
# - new entities built in memory before ``register_entity``
# - JSON payloads with ``"id": null`` or the field omitted
# - nested models deserialized before the server assigns an id
#
# After a successful fetch, callers rely on static checkers treating ``res.id`` as
# ``ID``, not ``ID | None`` (for example ``id_res: ID = res.id`` in client code).
#
# A plain ``id: ID | None`` annotation would be honest at runtime but would force
# every consumer to narrow or assert, even right after ``get_entity``. Conversely,
# ``id: ID = Field(default=None)`` satisfies pyright but Pydantic v2 rejects
# ``None`` values because ``ID`` is not nullable in the core schema.
#
# ``Annotated[ID, RuntimeNullableField, Field(default=None)]`` bridges that gap:
#
# - the annotated type stays ``ID``, so pyright reports ``.id`` as ``ID``
# - ``RuntimeNullableField`` wraps the UUID schema with ``nullable_schema``, so
#   Pydantic accepts ``None``, an explicit ``id=None``, and ``"id": null`` in JSON
# - ``Field(default=None)`` keeps the default unset for staging and registration
#
# The ``type: ignore[assignment]`` on ``Identifiable.id`` applies only to the
# default ``= None``, not to uses of ``.id`` afterward.
from entitysdk.models.fields import RuntimeNullableField
from entitysdk.types import ID, AgentType


class Struct(BaseModel):
    """Struct is a model with a frozen structure with no id."""


class Identifiable(BaseModel):
    """Identifiable is a model with an id."""

    id: Annotated[
        ID,
        RuntimeNullableField,
        Field(
            description="The primary key identifier of the resource.",
            default=None,
        ),
    ] = None  # type: ignore[assignment]
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
