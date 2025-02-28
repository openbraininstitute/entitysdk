"""Contribution models."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.agent import Organization, Person
from entitysdk.models.core import Identifiable, Struct


class Role(Identifiable):
    """Role model."""

    name: str = Field(..., description="The name of the role.")
    role_id: str = Field(
        ...,
        description="The role id.",
    )


class Contribution(Struct):
    """Contribution model."""

    agent: Annotated[Person | Organization, Field(discriminator="type")]
    role: Role = Field(..., description="The role of the contribution.")
