"""Download functions for Morphology entities"""

import logging
import pathlib

from entitysdk.models.morphology import ReconstructionMorphology


logger = logging.getLogger(__name__)


def download_morphology(
    client, access_token, morphology, morph_dir="./morphology", file_type="asc"
):
    """Download morphology file
    Args:
        client (Client): EntitySDK client
        access_token (str): access token for authentication
        morphology (ReconstructionMorphology): Morphology entitysdk object
        morph_dir (str or Pathlib.Path): directory to save the morphology file
        file_type (str or None): type of the morphology file (asc, swc or h5).
            Will take the first one if None.
    """
    if not morphology.assets:
        raise ValueError(f"No assets found in the morphology {morphology.name}.")
    morph_dir = pathlib.Path(morph_dir)
    morph_dir.mkdir(parents=True, exist_ok=True)

    asset_id = None
    asset_path = None
    # try to fetch morphology with the specified file type
    for asset in morphology.assets:
        if file_type is None or file_type in asset.content_type:
            asset_id = asset.id
            asset_path = asset.path
            break
    # fallback #1: we expect at least a asc or swc file
    if asset_id is None:
        for asset in morphology.assets:
            if 'asc' in asset.content_type or 'swc' in asset.content_type:
                logger.warning(
                    "No %s file found in the morphology %s, will select the one with %s.",
                    file_type,
                    morphology.name,
                    asset.content_type,
                )
                asset_id = asset.id
                asset_path = asset.path
                break
    # fallback #2: we take the first asset
    if asset_id is None:
        logger.warning(
            "No %s file found in the morphology %s, will select the first one.",
            file_type,
            morphology.name,
        )
        asset_id = morphology.assets[0].id
        asset_path = morphology.assets[0].path

    morph_out_path = morph_dir / asset_path
    client.download_file(
        asset_id=asset_id,
        entity_id=morphology.id,
        entity_type=ReconstructionMorphology,
        token=access_token,
        output_path=morph_out_path,
    )
    return morph_out_path
