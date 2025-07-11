"""Download functions for Morphology entities."""

import logging
from pathlib import Path

from entitysdk.client import Client
from entitysdk.models.morphology import ReconstructionMorphology
from entitysdk.types import ContentType
from entitysdk.utils.filesystem import create_dir

logger = logging.getLogger(__name__)


def download_morphology(
    client: Client,
    morphology: ReconstructionMorphology,
    output_dir: str | Path,
    file_type: str,
) -> Path:
    """Download morphology file.

    Args:
        client (Client): EntitySDK client
        morphology (ReconstructionMorphology): Morphology entitysdk object
        output_dir (str or Path): directory to save the morphology file
        file_type (str or None): type of the morphology file ('asc', 'swc' or 'h5').
            Will take the first one if None.
    """
    output_dir = create_dir(output_dir)

    asset = client.download_assets(
        morphology,
        selection={"content_type": ContentType(f"application/{file_type}")},
        output_path=output_dir,
    ).one()

    return asset.path
