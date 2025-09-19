"""Cell Morphology Protocol models."""

from typing import Annotated, Any, ClassVar, Literal

from pydantic import BaseModel, Field, HttpUrl, TypeAdapter

from entitysdk.models.entity import Entity
from entitysdk.types import (
    CellMorphologyGenerationType,
    CellMorphologyProtocolDesign,
    EntityType,
    ModifiedMorphologyMethodType,
    SlicingDirectionType,
    StainingType,
)


class CellMorphologyProtocolBase(Entity):
    """Cell Morphology Protocol Base, used by all the protocols except placeholder."""

    type: EntityType | None = EntityType.cell_morphology_protocol
    protocol_document: Annotated[
        HttpUrl | None,
        Field(description="URL link to protocol document or publication."),
    ] = None
    protocol_design: Annotated[
        CellMorphologyProtocolDesign | None,
        Field(description="The protocol design from a controlled vocabulary."),
    ] = None


class DigitalReconstructionCellMorphologyProtocol(
    CellMorphologyProtocolBase,
):
    """Experimental morphology method for capturing cell morphology data."""

    generation_type: Literal[CellMorphologyGenerationType.digital_reconstruction] = (
        CellMorphologyGenerationType.digital_reconstruction
    )
    staining_type: Annotated[
        StainingType | None, Field(description="Method used for staining.")
    ] = None
    slicing_thickness: Annotated[
        float, Field(description="Thickness of the slice in microns.", ge=0.0)
    ]
    slicing_direction: Annotated[
        SlicingDirectionType | None, Field(description="Direction of slicing.")
    ] = None
    magnification: Annotated[
        float | None, Field(description="Magnification level used.", ge=0.0)
    ] = None
    tissue_shrinkage: Annotated[
        float | None, Field(description="Amount tissue shrunk by (not correction factor).", ge=0.0)
    ] = None
    corrected_for_shrinkage: Annotated[
        bool | None, Field(description="Whether data has been corrected for shrinkage.")
    ] = None


class ModifiedReconstructionCellMorphologyProtocol(
    CellMorphologyProtocolBase,
):
    """Modified Reconstruction Cell Morphology Protocol."""

    generation_type: Literal[CellMorphologyGenerationType.modified_reconstruction] = (
        CellMorphologyGenerationType.modified_reconstruction
    )
    method_type: Annotated[ModifiedMorphologyMethodType, Field(description="Method type.")]


class ComputationallySynthesizedCellMorphologyProtocol(
    CellMorphologyProtocolBase,
):
    """Computationally Synthesized Cell Morphology Protocol."""

    generation_type: Literal[CellMorphologyGenerationType.computationally_synthesized] = (
        CellMorphologyGenerationType.computationally_synthesized
    )
    method_type: Annotated[str, Field(description="Method type.")]


class PlaceholderCellMorphologyProtocol(
    Entity,
):
    """Placeholder Cell Morphology Protocol."""

    generation_type: Literal[CellMorphologyGenerationType.placeholder] = (
        CellMorphologyGenerationType.placeholder
    )


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
