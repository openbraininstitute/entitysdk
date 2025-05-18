"""License model."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.core import Identifiable


class License(Identifiable):
    """License model."""

    name: Annotated[
        str,
        Field(
            examples=["Apache 2.0"],
            description="The name of the license.",
        ),
    ]
    description: Annotated[
        str,
        Field(
            examples=["The 2.0 version of the Apache License"],
            description="The description of the license.",
        ),
    ]
    label: Annotated[
        str,
        Field(
            examples=["Apache 2.0"],
            description="The label of the license.",
        ),
    ]
