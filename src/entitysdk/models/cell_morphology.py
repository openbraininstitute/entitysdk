"""Cell Morphology models."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.brain_location import BrainLocation
from entitysdk.models.cell_morphology_protocol import CellMorphologyProtocolUnion
from entitysdk.models.measurement_annotation import MeasurementAnnotation
from entitysdk.models.mtype import MTypeClass
from entitysdk.models.scientific_artifact import ScientificArtifact
from entitysdk.types import RepairPipelineType


class CellMorphology(ScientificArtifact):
    """Cell Morphology model."""

    cell_morphology_protocol: Annotated[
        CellMorphologyProtocolUnion | None,
        Field(description="The cell morphology protocol of the morphology."),
    ] = None
    location: Annotated[
        BrainLocation | None,
        Field(description="The location of the morphology in the brain."),
    ] = None
    mtypes: Annotated[
        list[MTypeClass] | None,
        Field(description="The mtype classes of the morphology."),
    ] = None
    measurement_annotation: Annotated[
        MeasurementAnnotation | None,
        Field(description="The optional annotation with the morphometrics."),
    ] = None
    has_segmented_spines: Annotated[
        bool, Field(description="Whether the morphology has segmented spines or not.")
    ] = False
    repair_pipeline_state: Annotated[
        RepairPipelineType | None,
        Field(description="The state of the repair pipeline."),
    ] = None
