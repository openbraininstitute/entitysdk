"""Download functions for IonChannelModel entities."""

from pathlib import Path

from entitysdk.client import Client
from entitysdk.models.ion_channel_model import IonChannelModel
from entitysdk.types import ContentType
from entitysdk.utils.filesystem import create_dir


def download_ion_channel_mechanism(
    client: Client,
    ion_channel_model: IonChannelModel,
    output_dir: str | Path,
) -> Path:
    """Download one mechanism file.

    Args:
        client (Client): EntitySDK client
        ion_channel_model (IonChannelModel): IonChannelModel entitysdk object
        output_dir (str or Pathlib.Path): directory to save the mechanism file
    """
    output_dir = create_dir(output_dir)
    asset = client.download_assets(
        ion_channel_model,
        selection={"content_type": ContentType.application_mod},
        output_path=output_dir,
    ).one()

    return asset.path
