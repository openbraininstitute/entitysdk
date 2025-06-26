import uuid

import pytest

from entitysdk.downloaders.morphology import download_morphology
from entitysdk.exception import IteratorResultError
from entitysdk.models.morphology import ReconstructionMorphology


def _mock_asset_response(asset_id):
    return {
        "id": str(asset_id),
        "path": "foo.asc",
        "full_path": "foo.asc",
        "is_directory": False,
        "content_type": "application/asc",
        "label": "morphology",
        "size": 100,
        "status": "created",
        "meta": {},
        "sha256_digest": "sha256_digest",
    }


def test_download_morphology(
    tmp_path,
    client,
    httpx_mock,
    api_url,
    request_headers,
):
    """Test downloading a morphology file from a Morphology entity."""
    morph_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/reconstruction-morphology/{morph_id}/assets/{asset_id}",
        match_headers=request_headers,
        json=_mock_asset_response(asset_id) | {"path": "foo.asc"},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/reconstruction-morphology/{morph_id}/assets/{asset_id}/download",
        match_headers=request_headers,
        content="foo",
    )

    morphology = ReconstructionMorphology(
        id=morph_id, name="foo", assets=[_mock_asset_response(asset_id)]
    )

    output_path = download_morphology(
        client=client,
        morphology=morphology,
        output_dir=tmp_path,
        file_type="asc",
    )

    assert output_path.is_file()

    # should raise when the file type is not present in the morphology assets
    with pytest.raises(IteratorResultError, match="Iterable is empty."):
        output_path = download_morphology(
            client=client,
            morphology=morphology,
            output_dir=tmp_path,
            file_type="swc",
        )
