"""Agent models."""

from pydantic import Field

from entitysdk.models.core import Struct


class Person(Struct):
    """Person model."""

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
    pref_label: str = Field(
        ...,
        examples=["John Doe", "Jane Smith"],
        description="The preferred label of the person.",
    )


class Organization(Struct):
    """Organization model."""

    pref_label: str = Field(
        ...,
        examples=["Open Brain Institute"],
        description="The preferred label of the organization.",
    )
    alternative_name: str | None = Field(
        default=None,
        examples=["Open Brain Institute"],
        description="The alternative name of the organization.",
    )
