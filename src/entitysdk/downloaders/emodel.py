"""Download functions for EModel entities."""

from pathlib import Path


def download_hoc(client, access_token, emodel, hoc_dir="./hoc"):
    """Download hoc file.

    Args:
        client (Client): EntitySDK client
        access_token (str): access token for authentication
        emodel (EModel): EModel entitysdk object
        hoc_dir (str or Pathlib.Path): directory to save the hoc file
    """
    hoc_dir = Path(hoc_dir)
    hoc_dir.mkdir(parents=True, exist_ok=True)
    asset = client.download_assets(
        emodel,
        selection={"content_type": "application/hoc"},
        output_path=hoc_dir,
        token=access_token,
    ).one()

    return asset.output_path
