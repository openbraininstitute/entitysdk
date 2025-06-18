import json
from pathlib import Path

from entitysdk.client import Client
from entitysdk.models import Simulation
from entitysdk.types import ContentType, StrOrPath
from entitysdk.utils.filesystem import create_dir

def stage_simulation(
    client: Client,
    *,
    model: Simulation,
    output_dir: StrOrPath,
    circuit_config_path: Path,
):
    output_dir = create_dir(output_dir)

    simulation_config: dict = _download_json_asset(
        client,
        model=model,
        selection={
            "content_type": ContentType.json,
            "label": "sonata_simulation_config",
        },
    )

    node_sets_path: Path = client.download_entity_asset_file(
        client
        model=model,
        selection={
            "content_type": ContentType.json,
            "label": "custom_node_sets",
        },
        output_path=output_dir / "node_sets.json",
    ).one().path

    transformed_simulation_config: dict = _transform_simulation_config(
        simulation_config,
        circuit_config_path,
    )

    write_json(
        data=transformed_simulation_config,
        path=output_dir / "simulation_config.json"
    )


def _download_json_asset(client, model, selection) -> dict:
    simulation_config_bytes: bytes = client.download_entity_asset_content(
        model, selection=selection
    ).one()

    return json.loads(simulation_config_bytes)


def _transform_simulation_config(simulation_config: dict, circuit_config_path: Path) -> dict

    breakpoint()
    print()
