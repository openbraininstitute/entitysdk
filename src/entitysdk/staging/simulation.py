import json
from pathlib import Path

from entitysdk.client import Client
from entitysdk.models import Simulation
from entitysdk.types import ContentType, StrOrPath
from entitysdk.utils.filesystem import create_dir
from entitysdk.utils.io import write_json


def stage_simulation(
    client: Client,
    *,
    model: Simulation,
    output_dir: StrOrPath,
    circuit_config_path: Path,
):
    output_dir = create_dir(output_dir).resolve()

    simulation_config: dict = json.loads(
        client.download_entity_asset_content(
            model,
            selection={
                "content_type": ContentType.json,
                "label": "sonata_simulation_config",
            },
        ).content
    )
    node_sets_path: Path = client.download_entity_asset_file(
        model,
        selection={
            "content_type": ContentType.json,
            "label": "custom_node_sets",
        },
        output_path=output_dir / "node_sets.json",
    ).path
    transformed_simulation_config: dict = _transform_simulation_config(
        simulation_config,
        circuit_config_path,
        node_sets_path,
        output_dir,
    )

    write_json(data=transformed_simulation_config, path=output_dir / "simulation_config.json")


def _transform_simulation_config(
    simulation_config: dict, circuit_config_path: Path, node_sets_path: Path, output_dir: Path
) -> dict:
    return simulation_config | {
        "network": str(circuit_config_path),
        "node_sets_file": str(node_sets_path),
    }
