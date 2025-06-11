import json
from pathlib import Path

import pytest

from entitysdk.models.morphology import (
    ReconstructionMorphology,
)

from ..util import MOCK_UUID

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def json_morphology_expanded():
    return json.loads(Path(DATA_DIR / "reconstruction_morphology.json").read_bytes())


@pytest.fixture
def morphology(json_morphology_expanded):
    return ReconstructionMorphology.model_validate(json_morphology_expanded)


def test_read_reconstruction_morphology(client, httpx_mock, auth_token, json_morphology_expanded):
    httpx_mock.add_response(method="GET", json=json_morphology_expanded)
    entity = client.get_entity(
        entity_id=MOCK_UUID,
        entity_type=ReconstructionMorphology,
    )
    assert entity.model_dump(mode="json") == json_morphology_expanded | {"legacy_id": None}


def test_register_reconstruction_morphology(
    client, httpx_mock, auth_token, morphology, json_morphology_expanded
):
    httpx_mock.add_response(
        method="POST", json=morphology.model_dump(mode="json") | {"id": str(MOCK_UUID)}
    )
    registered = client.register_entity(entity=morphology)
    expected_json = json_morphology_expanded.copy() | {"id": str(MOCK_UUID)}
    assert registered.model_dump(mode="json") == expected_json | {"legacy_id": None}


def test_update_reconstruction_morphology(
    client, httpx_mock, auth_token, morphology, json_morphology_expanded
):
    httpx_mock.add_response(
        method="PATCH",
        json=morphology.model_dump(mode="json") | {"name": "foo"},
    )
    updated = client.update_entity(
        entity_id=morphology.id,
        entity_type=ReconstructionMorphology,
        attrs_or_entity={"name": "foo"},
    )

    expected_json = json_morphology_expanded.copy() | {"name": "foo"}
    assert updated.model_dump(mode="json") == expected_json | {"legacy_id": None}
