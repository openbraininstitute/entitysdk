"""Download functions for IonChannelModel entities."""

from entitysdk.models.ion_channel_model import IonChannelModel


def download_one_mechanism(client, access_token, ic, mechanisms_dir="./mechanisms"):
    """Download one mechanism file

    Args:
        client (Client): EntitySDK client
        access_token (str): access token for authentication
        ic (IonChannelModel): IonChannelModel entitysdk object
        mechanisms_dir (str or Pathlib.Path): directory to save the mechanism file
    """
    if not ic.assets:
        raise ValueError(f"No assets found in the ion channel model {ic.name}.")
    asset = ic.assets[0]
    asset_id = asset.id
    asset_path = asset.path
    client.download_file(
        asset_id=asset_id,
        entity_id=ic.id,
        entity_type=IonChannelModel,
        token=access_token,
        output_path=mechanisms_dir / asset_path,
    )
