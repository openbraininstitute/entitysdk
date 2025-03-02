"""Agent models."""

from typing import Literal

from entitysdk.models.core import Identifiable


class Agent(Identifiable):
    """Agent model."""

    type: str
    pref_label: str


class Person(Agent):
    """Person model."""

    type: Literal["person"]
    familyName: str
    givenName: str


class Organization(Agent):
    """Organization model."""

    type: Literal["organization"]
    alternative_name: str
