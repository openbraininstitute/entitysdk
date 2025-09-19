"""Simulatable neuron model."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.base import BaseModel
from entitysdk.models.brain_region import BrainRegion
from entitysdk.models.cell_morphology import CellMorphology
from entitysdk.models.contribution import Contribution
from entitysdk.models.core import Identifiable
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
    validation_status: Annotated[
        ValidationStatus,
        Field(
            description="The validation status of the memodel.",
        ),
    ]


class NestedMEModel(MEModelBase, Identifiable):
    """Nested simulatable neuron model."""

    etypes: Annotated[
        list[ETypeClass] | None,
        Field(
            description="The etype classes of the memodel.",
        ),
    ] = None
    mtypes: Annotated[
        list[MTypeClass] | None,
        Field(
            description="The mtype classes of the memodel.",
        ),
    ] = None


class MEModel(MEModelBase, Entity):
    """Simulatable neuron model."""

    species: Annotated[
        Species,
        Field(description="The species for which the memodel applies."),
    ]
    strain: Annotated[
        Strain | None,
        Field(description="The specific strain of the species, if applicable."),
    ] = None
    brain_region: Annotated[
        BrainRegion,
        Field(description="The brain region where the memodel is used or applies."),
    ]
    license: Annotated[
        License | None,
        Field(description="License under which the memodel is distributed."),
    ] = None
    contributions: Annotated[
        list[Contribution] | None,
        Field(description="List of contributions related to this memodel."),
    ] = None
    iteration: Annotated[
        str | None,
        Field(
            description="The iteration of the memodel used during optimisation.",
            examples=["1372346"],
        ),
    ] = None
    holding_current: Annotated[
        float | None,
        Field(
            description="The holding current of the memodel.",
            examples=[0.0],
        ),
    ] = None
    threshold_current: Annotated[
        float | None,
        Field(
            description="The threshold current of the memodel.",
            examples=[0.1],
        ),
    ] = None
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
        list[ETypeClass] | None,
        Field(
            description="The etype classes of the memodel.",
        ),
    ] = None
    mtypes: Annotated[
        list[MTypeClass] | None,
        Field(
            description="The mtype classes of the memodel.",
        ),
    ] = None
    calibration_result: Annotated[
        MEModelCalibrationResult | None,
        Field(
            description="The calibration result of the memodel.",
        ),
    ] = None
    legacy_id: list[str] | None = None
