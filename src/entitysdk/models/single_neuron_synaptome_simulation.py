"""Single neuron synaptome simulation."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.entity import Entity
from entitysdk.types import ID, SingleNeuronSimulationStatus


class SingleNeuronSynaptomeSimulation(Entity):
    """Single neuron synaptome simulation."""

    seed: Annotated[
        int,
        Field(
            description="Random number generator seed used during the simulation.",
            example=42,
        ),
    ]
    injection_location: Annotated[
        list[str],
        Field(
            description="List of locations where the stimuli were injected, in hoc-compatible format.",
            example="soma[0]"
        )
    ]
    recording_location:  Annotated[
        list[str],
        Field(
            description="List of locations where the stimuli were recorded, in hoc-compatible format.",
            example="soma[0]"
        )
    ]
    status: Annotated[
        SingleNeuronSimulationStatus,
        Field(
            description="Status of the simulation. Can be .started, .failure, .success",
            example=SingleNeuronSimulationStatus.success
        )
    ]
    synaptome_id: Annotated[
        ID,
        Field(
            description="ID of the synaptome that was simulated.",
            example="85663316-a7ff-4107-9eb9-236de8868c5c",
        ),
    ]
