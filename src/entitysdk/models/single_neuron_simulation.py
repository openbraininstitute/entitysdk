"""Single neuron simulation."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.entity import Entity
from entitysdk.models.memodel import NestedMEModel
from entitysdk.types import SingleNeuronSimulationStatus


class SingleNeuronSimulation(Entity):
    """Single neuron simulation."""

    seed: Annotated[
        int,
        Field(
            description="Random number generator seed used during the simulation.",
            examples=42,
        ),
    ]
    injection_location: Annotated[
        list[str],
        Field(
            description="List of locations where the stimuli were injected, "
            "in hoc-compatible format.",
            examples="soma[0]",
        ),
    ]
    recording_location: Annotated[
        list[str],
        Field(
            description="List of locations where the stimuli were recorded, "
            "in hoc-compatible format.",
            examples="soma[0]",
        ),
    ]
    status: Annotated[
        SingleNeuronSimulationStatus,
        Field(
            description="Status of the simulation. Can be .started, .failure, .success",
            examples=SingleNeuronSimulationStatus.success,
        ),
    ]
    me_model: Annotated[
        NestedMEModel,
        Field(
            description="The me-model (single cell model) that was simulated, in nested form.",
        ),
    ]
