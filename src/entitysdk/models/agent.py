"""Agent models."""

from typing import ClassVar

from entitysdk.core import Struct


class Person(Struct):
    """Person model."""

    __route__: ClassVar[str] = "person"

    givenName: str
    familyName: str
    pref_label: str


class Organization(Struct):
    """Organization model."""

    __route__: ClassVar[str] = "organization"

    pref_label: str
    alternative_name: str | None = None
