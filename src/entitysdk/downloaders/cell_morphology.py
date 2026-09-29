"""Download functions for Morphology entities."""

import logging
from pathlib import Path

from entitysdk.client import Client
from entitysdk.models.cell_morphology import CellMorphology
from entitysdk.types import ContentType
from entitysdk.utils.filesystem import create_dir
from entitysdk._server_schemas import AssetLabel

logger = logging.getLogger(__name__)

MORPHOLOGY_CONTENT_TYPES = {
    "asc": ContentType.application_asc,
    "swc": ContentType.application_swc,
    "h5": ContentType.application_x_hdf5,
}


def download_morphology(
    client: Client,
    morphology: CellMorphology,
    output_dir: str | Path,
    file_type: str,
    asset_label: AssetLabel = AssetLabel.morphology,
) -> Path:
    """Download a morphology file.

    Args:
        client: EntitySDK client.
        morphology: Morphology entity.
        output_dir: Directory where the morphology file is saved.
        file_type: Morphology file type ('asc', 'swc', or 'h5').
        asset_label: Label identifying the morphology asset.
    """
    output_dir = create_dir(output_dir)

    asset = client.fetch_assets(
        morphology,
        selection={
            "content_type": MORPHOLOGY_CONTENT_TYPES[file_type],
            "label": asset_label,
        },
        output_path=output_dir,
    ).one()

    return asset.path
