"""Agent models."""

from typing import Literal

from pydantic import Field

from entitysdk.models.core import Identifiable


class Agent(Identifiable):
    """Agent model."""

    type: str = Field(
        ...,
        description="The type of this agent.",
    )
    pref_label: str = Field(
        ...,
        description="The preferred label of the agent.",
    )


class Person(Agent):
    """Person model."""

    type: Literal["person"] = Field(
        default="person", description="The type of this agent. Should be 'agent'"
    )
    givenName: str = Field(
        ...,
        examples=["John", "Jane"],
        description="The given name of the person.",
    )
    familyName: str = Field(
        ...,
        examples=["Doe", "Smith"],
        description="The family name of the person.",
    )


class Organization(Agent):
    """Organization model."""

    type: Literal["organization"] = Field(
        default="organization",
        description="The organization type. Should be 'organization'",
    )
    alternative_name: str | None = Field(
        default=None,
        examples=["Open Brain Institute"],
        description="The alternative name of the organization.",
    )
