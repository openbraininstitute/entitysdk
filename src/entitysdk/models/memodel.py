"""Simulatable neuron model."""

from typing import Annotated

from pydantic import MISSING, Field

from entitysdk.models.base import BaseModel
from entitysdk.models.brain_region import BrainRegion
from entitysdk.models.cell_morphology import CellMorphology
from entitysdk.models.contribution import Contribution
from entitysdk.models.emodel import EModel
from entitysdk.models.entity import Entity
from entitysdk.models.etype import ETypeClass
from entitysdk.models.license import License
from entitysdk.models.memodelcalibrationresult import MEModelCalibrationResult
from entitysdk.models.mtype import MTypeClass
from entitysdk.models.taxonomy import Species, Strain
from entitysdk.types import ValidationStatus


class MEModelBase(BaseModel):
    """Base for simulatable neuron model."""

    name: Annotated[
        str | None | MISSING,
        Field(
            examples=["Entity 1"],
            description="The name of the entity.",
        ),
    ] = MISSING
    description: Annotated[
        str | None | MISSING,
        Field(
            examples=["This is entity 1"],
            description="The description of the entity.",
        ),
    ] = MISSING
    validation_status: Annotated[
        ValidationStatus,
        Field(
            description="The validation status of the memodel.",
        ),
    ]


class NestedMEModel(MEModelBase, Entity):
    """Nested simulatable neuron model."""

    etypes: Annotated[
        list[ETypeClass] | None | MISSING,
        Field(
            description="The etype classes of the memodel.",
        ),
    ] = MISSING
    mtypes: Annotated[
        list[MTypeClass] | None | MISSING,
        Field(
            description="The mtype classes of the memodel.",
        ),
    ] = MISSING


class MEModel(MEModelBase, Entity):
    """Simulatable neuron model."""

    species: Annotated[
        Species,
        Field(description="The species for which the memodel applies."),
    ]
    strain: Annotated[
        Strain | None | MISSING,
        Field(description="The specific strain of the species, if applicable."),
    ] = MISSING
    brain_region: Annotated[
        BrainRegion,
        Field(description="The brain region where the memodel is used or applies."),
    ]
    license: Annotated[
        License | None | MISSING,
        Field(description="License under which the memodel is distributed."),
    ] = MISSING
    contributions: Annotated[
        list[Contribution] | None | MISSING,
        Field(description="List of contributions related to this memodel."),
    ] = MISSING
    iteration: Annotated[
        str | None | MISSING,
        Field(
            description="The iteration of the memodel used during optimisation.",
            examples=["1372346"],
        ),
    ] = MISSING
    holding_current: Annotated[
        float | None | MISSING,
        Field(
            description="The holding current of the memodel.",
            examples=[0.0],
        ),
    ] = MISSING
    threshold_current: Annotated[
        float | None | MISSING,
        Field(
            description="The threshold current of the memodel.",
            examples=[0.1],
        ),
    ] = MISSING
    morphology: Annotated[
        CellMorphology,
        Field(
            description="The morphology of the memodel.",
        ),
    ]
    emodel: Annotated[
        EModel,
        Field(
            description="The emodel of the memodel.",
        ),
    ]
    etypes: Annotated[
        list[ETypeClass] | None | MISSING,
        Field(
            description="The etype classes of the memodel.",
        ),
    ] = MISSING
    mtypes: Annotated[
        list[MTypeClass] | None | MISSING,
        Field(
            description="The mtype classes of the memodel.",
        ),
    ] = MISSING
    calibration_result: Annotated[
        MEModelCalibrationResult | None | MISSING,
        Field(
            description="The calibration result of the memodel.",
        ),
    ] = MISSING
    legacy_id: list[str] | None | MISSING = MISSING
