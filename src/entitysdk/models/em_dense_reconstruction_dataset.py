"""EM Dense Reconstruction Dataset models."""

from typing import Annotated

from pydantic import Field, HttpUrl

from entitysdk.models.scientific_artifact import ScientificArtifact
from entitysdk.types import SlicingDirectionType


class EMDenseReconstructionDataset(ScientificArtifact):
    """EM Dense Reconstruction Dataset model."""

    protocol_document: Annotated[
        HttpUrl | None,
        Field(
            description="URL to the protocol document.",
        ),
    ] = None
    fixation: Annotated[
        str | None,
        Field(
            description="Fixation method used.",
        ),
    ] = None
    staining_type: Annotated[
        str | None,
        Field(
            description="Type of staining used.",
        ),
    ] = None
    slicing_thickness: Annotated[
        float | None,
        Field(
            description="Thickness of the slices in micrometers.",
        ),
    ] = None
    tissue_shrinkage: Annotated[
        float | None,
        Field(
            description="Tissue shrinkage factor.",
        ),
    ] = None
    microscope_type: Annotated[
        str | None,
        Field(
            description="Type of microscope used.",
        ),
    ] = None
    detector: Annotated[
        str | None,
        Field(
            description="Type of detector used.",
        ),
    ] = None
    slicing_direction: Annotated[
        SlicingDirectionType | None,
        Field(
            description="Direction of slicing.",
        ),
    ] = None
    landmarks: Annotated[
        str | None,
        Field(
            description="Landmarks used for alignment.",
        ),
    ] = None
    voltage: Annotated[
        float | None,
        Field(
            description="Voltage used for imaging.",
        ),
    ] = None
    current: Annotated[
        float | None,
        Field(
            description="Current used for imaging.",
        ),
    ] = None
    dose: Annotated[
        float | None,
        Field(
            description="Dose used for imaging.",
        ),
    ] = None
    temperature: Annotated[
        float | None,
        Field(
            description="Temperature during imaging.",
        ),
    ] = None
    volume_resolution_x_nm: Annotated[
        float,
        Field(
            description="Volume resolution in X direction in nanometers.",
        ),
    ]
    volume_resolution_y_nm: Annotated[
        float,
        Field(
            description="Volume resolution in Y direction in nanometers.",
        ),
    ]
    volume_resolution_z_nm: Annotated[
        float,
        Field(
            description="Volume resolution in Z direction in nanometers.",
        ),
    ]
    release_url: Annotated[
        str,
        Field(
            description="URL to the dataset release.",
        ),
    ]
    cave_client_url: Annotated[
        str,
        Field(
            description="URL to the CAVE client for visualization.",
        ),
    ]
    cave_datastack: Annotated[
        str,
        Field(
            description="CAVE datastack identifier.",
        ),
    ]
    precomputed_mesh_url: Annotated[
        str,
        Field(
            description="URL to precomputed meshes.",
        ),
    ]
    cell_identifying_property: Annotated[
        str,
        Field(
            description="Property used to identify cells in the dataset.",
        ),
    ]
