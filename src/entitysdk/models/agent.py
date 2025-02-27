"""Agent models."""

from entitysdk.models.core import Struct


class Person(Struct):
    """Person model."""

    givenName: str
    familyName: str
    pref_label: str


class Organization(Struct):
    """Organization model."""

    pref_label: str
    alternative_name: str | None = None
