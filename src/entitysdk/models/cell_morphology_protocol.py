"""Cell Morphology Protocol models."""

from typing import Annotated, Any, ClassVar, Literal

from pydantic import BaseModel, Field, TypeAdapter

from entitysdk.models.entity import Entity
from entitysdk.types import (
    CellMorphologyGenerationType,
    CellMorphologyProtocolDesign,
    ModifiedMorphologyMethodType,
    SlicingDirectionType,
    StainingType,
)


class CellMorphologyProtocolBase(Entity):
    """Cell Morphology Protocol Base, used by all the protocols except placeholder."""

    protocol_document: Annotated[str | None, Field()] = None
    protocol_design: Annotated[CellMorphologyProtocolDesign | None, Field()] = None


class DigitalReconstructionCellMorphologyProtocol(
    CellMorphologyProtocolBase,
):
    """Experimental morphology method for capturing cell morphology data.

    Attributes:
        staining_type: Method used for staining.
        slicing_thickness: Thickness of the slice in microns.
        slicing_direction: Direction of slicing.
        magnification: Magnification level used.
        tissue_shrinkage: Amount tissue shrunk by (not correction factor).
        corrected_for_shrinkage: Whether data has been corrected for shrinkage.
    """

    generation_type: Literal[CellMorphologyGenerationType.digital_reconstruction]
    staining_type: StainingType | None = None
    slicing_thickness: Annotated[float, Field(ge=0.0)]
    slicing_direction: SlicingDirectionType | None = None
    magnification: Annotated[float | None, Field(ge=0.0)] = None
    tissue_shrinkage: Annotated[float | None, Field(ge=0.0)] = None
    corrected_for_shrinkage: bool | None = None


class ModifiedReconstructionCellMorphologyProtocol(
    CellMorphologyProtocolBase,
):
    """Modified Reconstruction Cell Morphology Protocol."""

    generation_type: Literal[CellMorphologyGenerationType.modified_reconstruction]
    method_type: ModifiedMorphologyMethodType


class ComputationallySynthesizedCellMorphologyProtocol(
    CellMorphologyProtocolBase,
):
    """Computationally Synthesized Cell Morphology Protocol."""

    generation_type: Literal[CellMorphologyGenerationType.computationally_synthesized]
    method_type: str


class PlaceholderCellMorphologyProtocol(
    Entity,
):
    """Placeholder Cell Morphology Protocol."""

    generation_type: Literal[CellMorphologyGenerationType.placeholder]


CellMorphologyProtocolUnion = Annotated[
    DigitalReconstructionCellMorphologyProtocol
    | ModifiedReconstructionCellMorphologyProtocol
    | ComputationallySynthesizedCellMorphologyProtocol
    | PlaceholderCellMorphologyProtocol,
    Field(discriminator="generation_type"),
]


class CellMorphologyProtocol(BaseModel):
    """Wrapper for consistent API, to be used for retrieving all the protocol types."""

    _adapter: ClassVar[TypeAdapter] = TypeAdapter(CellMorphologyProtocolUnion)

    @classmethod
    def model_validate(cls, obj: Any, *args, **kwargs) -> CellMorphologyProtocolUnion:  # type: ignore[override]
        """Return the correct instance of CellMorphologyProtocolUnion."""
        return cls._adapter.validate_python(obj, *args, **kwargs)
