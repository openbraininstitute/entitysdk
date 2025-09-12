"""Electrical cell recording models."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.electrical_recording import ElectricalRecording
from entitysdk.models.etype import ETypeClass


class ElectricalCellRecording(ElectricalRecording):
    """Electrical cell recording model."""

    etypes: Annotated[
        list[ETypeClass] | None,
        Field(
            description="The etypes of the emodel.",
        ),
    ] = None
