"""Cell Morphology Protocol models."""

from typing import Annotated, Any, ClassVar, Literal

from pydantic import ConfigDict, Field, HttpUrl, TypeAdapter

from entitysdk.models.core import Identifiable
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
    """Cell Morphology Protocol Base, used by all the protocols."""

    # forbid extra parameters to prevent providing attributes of other classes by mistake
    model_config = ConfigDict(extra="forbid")

    type: EntityType | None = EntityType.cell_morphology_protocol


class CellMorphologyProtocolExtendedBase(CellMorphologyProtocolBase):
    """Cell Morphology Protocol Extended Base, used by all the protocols except placeholder."""

    protocol_document: Annotated[
        HttpUrl | None,
        Field(description="URL link to protocol document or publication."),
    ] = None
    protocol_design: Annotated[
        CellMorphologyProtocolDesign | None,
        Field(description="The protocol design from a controlled vocabulary."),
    ] = None


class DigitalReconstructionCellMorphologyProtocol(
    CellMorphologyProtocolExtendedBase,
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
    CellMorphologyProtocolExtendedBase,
):
    """Modified Reconstruction Cell Morphology Protocol."""

    generation_type: Literal[CellMorphologyGenerationType.modified_reconstruction] = (
        CellMorphologyGenerationType.modified_reconstruction
    )
    method_type: Annotated[ModifiedMorphologyMethodType, Field(description="Method type.")]


class ComputationallySynthesizedCellMorphologyProtocol(
    CellMorphologyProtocolExtendedBase,
):
    """Computationally Synthesized Cell Morphology Protocol."""

    generation_type: Literal[CellMorphologyGenerationType.computationally_synthesized] = (
        CellMorphologyGenerationType.computationally_synthesized
    )
    method_type: Annotated[str, Field(description="Method type.")]


class PlaceholderCellMorphologyProtocol(
    CellMorphologyProtocolBase,
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


class CellMorphologyProtocol(Identifiable):
    """Polymorphic wrapper for consistent API, to be used for searching and retrieving.

    The correct specific protocols are automatically instantiated.

    For the registration it's possible to use this same class, or any of the specific classes:

    - `DigitalReconstructionCellMorphologyProtocol`
    - `ModifiedReconstructionCellMorphologyProtocol`
    - `ComputationallySynthesizedCellMorphologyProtocol`
    - `PlaceholderCellMorphologyProtocol`
    """

    _adapter: ClassVar[TypeAdapter] = TypeAdapter(CellMorphologyProtocolUnion)

    def __new__(cls, *args, **kwargs) -> CellMorphologyProtocolUnion:  # type: ignore[misc]
        """Construct a CellMorphologyProtocol from keyword arguments."""
        if args:
            msg = "Positional args not supported, use keyword args instead."
            raise TypeError(msg)
        return cls._adapter.validate_python(kwargs)

    def __init__(self, **kwargs: Any) -> None:
        """Catch-all to satisfy type checkers."""

    @classmethod
    def model_validate(cls, obj: Any, *args, **kwargs) -> CellMorphologyProtocolUnion:  # type: ignore[override]
        """Return the correct instance of CellMorphologyProtocolUnion."""
        return cls._adapter.validate_python(obj, *args, **kwargs)
