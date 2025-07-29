"""ME-Model Calibration Result."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.entity import Entity
from entitysdk.types import ID


class MEModelCalibrationResult(Entity):
    """ME-Model calibration result."""

    holding_current: Annotated[
        float,
        Field(
            description="The holding current to apply to the simulatable neuron, in nA.",
            examples=[-0.016],
        ),
    ]
    threshold_current: Annotated[
        float,
        Field(
            description="The minimal amount of current needed to make "
            "the simulatable neuron spike, in nA.",
            examples=[0.1],
        ),
    ]
    rin: Annotated[
        float | None,
        Field(
            description="The input resistance of the simulatable neuron, in MOhm.",
            examples=[0.1],
        ),
    ] = None
    calibrated_entity_id: Annotated[
        ID,
        Field(
            description="ID of the calibrated entity.",
            examples=["85663316-a7ff-4107-9eb9-236de8868c5c"],
        ),
    ]
