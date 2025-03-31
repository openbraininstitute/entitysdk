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
    givenName: Annotated[
        str,
        Field(
            examples=["John", "Jane"],
            description="The given name of the person.",
        ),
    ]
    familyName: Annotated[
        str,
        Field(
            examples=["Doe", "Smith"],
            description="The family name of the person.",
        ),
    ]


class Organization(Agent):
    """Organization model."""

    type: Annotated[
        Literal["organization"],
        Field(
            default="organization",
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


AgentUnion = Annotated[Person | Organization, Field(discriminator="type")]
