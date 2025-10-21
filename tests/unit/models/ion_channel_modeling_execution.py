import json
from pathlib import Path

import pytest

from entitysdk.models.ion_channel_modeling_execution import IonChannelModelingExecution

from ..util import MOCK_UUID

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def json_data():
    return json.loads(Path(DATA_DIR / "ion_channel_modeling_execution.json").read_bytes())


@pytest.fixture
def ion_channel_modeling_execution(json_data):
    return IonChannelModelingExecution.model_validate(json_data)


def test_read_ion_channel_modeling_execution(client, httpx_mock, auth_token, json_data):
    httpx_mock.add_response(method="GET", json=json_data)
    entity = client.get_entity(
        entity_id=MOCK_UUID,
        entity_type=IonChannelModelingExecution,
    )
    assert entity.model_dump(mode="json") == json_data | {"legacy_id": None}


def test_register_ion_channel_modeling_execution(
    client, httpx_mock, auth_token, ion_channel_modeling_execution, json_data
):
    httpx_mock.add_response(
        method="POST",
        json=ion_channel_modeling_execution.model_dump(mode="json") | {"id": str(MOCK_UUID)},
    )
    registered = client.register_entity(entity=ion_channel_modeling_execution)
    expected_json = json_data.copy() | {"id": str(MOCK_UUID)}
    assert registered.model_dump(mode="json") == expected_json | {"legacy_id": None}
