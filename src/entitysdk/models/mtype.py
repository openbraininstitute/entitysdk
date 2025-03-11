"""MType classification models."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.entity import Entity


class MTypeClass(Entity):
    """MType model class."""

    pref_label: Annotated[
        str,
        Field(
            description="The preferred label of the mtype class.",
        ),
    ]
    definition: Annotated[
        str,
        Field(
            description="The definition of the mtype class.",
        ),
    ]
    alt_label: Annotated[
        str | None,
        Field(description="The alternative label of th mtype class."),
    ]
