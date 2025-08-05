"""Publication models."""

import sys

if sys.version_info < (3, 12):  # pragma: no cover
    from typing_extensions import TypedDict
else:
    from typing import TypedDict

from entitysdk.models.core import Identifiable


class Author(TypedDict):
    """Author struct."""

    given_name: str
    family_name: str


class Publication(Identifiable):
    """Publication model."""

    DOI: str
    title: str | None = None
    authors: list[Author] | None = None
    publication_year: int | None = None
    abstract: str | None = None
