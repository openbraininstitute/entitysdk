"""Single neuron synaptome."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.base import BaseModel
from entitysdk.models.brain_region import BrainRegion
from entitysdk.models.contribution import Contribution
from entitysdk.models.core import Identifiable
from entitysdk.models.entity import Entity
from entitysdk.models.memodel import NestedMEModel


class SingleNeuronSynaptomeBase(BaseModel):
    """Base for single neuron synaptome."""

    name: Annotated[
        str | None,
        Field(
            examples=["Entity 1"],
            description="The name of the entity.",
        ),
    ] = None
    description: Annotated[
        str | None,
        Field(
            examples=["This is entity 1"],
            description="The description of the entity.",
        ),
    ] = None
    seed: Annotated[
        int,
        Field(
            description="Random number generator seed.",
            examples=[42],
        ),
    ]


class NestedSynaptome(SingleNeuronSynaptomeBase, Identifiable):
    """Nested single neuron synaptome."""

    pass


class SingleNeuronSynaptome(SingleNeuronSynaptomeBase, Entity):
    """Single neuron synaptome."""

    brain_region: Annotated[
        BrainRegion,
        Field(description="The brain region where the memodel is used or applies."),
    ]
    contributions: Annotated[
        list[Contribution] | None,
        Field(description="List of contributions related to this memodel."),
    ] = None
    me_model: Annotated[
        NestedMEModel,
        Field(
            description="The me-model (single cell model) the synaptome applies to.",
        ),
    ]
