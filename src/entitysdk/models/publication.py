"""Publication models."""

from typing import TypedDict

from entitysdk.models.entity import Entity


class Author(TypedDict):
    """Author struct."""

    given_name: str
    family_name: str


class Publication(Entity):
    """Publication model."""

    DOI: str | None = None
    title: str | None = None
    authors: list[Author] | None = None
    publication_year: int | None = None
    abstract: str | None = None
