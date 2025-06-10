"""Download functions for EModel entities."""

import pathlib

from entitysdk.models.emodel import EModel


def download_hoc(client, access_token, emodel, hoc_dir="./hoc"):
    """Download hoc file.

    Args:
        client (Client): EntitySDK client
        access_token (str): access token for authentication
        emodel (EModel): EModel entitysdk object
        hoc_dir (str or Pathlib.Path): directory to save the hoc file
    """
    asset_id = None
    asset_path = None
    # Download the emodel hoc file
    if emodel.assets is None:
        raise ValueError(f"No assets found in the emodel {emodel.name}.")
    for asset in emodel.assets:
        if "hoc" in asset.content_type:
            asset_id = asset.id
            asset_path = asset.path
            break
    if asset_id is None:
        raise ValueError(f"No hoc file found in the emodel {emodel.name}.")
    hoc_dir = pathlib.Path(hoc_dir)
    hoc_dir.mkdir(parents=True, exist_ok=True)
    hoc_output_path = hoc_dir / asset_path
    client.download_file(
        asset_id=asset_id,
        entity_id=emodel.id,
        entity_type=EModel,
        token=access_token,
        output_path=hoc_output_path,
    )
    return hoc_output_path
