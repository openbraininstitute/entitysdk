"""Brain location model."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.core import Struct


class BrainLocation(Struct):
    """BrainLocation model."""

    x: Annotated[
        float,
        Field(
            examples=[1.0, 2.0, 3.0],
            description="The x coordinate of the brain location.",
        ),
    ]
    y: Annotated[
        float,
        Field(
            examples=[1.0, 2.0, 3.0],
            description="The y coordinate of the brain location.",
        ),
    ]
    z: Annotated[
        float,
        Field(
            examples=[1.0, 2.0, 3.0],
            description="The z coordinate of the brain location.",
        ),
    ]
