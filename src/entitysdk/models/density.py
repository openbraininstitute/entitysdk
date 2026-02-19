"""Density models."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.base import BaseModel
from entitysdk.models.brain_region import BrainRegion
from entitysdk.models.contribution import Contribution
from entitysdk.models.entity import Entity
from entitysdk.models.etype import ETypeClass
from entitysdk.models.license import License
from entitysdk.models.mtype import MTypeClass
from entitysdk.models.subject import Subject
from entitysdk.types import MeasurementStatistic, MeasurementUnit


class MeasurementRecord(BaseModel):
    """Measurement record."""

    id: int | None = None
    name: MeasurementStatistic
    unit: MeasurementUnit
    value: float


class ExperimentalDensityBase(Entity):
    """Experimental Density Base model."""

    subject: Annotated[Subject, Field(description="The subject associated with the density.")]
    brain_region: Annotated[
        BrainRegion,
        Field(description="The brain region associated with the density."),
    ]
    license: Annotated[
        License | None,
        Field(description="License under which the density is distributed."),
    ] = None
    contributions: Annotated[
        list[Contribution] | None,
        Field(description="List of contributions related to this density."),
    ] = None
    measurements: list[MeasurementRecord]


class ExperimentalNeuronDensity(ExperimentalDensityBase):
    """Experimental Neuron Density."""

    mtypes: Annotated[
        list[MTypeClass] | None,
        Field(
            description="The mtype classes of the density.",
        ),
    ] = None
    etypes: Annotated[
        list[ETypeClass] | None,
        Field(
            description="The etype classes of the density.",
        ),
    ] = None


class ExperimentalBoutonDensity(ExperimentalDensityBase):
    """Experimental Bouton Density."""

    mtypes: Annotated[
        list[MTypeClass] | None,
        Field(
            description="The mtype classes of the density.",
        ),
    ] = None


class ExperimentalSynapsesPerConnection(ExperimentalDensityBase):
    """Experimental Synapses Per Connection."""

    pre_mtype: MTypeClass
    post_mtype: MTypeClass
    pre_region: BrainRegion
    post_region: BrainRegion
