"""Contribution models."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.agent import Organization, Person
from entitysdk.models.core import Identifiable, Struct


class Role(Identifiable):
    """Role model."""

    name: str
    role_id: str


class Contribution(Struct):
    """Contribution model."""

    agent: Annotated[Person | Organization, Field(discriminator="type")]
    role: Role
