import json
from pathlib import Path

import pytest

from entitysdk.models.circuit import Circuit

from ..util import MOCK_UUID

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def json_data():
    return json.loads(Path(DATA_DIR / "circuit.json").read_bytes())


@pytest.fixture
def circuit(json_data):
    return Circuit.model_validate(json_data)


def test_read_circuit(client, httpx_mock, auth_token, json_data):
    httpx_mock.add_response(method="GET", json=json_data)
    entity = client.get_entity(
        entity_id=MOCK_UUID,
        entity_type=Circuit,
    )
    assert entity.model_dump(mode="json") == json_data | {"legacy_id": None}


def test_register_circuit(client, httpx_mock, circuit, json_data):
    httpx_mock.add_response(
        method="POST", json=circuit.model_dump(mode="json") | {"id": str(MOCK_UUID)}
    )
    registered = client.register_entity(entity=circuit)
    expected_json = json_data.copy() | {"id": str(MOCK_UUID)}
    assert registered.model_dump(mode="json") == expected_json | {"legacy_id": None}
