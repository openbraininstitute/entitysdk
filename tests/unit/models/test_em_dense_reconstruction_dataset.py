import pytest

from entitysdk.models.em_dense_reconstruction_dataset import EMDenseReconstructionDataset

from ..util import MOCK_UUID


def test_em_dense_reconstruction_dataset_validation():
    """Test that EMDenseReconstructionDataset validates required fields."""
    # Test valid dataset
    dataset_data = {
        "id": str(MOCK_UUID),
        "name": "Test Dataset",
        "description": "Test Description",
        "volume_resolution_x_nm": 8.0,
        "volume_resolution_y_nm": 8.0,
        "volume_resolution_z_nm": 8.0,
        "release_url": "https://example.com/dataset",
        "cave_client_url": "https://cave.example.com",
        "cave_datastack": "test_datastack",
        "precomputed_mesh_url": "https://example.com/meshes",
        "cell_identifying_property": "cell_id",
    }
    dataset = EMDenseReconstructionDataset.model_validate(dataset_data)
    assert dataset.volume_resolution_x_nm == 8.0
    assert dataset.release_url == "https://example.com/dataset"

    # Test invalid slicing direction
    with pytest.raises(ValueError):
        EMDenseReconstructionDataset.model_validate(
            {**dataset_data, "slicing_direction": "invalid_direction"}
        )

    # Test missing required field
    with pytest.raises(ValueError):
        EMDenseReconstructionDataset.model_validate(
            {
                "id": str(MOCK_UUID),
                "name": "Test Dataset",
                "description": "Test Description",
                # Missing required fields
            }
        )
