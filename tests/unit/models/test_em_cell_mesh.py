import json
from pathlib import Path

import pytest

from entitysdk.models.em_cell_mesh import EMCellMesh

from ..util import MOCK_UUID

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def json_em_cell_mesh_expanded():
    return json.loads(Path(DATA_DIR / "em_cell_mesh.json").read_bytes())


@pytest.fixture
def em_cell_mesh(json_em_cell_mesh_expanded):
    return EMCellMesh.model_validate(json_em_cell_mesh_expanded)


def test_read_em_cell_mesh(client, httpx_mock, auth_token, json_em_cell_mesh_expanded):
    httpx_mock.add_response(method="GET", json=json_em_cell_mesh_expanded)
    entity = client.get_entity(
        entity_id=MOCK_UUID,
        entity_type=EMCellMesh,
    )
    assert entity.model_dump(mode="json", exclude_unset=True) == json_em_cell_mesh_expanded


def test_register_em_cell_mesh(
    client, httpx_mock, auth_token, em_cell_mesh, json_em_cell_mesh_expanded
):
    httpx_mock.add_response(
        method="POST",
        json=(em_cell_mesh.model_dump(mode="json", exclude_unset=True) | {"id": str(MOCK_UUID)}),
    )
    registered = client.register_entity(entity=em_cell_mesh)
    expected_json = json_em_cell_mesh_expanded.copy() | {"id": str(MOCK_UUID)}
    assert registered.model_dump(mode="json", exclude_unset=True) == expected_json


def test_update_em_cell_mesh(
    client, httpx_mock, auth_token, em_cell_mesh, json_em_cell_mesh_expanded
):
    httpx_mock.add_response(
        method="PATCH",
        json=(em_cell_mesh.model_dump(mode="json", exclude_unset=True) | {"name": "Updated Mesh"}),
    )
    updated = client.update_entity(
        entity_id=em_cell_mesh.id,
        entity_type=EMCellMesh,
        attrs_or_entity={"name": "Updated Mesh"},
    )

    expected_json = json_em_cell_mesh_expanded.copy() | {"name": "Updated Mesh"}
    assert updated.model_dump(mode="json", exclude_unset=True) == expected_json


def test_em_cell_mesh_validation():
    """Test that EMCellMesh validates required fields."""
    # Test valid mesh
    mesh_data = {
        "id": str(MOCK_UUID),
        "name": "Test Mesh",
        "description": "Test Description",
        "release_version": 1,
        "dense_reconstruction_cell_id": 12345,
        "generation_method": "marching_cubes",
        "level_of_detail": 5,
        "mesh_type": "static",
    }
    mesh = EMCellMesh.model_validate(mesh_data)
    assert mesh.release_version == 1
    assert mesh.generation_method == "marching_cubes"
    assert mesh.mesh_type == "static"

    # Test invalid generation method
    with pytest.raises(ValueError):
        EMCellMesh.model_validate({**mesh_data, "generation_method": "invalid_method"})

    # Test invalid mesh type
    with pytest.raises(ValueError):
        EMCellMesh.model_validate({**mesh_data, "mesh_type": "invalid_type"})
