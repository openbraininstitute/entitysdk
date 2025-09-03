"""Ion channel recording models."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.electrical_cell_recording import ElectricalCellRecording
from entitysdk.models.ion_channel import IonChannel


class IonChannelRecording(ElectricalCellRecording):
    """Ion channel recording model."""

    ion_channel: Annotated[
        IonChannel,
        Field(
            title="Ion channel",
        ),
    ]
    cell_line: Annotated[
        str,
        Field(
            title="Cell line",
            description=(
                "Cell line used to host the ion channel."
            ),
            example="CHO"
        ),
    ]
