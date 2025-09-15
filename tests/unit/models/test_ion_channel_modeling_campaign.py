import json
from pathlib import Path

import pytest

from entitysdk.models.ion_channel_modeling_campaign import IonChannelModelingCampaign

from ..util import MOCK_UUID

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def json_data():
    return json.loads(Path(DATA_DIR / "ion_channel_modeling_campaign.json").read_bytes())


@pytest.fixture
def ion_channel_modeling_campaign(json_data):
    return IonChannelModelingCampaign.model_validate(json_data)


def test_read_ion_channel_modeling_campaign(client, httpx_mock, auth_token, json_data):
    httpx_mock.add_response(method="GET", json=json_data)
    entity = client.get_entity(
        entity_id=MOCK_UUID,
        entity_type=IonChannelModelingCampaign,
    )
    assert entity.model_dump(mode="json", exclude_none=True) == json_data


def test_register_ion_channel_modeling_campaign(
    client, httpx_mock, auth_token, ion_channel_modeling_campaign, json_data
):
    httpx_mock.add_response(
        method="POST",
        json=ion_channel_modeling_campaign.model_dump(mode="json") | {"id": str(MOCK_UUID)},
    )
    registered = client.register_entity(entity=ion_channel_modeling_campaign)
    expected_json = json_data.copy() | {"id": str(MOCK_UUID)}
    assert registered.model_dump(mode="json", exclude_none=True) == expected_json
