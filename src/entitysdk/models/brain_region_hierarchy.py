"""BrainRegionHierarchy model."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.core import Identifiable


class BrainRegionHierarchy(Identifiable):
    """BrainRegionHierarchy model."""

    name: Annotated[
        str,
        Field(
            examples=["Thalamus"],
            description="The name of the brain region.",
        ),
    ]
