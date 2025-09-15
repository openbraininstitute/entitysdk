"""Download functions for EM Cell Mesh entities."""

import logging
from pathlib import Path

from entitysdk.client import Client
from entitysdk.models.em_cell_mesh import EMCellMesh
from entitysdk.types import ContentType
from entitysdk.utils.filesystem import create_dir

logger = logging.getLogger(__name__)


def download_mesh_file(
    client: Client,
    em_cell_mesh: EMCellMesh,
    output_dir: str | Path,
    file_type: str = "obj",
) -> Path:
    """Download mesh file.

    Args:
        client (Client): EntitySDK client
        em_cell_mesh (EMCellMesh): EM Cell Mesh entitysdk object
        output_dir (str or Path): directory to save the mesh file
        file_type (str): type of the mesh file ('obj', h5)
            Will take the first one if None.

    Returns:
        Path: Path to the downloaded file
    """
    output_dir = create_dir(output_dir)
    if file_type == "h5":
        file_type = "application/x-hdf5"
    asset = client.download_assets(
        em_cell_mesh,
        selection={"content_type": ContentType(f"application/{file_type}")},
        output_path=output_dir,
    ).one()

    return asset.path
