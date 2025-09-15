"""EM Cell Mesh models."""

from enum import Enum
from typing import Annotated

from pydantic import Field

from entitysdk.models.brain_region import BrainRegion
from entitysdk.models.entity import Entity
from entitysdk.models.license import License
from entitysdk.models.subject import Subject


class EMCellMeshGenerationMethod(str, Enum):
    """EM Cell Mesh generation method."""

    MARCHING_CUBES = "marching_cubes"


class EMCellMeshType(str, Enum):
    """EM Cell Mesh type."""

    STATIC = "static"
    DYNAMIC = "dynamic"


class EMCellMesh(Entity):
    """EM Cell Mesh model."""

    brain_region: Annotated[
        BrainRegion | None,
        Field(
            description="The brain region where the mesh is located.",
        ),
    ] = None
    subject: Annotated[
        Subject | None,
        Field(
            description="The subject from which the mesh was generated.",
        ),
    ] = None
    license: Annotated[
        License | None,
        Field(
            description="The license attached to the mesh.",
        ),
    ] = None
    experiment_date: Annotated[
        str | None,
        Field(
            description="The date when the experiment was performed.",
        ),
    ] = None
    contact_email: Annotated[
        str | None,
        Field(
            description="Contact email for the mesh.",
        ),
    ] = None
    published_in: Annotated[
        str | None,
        Field(
            description="Publication where the mesh was described.",
        ),
    ] = None
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
