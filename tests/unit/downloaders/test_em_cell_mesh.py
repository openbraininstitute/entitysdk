import uuid

from entitysdk.downloaders.em_cell_mesh import download_mesh_file
from entitysdk.models.em_cell_mesh import EMCellMesh
from entitysdk.types import ContentType


def _mock_asset_response(asset_id):
    return {
        "id": str(asset_id),
        "path": "mesh.obj",
        "full_path": "mesh.obj",
        "is_directory": False,
        "content_type": "application/obj",
        "size": 1000,
        "status": "created",
        "meta": {},
        "sha256_digest": "sha256_digest",
        "label": "cell_surface_mesh",
    }


def test_download_mesh_file(
    tmp_path,
    client,
    httpx_mock,
    api_url,
    request_headers,
):
    """Test downloading a mesh file from an EMCellMesh entity."""
    mesh_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/em-cell-mesh/{mesh_id}/assets/{asset_id}",
        match_headers=request_headers,
        json=_mock_asset_response(asset_id),
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/em-cell-mesh/{mesh_id}/assets/{asset_id}/download",
        match_headers=request_headers,
        content="mesh data",
    )

    em_cell_mesh = EMCellMesh(
        id=mesh_id,
        name="Test Mesh",
        release_version=1,
        dense_reconstruction_cell_id=12345,
        generation_method="marching_cubes",
        level_of_detail=5,
        mesh_type="static",
        assets=[_mock_asset_response(asset_id)],
    )

    output_path = download_mesh_file(
        client=client,
        em_cell_mesh=em_cell_mesh,
        output_dir=tmp_path,
        content_type=ContentType.application_obj,
    )

    assert output_path.is_file()
