"""Ion channel recording models."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.electrical_recording import ElectricalRecording
from entitysdk.models.ion_channel import IonChannel


class IonChannelRecording(ElectricalRecording):
    """Ion channel recording model."""

    ion_channel: Annotated[
        IonChannel | None,
        Field(
            title="Ion channel",
        ),
    ] = None
    cell_line: Annotated[
        str,
        Field(
            title="Cell line",
            description=("Cell line used to host the ion channel."),
            examples=["CHO"],
        ),
    ]
