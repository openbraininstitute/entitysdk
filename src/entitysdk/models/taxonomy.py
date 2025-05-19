"""License model."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.core import Identifiable
from entitysdk.models.entity import Entity
from entitysdk.types import ID


class Species(Identifiable):
    """Species model."""

    name: Annotated[
        str,
        Field(
            examples=["Mus musculus"],
            description="The name of the species.",
        ),
    ]
    taxonomy_id: Annotated[
        str,
        Field(
            examples=["1"],
            description="The taxonomy id of the species.",
        ),
    ]


class Strain(Identifiable):
    """Strain model."""

    name: Annotated[
        str,
        Field(
            examples=["C57BL/6J"],
            description="The name of the strain.",
        ),
    ]
    taxonomy_id: Annotated[
        str,
        Field(
            examples=["1"],
            description="The taxonomy id of the strain.",
        ),
    ]
    species_id: Annotated[
        ID,
        Field(
            description="The species id of the strain.",
        ),
    ]


class Taxonomy(Entity):
    """Taxonomy model."""

    name: Annotated[
        str,
        Field(
            examples=["Homo sapiens"],
            description="The name of the taxonomy.",
        ),
    ]
    pref_label: Annotated[
        str,
        Field(
            examples=["Homo sapiens"],
            description="The preferred label of the taxonomy.",
        ),
    ]
