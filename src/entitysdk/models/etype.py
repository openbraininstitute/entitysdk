"""EType classification models."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.core import Identifiable


class ETypeClass(Identifiable):
    """EType model class."""

    pref_label: Annotated[
        str,
        Field(
            description="The preferred label of the etype class.",
        ),
    ]
    definition: Annotated[
        str,
        Field(
            description="The definition of the etype class.",
        ),
    ]
    alt_label: Annotated[
        str | None,
        Field(description="The alternative label of th etype class."),
    ]
