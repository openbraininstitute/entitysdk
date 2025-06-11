"""Download functions for IonChannelModel entities."""

from pathlib import Path

from entitysdk.client import Client
from entitysdk.models.ion_channel_model import IonChannelModel

def download_one_mechanism(
    client: Client,
    ic: IonChannelModel,
    mechanisms_dir: str | Path,
) -> Path:
    """Download one mechanism file.

    Args:
        client (Client): EntitySDK client
        ic (IonChannelModel): IonChannelModel entitysdk object
        mechanisms_dir (str or Pathlib.Path): directory to save the mechanism file
    """
    mechanisms_dir = Path(mechanisms_dir)
    mechanisms_dir.mkdir(parents=True, exist_ok=True)
    asset = client.download_assets(
        ic,
        selection={"content_type": "application/neuron-mod"},
        output_path=mechanisms_dir,
    ).one()

    return asset.output_path
