import json
from pathlib import Path

import pytest

from entitysdk.models.cell_morphology import CellMorphology

from ..util import MOCK_UUID

DATA_DIR = Path(__file__).parent / "data"

Model = CellMorphology


@pytest.fixture
def json_data():
    return json.loads(Path(DATA_DIR / "cell_morphology.json").read_bytes())


@pytest.fixture
def model(json_data):
    return Model.model_validate(json_data)


def test_read(client, httpx_mock, auth_token, json_data):
    httpx_mock.add_response(method="GET", json=json_data)
    entity = client.get_entity(
        entity_id=MOCK_UUID,
        entity_type=Model,
    )
    assert entity.model_dump(mode="json", exclude_unset=True) == json_data


def test_register(client, httpx_mock, auth_token, model, json_data):
    httpx_mock.add_response(
        method="POST",
        json=model.model_dump(mode="json", exclude_unset=True) | {"id": str(MOCK_UUID)},
    )
    registered = client.register_entity(entity=model)
    expected_json = json_data | {"id": str(MOCK_UUID)}
    assert registered.model_dump(mode="json", exclude_unset=True) == expected_json


def test_update(client, httpx_mock, auth_token, model, json_data):
    httpx_mock.add_response(
        method="PATCH",
        json=model.model_dump(mode="json", exclude_unset=True) | {"name": "foo"},
    )
    updated = client.update_entity(
        entity_id=model.id,
        entity_type=Model,
        attrs_or_entity={"name": "foo"},
    )

    expected_json = json_data | {"name": "foo"}
    assert updated.model_dump(mode="json", exclude_unset=True) == expected_json
