

from entitysdk.client import Client
from entitysdk.models import Simulation
from entitysdk.types import ContenType


def stage_simulation_config(
    client: Client, *,
    model: Simulation,
    output_path: StrOrPath,
):

    simulation_config = client.download_assets(model, selection={"content_type": ContentType.json, label="sonata_simulation_config"}).one()
