import json
import uuid
from pathlib import Path

import pytest

from entitysdk.models import Asset, Simulation
from entitysdk.staging import simulation as test_module
from entitysdk.utils.io import load_json

DATA_DIR = Path(__file__).parent / "data"


MOCK_SIMULATION_ID = uuid.UUID(int=0)
MOCK_CONFIG_ID = uuid.UUID(int=1)
MOCK_NODESETS_ID = uuid.UUID(int=2)


@pytest.fixture
def simulation_config():
    return json.loads(Path(DATA_DIR / "simulation_config.json").read_bytes())


@pytest.fixture
def node_sets_file():
    return json.loads(Path(DATA_DIR / "node_sets.json").read_bytes())


@pytest.fixture
def simulation():
    return Simulation(
        id=MOCK_SIMULATION_ID,
        name="my-simulation",
        description="my-description",
        entity_id=uuid.uuid4(),
        simulation_campaign_id=uuid.uuid4(),
        scan_parameters={},
        assets=[
            Asset(
                id=MOCK_CONFIG_ID,
                content_type="application/json",
                label="sonata_simulation_config",
                path="foo.json",
                full_path="/foo.json",
                size=0,
                is_directory=False,
            ),
            Asset(
                id=MOCK_NODESETS_ID,
                content_type="application/json",
                label="custom_node_sets",
                path="bar.json",
                full_path="/bar.json",
                size=0,
                is_directory=False,
            ),
        ],
    )


def test_stage_simulation(
    client, simulation, api_url, httpx_mock, tmp_path, simulation_config, node_sets_file
):
    circuit_config_path = "/foo/bar/circuit_config.json"

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/simulation/{MOCK_SIMULATION_ID}/assets/{MOCK_CONFIG_ID}/download",
        json=simulation_config,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/simulation/{MOCK_SIMULATION_ID}/assets/{MOCK_NODESETS_ID}/download",
        json=simulation_config,
    )

    res = test_module.stage_simulation(
        client,
        model=simulation,
        output_dir=tmp_path,
        circuit_config_path=circuit_config_path,
    )

    expected_simulation_config_path = tmp_path / "simulation_config.json"
    expected_node_sets_path = tmp_path / "node_sets.json"

    assert expected_simulation_config_path.exists()
    assert expected_node_sets_path.exists()

    simulation_config = load_json(expected_simulation_config_path)
    assert simulation_config["network"] == circuit_config_path
    assert simulation_config["node_sets_file"] == str(expected_node_sets_path)
