"""Agent models."""

from typing import Annotated, Literal

from pydantic import Field

from entitysdk.models.core import Identifiable


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
