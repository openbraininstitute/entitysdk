
import json
import uuid
import pytest
from pathlib import Path
from entitysdk.staging import simulation as test_module


DATA_DIR = Path(__file__).parent.parent / "data"


MOCK_CONFIG_ID = uuid.uuid4()
MOCK_NODESETS_ID = uuid.uuid4()


@pytest.fixture
def simulation_config():
    return json.loads(Path(DATA_DIR / "simulation_config.json").read_bytes())


@pytest.fixture
def node_sets_file():
    return json.loads(Path(DATA_DIR / "node_sets.json").read_bytes())


@pytest.fixture
def simulation():
    return Simulation(
        name="my-simulation",
        description="my-description",
        assets=[
            Asset(
                id=MOCK_CONFIG_ID,
                content_type="application/json",
                label="sonata_simulation_config",
            ),
            Asset(
                id=MOCK_CONFIG_ID,
                content_type="application/json",
                label="custom_node_sets",
            )
        ]
    )


def test_stage_simulation(client, simulation, api_url, httpx_mock, tmp_path, simulation_config, node_sets_file):

    circuit_config_path = "/foo/bar/circuit_config.json"

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/simulation/assets/{MOCK_CONFIG_ID}/download",
        json=simulation_config,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/simulation/assets/{MOCK_NODESETS_ID}/download",
        json=simulation_config,
    )

    res = test_module.stage_simulation_config(client, model=simulation, output_path=tmp_path, external_circuit_config_path=circuit_config_path)

    expected_simulation_config_path = tmp_path / "simulation_config.json"
    expected_node_sets_path = tmp_path / "node_sets.json"

    assert expected_simulation_config_path.exists()
    assert expected_node_sets_path.exists()
