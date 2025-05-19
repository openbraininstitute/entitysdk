"""Electrical cell recording models."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.brain_region import BrainRegion
from entitysdk.models.entity import Entity
from entitysdk.models.license import License
from entitysdk.models.subject import Subject
from entitysdk.types import (
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


class ElectricalCellRecording(Entity):
    """Electrical cell recording model."""

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
    comment: Annotated[
        str | None,
        Field(
            title="Comment",
            description="Comment with further details.",
        ),
    ] = None
    brain_region: Annotated[
        BrainRegion,
        Field(
            description="The region of the brain where the morphology is located.",
        ),
    ]
    subject: Annotated[
        Subject,
        Field(title="Subject", description="The subject of the electrical cell recording."),
    ]
    stimuli: Annotated[
        list[ElectricalRecordingStimulus] | None,
        Field(
            title="Electrical Recording Stimuli",
            description="List of stimuli applied to the cell with their respective time steps",
        ),
    ] = None
    license: Annotated[
        License | None,
        Field(
            description="The license attached to the morphology.",
        ),
    ] = None
