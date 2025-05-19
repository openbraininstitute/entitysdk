"""Electrical cell model."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.contribution import Contribution
from entitysdk.models.entity import Entity
from entitysdk.models.etype import ETypeClass
from entitysdk.models.ion_channel_model import IonChannelModel
from entitysdk.models.morphology import (
    BrainRegion,
    License,
    ReconstructionMorphology,
    Species,
    Strain,
)
from entitysdk.models.mtype import MTypeClass


class EModel(Entity):
    """Electrical cell model."""

    species: Annotated[
        Species,
        Field(description="The species for which the emodel applies."),
    ]
    strain: Annotated[
        Strain | None,
        Field(description="The specific strain of the species, if applicable."),
    ] = None
    brain_region: Annotated[
        BrainRegion,
        Field(description="The brain region where the emodel is used or applies."),
    ]
    license: Annotated[
        License | None,
        Field(description="License under which the emodel is distributed."),
    ] = None
    contributions: Annotated[
        list[Contribution] | None,
        Field(description="List of contributions related to this emodel."),
    ] = None
    iteration: Annotated[
        str,
        Field(
            description="The iteration of the emodel used during optimisation.",
            examples="1372346",
        ),
    ]
    score: Annotated[
        float,
        Field(
            description="The score of the emodel gotten during validation.",
            examples=54.0,
        ),
    ]
    seed: Annotated[
        int,
        Field(
            description="The RNG seed used during optimisation.",
            examples=13,
        ),
    ]
    exemplar_morphology: Annotated[
        ReconstructionMorphology | None,
        Field(
            description="The morphology used during optimisation.",
        ),
    ] = None
    etypes: Annotated[
        list[ETypeClass] | None,
        Field(
            description="The etype classes of the emodel.",
        ),
    ] = None
    mtypes: Annotated[
        list[MTypeClass] | None,
        Field(
            description="The mtype classes of the emodel.",
        ),
    ] = None
    ion_channel_models: Annotated[
        list[IonChannelModel] | None,
        Field(
            description="List of ion channel models.",
        ),
    ] = None
    legacy_id: list[str] | None = None
