"""Cell Morphology models."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.brain_location import BrainLocation
from entitysdk.models.cell_morphology_protocol import CellMorphologyProtocolUnion
from entitysdk.models.mtype import MTypeClass
from entitysdk.models.scientific_artifact import ScientificArtifact


class CellMorphology(ScientificArtifact):
    """Cell Morphology model."""

    cell_morphology_protocol: Annotated[
        CellMorphologyProtocolUnion | None,
        Field(description="The cell morphology protocol of the morphology."),
    ] = None
    location: Annotated[
        BrainLocation | None,
        Field(
            description="The location of the morphology in the brain.",
        ),
    ] = None
    mtypes: Annotated[
        list[MTypeClass] | None,
        Field(
            description="The mtype classes of the morphology.",
        ),
    ] = None
