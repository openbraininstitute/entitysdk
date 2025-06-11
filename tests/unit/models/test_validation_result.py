import json
from pathlib import Path

import pytest

from entitysdk.models import ValidationResult

from ..util import MOCK_UUID

DATA_DIR = Path(__file__).parent / "data"

Model = ValidationResult


@pytest.fixture
def json_data():
    return json.loads(Path(DATA_DIR / "validation_result.json").read_bytes())


@pytest.fixture
def model(json_data):
    return Model.model_validate(json_data)


def test_read(client, httpx_mock, auth_token, json_data):
    httpx_mock.add_response(method="GET", json=json_data)
    entity = client.get_entity(
        entity_id=MOCK_UUID,
        entity_type=Model,
    )
    assert entity.model_dump(mode="json", exclude_none=True) == json_data


def test_register(client, httpx_mock, auth_token, model, json_data):
    httpx_mock.add_response(
        method="POST", json=model.model_dump(mode="json") | {"id": str(MOCK_UUID)}
    )
    registered = client.register_entity(entity=model)
    expected_json = json_data | {"id": str(MOCK_UUID)}
    assert registered.model_dump(mode="json", exclude_none=True) == expected_json
