"""Simulatable neuron model."""

from typing import Annotated

from pydantic import MISSING, Field

from entitysdk.mixin import NameDescriptionMixin
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


class MEModelBase(NameDescriptionMixin):
    """Base for simulatable neuron model."""

    validation_status: Annotated[
        ValidationStatus,
        Field(
            description="The validation status of the memodel.",
        ),
    ]


class NestedMEModel(MEModelBase, Entity):
    """Nested simulatable neuron model."""

    etypes: Annotated[
        list[ETypeClass] | None,
        Field(
            description="The etype classes of the memodel.",
        ),
    ] = MISSING  # type: ignore[assignment]
    mtypes: Annotated[
        list[MTypeClass] | None,
        Field(
            description="The mtype classes of the memodel.",
        ),
    ] = MISSING  # type: ignore[assignment]


class MEModel(MEModelBase, Entity):
    """Simulatable neuron model."""

    species: Annotated[
        Species,
        Field(description="The species for which the memodel applies."),
    ]
    strain: Annotated[
        Strain | None,
        Field(description="The specific strain of the species, if applicable."),
    ] = MISSING  # type: ignore[assignment]
    brain_region: Annotated[
        BrainRegion,
        Field(description="The brain region where the memodel is used or applies."),
    ]
    license: Annotated[
        License | None,
        Field(description="License under which the memodel is distributed."),
    ] = MISSING  # type: ignore[assignment]
    contributions: Annotated[
        list[Contribution] | None,
        Field(description="List of contributions related to this memodel."),
    ] = MISSING  # type: ignore[assignment]
    iteration: Annotated[
        str | None,
        Field(
            description="The iteration of the memodel used during optimisation.",
            examples=["1372346"],
        ),
    ] = MISSING  # type: ignore[assignment]
    holding_current: Annotated[
        float | None,
        Field(
            description="The holding current of the memodel.",
            examples=[0.0],
        ),
    ] = MISSING  # type: ignore[assignment]
    threshold_current: Annotated[
        float | None,
        Field(
            description="The threshold current of the memodel.",
            examples=[0.1],
        ),
    ] = MISSING  # type: ignore[assignment]
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
    ] = MISSING  # type: ignore[assignment]
    mtypes: Annotated[
        list[MTypeClass] | None,
        Field(
            description="The mtype classes of the memodel.",
        ),
    ] = MISSING  # type: ignore[assignment]
    calibration_result: Annotated[
        MEModelCalibrationResult | None,
        Field(
            description="The calibration result of the memodel.",
        ),
    ] = MISSING  # type: ignore[assignment]
    legacy_id: list[str] | None = MISSING  # type: ignore[assignment]
