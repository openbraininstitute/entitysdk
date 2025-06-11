import json
from pathlib import Path

import pytest

from entitysdk.models.simulation_campaign import SimulationCampaign

from ..util import MOCK_UUID

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def json_data():
    return json.loads(Path(DATA_DIR / "simulation_campaign.json").read_bytes())


@pytest.fixture
def simulation_campaign(json_data):
    return SimulationCampaign.model_validate(json_data)


def test_read_simulation_campaign(client, httpx_mock, auth_token, json_data):
    httpx_mock.add_response(method="GET", json=json_data)
    entity = client.get_entity(
        entity_id=MOCK_UUID,
        entity_type=SimulationCampaign,
    )
    assert entity.model_dump(mode="json") == json_data | {"legacy_id": None}


def test_register_simulation_campaign(
    client, httpx_mock, auth_token, simulation_campaign, json_data
):
    httpx_mock.add_response(
        method="POST", json=simulation_campaign.model_dump(mode="json") | {"id": str(MOCK_UUID)}
    )
    registered = client.register_entity(entity=simulation_campaign)
    expected_json = json_data.copy() | {"id": str(MOCK_UUID)}
    assert registered.model_dump(mode="json") == expected_json | {"legacy_id": None}
