import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from entitysdk.models.cell_morphology_protocol import (
    CellMorphologyProtocol,
    ComputationallySynthesizedCellMorphologyProtocol,
    DigitalReconstructionCellMorphologyProtocol,
    ModifiedReconstructionCellMorphologyProtocol,
    PlaceholderCellMorphologyProtocol,
)

from ..util import MOCK_UUID

DATA_DIR = Path(__file__).parent / "data"

Model = CellMorphologyProtocol


@pytest.fixture
def json_digital_reconstruction():
    return json.loads(
        Path(DATA_DIR / "cell_morphology_protocol__digital_reconstruction.json").read_bytes()
    )


@pytest.fixture
def json_modified_reconstruction():
    return json.loads(
        Path(DATA_DIR / "cell_morphology_protocol__modified_reconstruction.json").read_bytes()
    )


@pytest.fixture
def json_computationally_synthesized():
    return json.loads(
        Path(DATA_DIR / "cell_morphology_protocol__computationally_synthesized.json").read_bytes()
    )


@pytest.fixture
def json_placeholder():
    return json.loads(Path(DATA_DIR / "cell_morphology_protocol__placeholder.json").read_bytes())


@pytest.fixture
def model_digital_reconstruction(json_digital_reconstruction):
    model = Model.model_validate(json_digital_reconstruction)
    assert isinstance(model, DigitalReconstructionCellMorphologyProtocol)
    return model


@pytest.fixture
def model_modified_reconstruction(json_modified_reconstruction):
    model = Model.model_validate(json_modified_reconstruction)
    assert isinstance(model, ModifiedReconstructionCellMorphologyProtocol)
    return model


@pytest.fixture
def model_computationally_synthesized(json_computationally_synthesized):
    model = Model.model_validate(json_computationally_synthesized)
    assert isinstance(model, ComputationallySynthesizedCellMorphologyProtocol)
    return model


@pytest.fixture
def model_placeholder(json_placeholder):
    model = Model.model_validate(json_placeholder)
    assert isinstance(model, PlaceholderCellMorphologyProtocol)
    return model


@pytest.mark.parametrize(
    "json_data_fixture",
    [
        "json_digital_reconstruction",
        "json_modified_reconstruction",
        "json_computationally_synthesized",
        "json_placeholder",
    ],
)
def test_read(request, client, httpx_mock, auth_token, json_data_fixture):
    json_data = request.getfixturevalue(json_data_fixture)
    httpx_mock.add_response(method="GET", json=json_data)
    entity = client.get_entity(
        entity_id=MOCK_UUID,
        entity_type=Model,
    )
    assert entity.model_dump(mode="json", exclude_unset=True) == json_data


@pytest.mark.parametrize(
    ("json_data_fixture", "model_fixture"),
    [
        ("json_digital_reconstruction", "model_digital_reconstruction"),
        ("json_modified_reconstruction", "model_modified_reconstruction"),
        ("json_computationally_synthesized", "model_computationally_synthesized"),
        ("json_placeholder", "model_placeholder"),
    ],
)
def test_register(request, client, httpx_mock, auth_token, json_data_fixture, model_fixture):
    json_data = request.getfixturevalue(json_data_fixture)
    model = request.getfixturevalue(model_fixture)
    httpx_mock.add_response(
        method="POST",
        json=model.model_dump(mode="json", exclude_unset=True) | {"id": str(MOCK_UUID)},
    )
    registered = client.register_entity(entity=model)
    expected_json = json_data | {"id": str(MOCK_UUID)}
    assert registered.model_dump(mode="json", exclude_unset=True) == expected_json


@pytest.mark.parametrize(
    ("json_data_fixture", "model_fixture"),
    [
        ("json_digital_reconstruction", "model_digital_reconstruction"),
        ("json_modified_reconstruction", "model_modified_reconstruction"),
        ("json_computationally_synthesized", "model_computationally_synthesized"),
        ("json_placeholder", "model_placeholder"),
    ],
)
def test_adapter(request, json_data_fixture, model_fixture):
    json_data = request.getfixturevalue(json_data_fixture)
    model = request.getfixturevalue(model_fixture)

    new_model = Model(**json_data)
    assert new_model == model

    new_model = Model.model_validate(json_data)
    assert new_model == model

    with pytest.raises(TypeError, match="Positional args not supported"):
        Model("name")

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        Model(generation_type=json_data["generation_type"], invalid_input="invalid")


@pytest.mark.parametrize(
    ("json_data_fixture", "model_fixture"),
    [
        ("json_digital_reconstruction", "model_digital_reconstruction"),
        ("json_modified_reconstruction", "model_modified_reconstruction"),
        ("json_computationally_synthesized", "model_computationally_synthesized"),
        ("json_placeholder", "model_placeholder"),
    ],
)
def test_update(request, client, httpx_mock, auth_token, json_data_fixture, model_fixture):
    json_data = request.getfixturevalue(json_data_fixture)
    model = request.getfixturevalue(model_fixture)
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
