"""Download functions for EModel entities."""

from pathlib import Path

from entitysdk.client import Client
from entitysdk.models.emodel import EModel

def download_hoc(
    client: Client,
    emodel: EModel,
    hoc_dir: str | Path,
) -> Path:
    """Download hoc file.

    Args:
        client (Client): EntitySDK client
        emodel (EModel): EModel entitysdk object
        hoc_dir (str or Path): directory to save the hoc file
    """
    hoc_dir = Path(hoc_dir)
    hoc_dir.mkdir(parents=True, exist_ok=True)
    asset = client.download_assets(
        emodel,
        selection={"content_type": "application/hoc"},
        output_path=hoc_dir,
    ).one()

    return asset.output_path
