"""Extracellular recording model."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.scientific_artifact import ScientificArtifact


class ExtracellularRecording(ScientificArtifact):
    """Extracellular probe recording, e.g. Neuropixels, with its traces in an NWB asset."""

    sampling_frequency: Annotated[
        float,
        Field(
            title="Sampling Frequency",
            description="Sampling frequency of the raw traces, in Hz.",
        ),
    ]
    duration: Annotated[
        float,
        Field(
            title="Duration",
            description="Duration of the recording, in seconds.",
        ),
    ]
