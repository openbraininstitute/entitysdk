"""Download functions for IonChannelModel entities."""

from pathlib import Path


def download_one_mechanism(client, access_token, ic, mechanisms_dir="./mechanisms"):
    """Download one mechanism file.

    Args:
        client (Client): EntitySDK client
        access_token (str): access token for authentication
        ic (IonChannelModel): IonChannelModel entitysdk object
        mechanisms_dir (str or Pathlib.Path): directory to save the mechanism file
    """
    mechanisms_dir = Path(mechanisms_dir)
    mechanisms_dir.mkdir(parents=True, exist_ok=True)
    asset = client.download_assets(
        ic,
        selection={"content_type": "application/neuron-mod"},
        output_path=mechanisms_dir,
        token=access_token,
    ).one()

    return asset.output_path
