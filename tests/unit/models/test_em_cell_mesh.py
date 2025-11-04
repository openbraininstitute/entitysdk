import pytest

from entitysdk.models.em_cell_mesh import EMCellMesh

from ..util import MOCK_UUID


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
