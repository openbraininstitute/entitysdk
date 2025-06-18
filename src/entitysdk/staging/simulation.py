import json
from pathlib import Path

from entitysdk.client import Client
from entitysdk.models import Simulation
from entitysdk.types import ContentType, StrOrPath


def stage_simulation(
    client: Client,
    *,
    model: Simulation,
    output_dir: StrOrPath,
    circuit_config_path: Path,
):
    simulation_config: dict = _download_json_asset(
        client,
        model,
        selection={
            "content_type": ContentType.json,
            "label": "sonata_simulation_config",
        },
    )

    breakpoint()
    print()


def _download_json_asset(client, model, selection) -> dict:
    simulation_config_bytes: bytes = client.download_entity_asset_content(
        model, selection=selection
    ).one()

    return json.loads(simulation_config_bytes)
