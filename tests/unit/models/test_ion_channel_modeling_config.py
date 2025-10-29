import json
from pathlib import Path

import pytest

from entitysdk.models.ion_channel_modeling_config import IonChannelModelingConfig

from ..util import MOCK_UUID

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def json_data():
    return json.loads(Path(DATA_DIR / "ion_channel_modeling_config.json").read_bytes())


@pytest.fixture
def ion_channel_modeling_config(json_data):
    return IonChannelModelingConfig.model_validate(json_data)


def test_read_ion_channel_modeling_config(client, httpx_mock, auth_token, json_data):
    httpx_mock.add_response(method="GET", json=json_data)
    entity = client.get_entity(
        entity_id=MOCK_UUID,
        entity_type=IonChannelModelingConfig,
    )
    assert entity.model_dump(mode="json") == json_data | {"legacy_id": None}


def test_register_ion_channel_modeling_config(
    client, httpx_mock, auth_token, ion_channel_modeling_config, json_data
):
    httpx_mock.add_response(
        method="POST",
        json=ion_channel_modeling_config.model_dump(mode="json") | {"id": str(MOCK_UUID)},
    )
    registered = client.register_entity(entity=ion_channel_modeling_config)
    expected_json = json_data.copy() | {"id": str(MOCK_UUID)}
    assert registered.model_dump(mode="json") == expected_json | {"legacy_id": None}
