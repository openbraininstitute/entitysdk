"""Download functions for EModel entities."""

from pathlib import Path

from entitysdk.client import Client
from entitysdk.models.emodel import EModel
from entitysdk.types import ContentType
from entitysdk.utils.filesystem import create_dir


def download_hoc(
    client: Client,
    emodel: EModel,
    output_dir: str | Path,
) -> Path:
    """Download hoc file.

    Args:
        client (Client): EntitySDK client
        emodel (EModel): EModel entitysdk object
        output_dir (str or Path): directory to save the hoc file
    """
    output_dir = create_dir(output_dir)
    asset = client.download_assets(
        emodel,
        selection={"content_type": ContentType.application_hoc},
        output_path=output_dir,
    ).one()

    return asset.path
