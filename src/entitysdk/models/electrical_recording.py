"""Electrical recording and stimulus models."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.entity import Entity
from entitysdk.models.scientific_artifact import ScientificArtifact
from entitysdk.types import (
    ID,
    ElectricalRecordingOrigin,
    ElectricalRecordingStimulusShape,
    ElectricalRecordingStimulusType,
    ElectricalRecordingType,
)


class ElectricalRecordingStimulus(Entity):
    """Electrical cell recording stimulus model."""

    dt: float | None = None
    injection_type: ElectricalRecordingStimulusType
    shape: ElectricalRecordingStimulusShape
    start_time: float | None = None
    end_time: float | None = None
    recording_id: ID | None = None


class ElectricalRecording(ScientificArtifact):
    """Electrical recording base."""

    ljp: Annotated[
        float,
        Field(
            title="Liquid Junction Potential",
            description="Correction applied to the voltage trace, in mV",
            examples=[0.1],
        ),
    ] = 0.0
    recording_location: Annotated[
        list[str],
        Field(
            title="Recording Location",
            description=(
                "Location on the cell where recording was performed, in hoc-compatible format."
            ),
        ),
    ]
    recording_type: Annotated[
        ElectricalRecordingType,
        Field(
            title="Recording Type",
            description="Recording type.",
        ),
    ]
    recording_origin: Annotated[
        ElectricalRecordingOrigin,
        Field(
            title="Recording Origin",
            description="Recording origin.",
        ),
    ]
    temperature: Annotated[
        float | None,
        Field(
            title="Temperature",
            description="Temperature at which the recording was performed, in degrees Celsius.",
            examples=[36.5],
        ),
    ] = None
    comment: Annotated[
        str | None,
        Field(
            title="Comment",
            description="Comment with further details.",
        ),
    ] = None
    stimuli: Annotated[
        list[ElectricalRecordingStimulus] | None,
        Field(
            title="Electrical Recording Stimuli",
            description="List of stimuli applied to the cell with their respective time steps",
        ),
    ] = None
