"""EM Cell Mesh models."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.entity import Entity
from entitysdk.models.scientific_artifact import ScientificArtifact
from entitysdk.types import EMCellMeshGenerationMethod, EMCellMeshType


class EMCellMesh(ScientificArtifact):
    """EM Cell Mesh model."""

    release_version: Annotated[
        int,
        Field(
            description="The release version of the mesh.",
        ),
    ]
    dense_reconstruction_cell_id: Annotated[
        int,
        Field(
            description="The cell ID in the dense reconstruction dataset.",
        ),
    ]
    generation_method: Annotated[
        EMCellMeshGenerationMethod,
        Field(
            description="The algorithm used to generate the mesh from a volume.",
        ),
    ]
    level_of_detail: Annotated[
        int,
        Field(
            description="The level of detail of the mesh.",
        ),
    ]
    generation_parameters: Annotated[
        dict | None,
        Field(
            description="Parameters used for mesh generation.",
        ),
    ] = None
    mesh_type: Annotated[
        EMCellMeshType,
        Field(
            description="How the mesh was created (static or dynamic).",
        ),
    ]
    em_dense_reconstruction_dataset: Annotated[
        Entity | None,
        Field(
            description="The dense reconstruction dataset this mesh belongs to.",
        ),
    ] = None
