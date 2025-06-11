"""Download functions for Morphology entities."""

import logging
from pathlib import Path

from entitysdk.client import Client
from entitysdk.models.morphology import ReconstructionMorphology

logger = logging.getLogger(__name__)


def download_morphology(
    client: Client,
    morphology: ReconstructionMorphology,
    morph_dir: str | Path,
    file_type: str | None = "asc",
) -> Path:
    """Download morphology file.

    Args:
        client (Client): EntitySDK client
        morphology (ReconstructionMorphology): Morphology entitysdk object
        morph_dir (str or Path): directory to save the morphology file
        file_type (str or None): type of the morphology file (asc, swc or h5).
            Will take the first one if None.
    """
    morph_dir = Path(morph_dir)
    morph_dir.mkdir(parents=True, exist_ok=True)

    # try to fetch morphology with the specified file type
    asset = client.download_assets(
        morphology,
        selection={"content_type": f"application/{file_type}"},
        output_path=morph_dir,
    ).one_or_none()
    # fallback #1: we expect at least a asc or swc file
    if asset is None:
        asset = client.download_assets(
            morphology,
            selection={"content_type": "application/asc"},
            output_path=morph_dir,
        ).one_or_none()
        if asset is None:
            asset = client.download_assets(
                morphology,
                selection={"content_type": "application/swc"},
                output_path=morph_dir,
            ).one_or_none()
    # fallback #2: we take the first asset
    if asset is None:
        logger.warning(
            "No %s file found in the morphology %s, will select the first one.",
            file_type,
            morphology.name,
        )
        asset = client.download_assets(
            morphology,
            output_path=morph_dir,
        ).first()

    return asset.output_path
