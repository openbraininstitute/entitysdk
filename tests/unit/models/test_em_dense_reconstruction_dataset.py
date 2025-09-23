import json
from pathlib import Path

import pytest

from entitysdk.models.em_dense_reconstruction_dataset import EMDenseReconstructionDataset

from ..util import MOCK_UUID

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def json_em_dense_reconstruction_dataset_expanded():
    return json.loads(Path(DATA_DIR / "em_dense_reconstruction_dataset.json").read_bytes())


@pytest.fixture
def em_dense_reconstruction_dataset(json_em_dense_reconstruction_dataset_expanded):
    return EMDenseReconstructionDataset.model_validate(
        json_em_dense_reconstruction_dataset_expanded
    )


def test_read_em_dense_reconstruction_dataset(
    client, httpx_mock, auth_token, json_em_dense_reconstruction_dataset_expanded
):
    httpx_mock.add_response(method="GET", json=json_em_dense_reconstruction_dataset_expanded)
    entity = client.get_entity(
        entity_id=MOCK_UUID,
        entity_type=EMDenseReconstructionDataset,
    )
    assert (
        entity.model_dump(mode="json", exclude_unset=True)
        == json_em_dense_reconstruction_dataset_expanded
    )


def test_register_em_dense_reconstruction_dataset(
    client,
    httpx_mock,
    auth_token,
    em_dense_reconstruction_dataset,
    json_em_dense_reconstruction_dataset_expanded,
):
    httpx_mock.add_response(
        method="POST",
        json=em_dense_reconstruction_dataset.model_dump(mode="json", exclude_unset=True)
        | {"id": str(MOCK_UUID)},
    )
    registered = client.register_entity(entity=em_dense_reconstruction_dataset)
    expected_json = json_em_dense_reconstruction_dataset_expanded.copy() | {"id": str(MOCK_UUID)}
    assert registered.model_dump(mode="json", exclude_unset=True) == expected_json


def test_update_em_dense_reconstruction_dataset(
    client,
    httpx_mock,
    auth_token,
    em_dense_reconstruction_dataset,
    json_em_dense_reconstruction_dataset_expanded,
):
    httpx_mock.add_response(
        method="PATCH",
        json=em_dense_reconstruction_dataset.model_dump(mode="json", exclude_unset=True)
        | {"name": "Updated Dataset"},
    )
    updated = client.update_entity(
        entity_id=em_dense_reconstruction_dataset.id,
        entity_type=EMDenseReconstructionDataset,
        attrs_or_entity={"name": "Updated Dataset"},
    )

    expected_json = json_em_dense_reconstruction_dataset_expanded.copy() | {
        "name": "Updated Dataset"
    }
    assert updated.model_dump(mode="json", exclude_unset=True) == expected_json


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
