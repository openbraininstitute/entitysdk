"""Core models."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import MISSING, Field

from entitysdk.models.base import BaseModel
from entitysdk.types import ID, AgentType
from entitysdk.utils.pydantic import RuntimeNullableField


class Struct(BaseModel):
    """Struct is a model with a frozen structure with no id."""


class PlatformUser(BaseModel):
    """A registered user of the platform."""

    id: Annotated[
        ID,
        Field(description="Keycloak subject ID of the platform user."),
    ]
    creation_date: Annotated[
        datetime,
        Field(description="When the platform user was created."),
    ]
    update_date: Annotated[
        datetime,
        Field(description="When the platform user was last updated."),
    ]
    pref_label: Annotated[
        str,
        Field(description="Human-readable display name of the platform user."),
    ]


class Identifiable(BaseModel):
    """Identifiable is a model with an id."""

    # Annotate as T for checkers (not T | MISSING — pyright does not erase it).
    # id: entitycore always sends a concrete UUID on read; MISSING only for create.
    id: Annotated[
        ID,
        Field(
            description="The primary key identifier of the resource.",
        ),
    ] = MISSING  # type: ignore[assignment]
    # Timestamps/users: present on IdentifiableRead, omitted on AssetRead and some
    # nested stubs — RuntimeNullable keeps annotation as T while allowing omit/null.
    creation_date: Annotated[
        datetime,
        RuntimeNullableField,
        Field(
            examples=[datetime(2025, 1, 1)],
            description="The date and time the resource was created.",
        ),
    ] = MISSING  # type: ignore[assignment]
    update_date: Annotated[
        datetime,
        RuntimeNullableField,
        Field(
            examples=[datetime(2025, 1, 1)],
            description="The date and time the resource was last updated.",
        ),
    ] = MISSING  # type: ignore[assignment]
    created_by: Annotated[
        PlatformUser,
        RuntimeNullableField,
        Field(
            description="The platform user who created this resource.",
        ),
    ] = MISSING  # type: ignore[assignment]
    updated_by: Annotated[
        PlatformUser,
        RuntimeNullableField,
        Field(
            description="The platform user who last updated this resource.",
        ),
    ] = MISSING  # type: ignore[assignment]


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
    ] = MISSING  # type: ignore[assignment]
    family_name: Annotated[
        str | None,
        Field(
            examples=["Doe", "Smith"],
            description="The family name of the person.",
        ),
    ] = MISSING  # type: ignore[assignment]
    sub_id: Annotated[ID | None, Field(description="External subject id on Keycloak")] = MISSING  # type: ignore[assignment]

    orcid: Annotated[str | None, Field(description="Open Researcher and Contributor ID")] = MISSING  # type: ignore[assignment]


class Organization(Agent):
    """Organization model."""

    type: Annotated[  # pyright: ignore[reportIncompatibleVariableOverride]
        Literal[AgentType.organization],
        Field(
            description="The organization type. Should be 'organization'",
        ),
    ] = AgentType.organization
    alternative_name: Annotated[
        str,
        Field(
            examples=["Open Brain Institute"],
            description="The alternative name of the organization.",
        ),
    ]
    ror_id: Annotated[str | None, Field(description="Research Organization Registry Id")] = MISSING  # type: ignore[assignment]


class Consortium(Agent):
    """Consortium model."""

    type: Annotated[  # pyright: ignore[reportIncompatibleVariableOverride]
        Literal[AgentType.consortium],
        Field(
            description="The Consortium type. Should be 'consortium'",
        ),
    ] = AgentType.consortium
    alternative_name: Annotated[
        str,
        Field(
            examples=["Open Brain Institute"],
            description="The alternative name of the consortium.",
        ),
    ]


AgentUnion = Annotated[Person | Organization | Consortium, Field(discriminator="type")]
