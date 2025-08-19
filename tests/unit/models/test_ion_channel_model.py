import json
from pathlib import Path

import pytest

from entitysdk.models.ion_channel_model import IonChannelModel

from ..util import MOCK_UUID

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def json_ion_channel_expanded():
    return json.loads(Path(DATA_DIR / "ion_channel_model.json").read_bytes())


@pytest.fixture
def ion_channel_model(json_ion_channel_expanded):
    return IonChannelModel.model_validate(json_ion_channel_expanded)


def test_read_ion_channel_model(client, httpx_mock, auth_token, json_ion_channel_expanded):
    httpx_mock.add_response(method="GET", json=json_ion_channel_expanded)
    entity = client.get_entity(
        entity_id=MOCK_UUID,
        entity_type=IonChannelModel,
    )
    assert entity.model_dump(mode="json", exclude_unset=True) == json_ion_channel_expanded


def test_register_ion_channel_model(
    client, httpx_mock, auth_token, ion_channel_model, json_ion_channel_expanded
):
    httpx_mock.add_response(method="POST", json=json_ion_channel_expanded | {"id": str(MOCK_UUID)})
    registered = client.register_entity(entity=ion_channel_model)
    expected_json = json_ion_channel_expanded | {"id": str(MOCK_UUID)}
    assert registered.model_dump(mode="json", exclude_unset=True) == expected_json


def test_update_ion_channel_model(
    client, httpx_mock, auth_token, ion_channel_model, json_ion_channel_expanded
):
    httpx_mock.add_response(
        method="PATCH",
        json=json_ion_channel_expanded | {"name": "foo"},
    )
    updated = client.update_entity(
        entity_id=ion_channel_model.id,
        entity_type=IonChannelModel,
        attrs_or_entity={"name": "foo"},
    )

    expected_json = json_ion_channel_expanded | {"name": "foo"}
    assert updated.model_dump(mode="json", exclude_unset=True) == expected_json
