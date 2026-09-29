import uuid

import pytest

from entitysdk.downloaders.cell_morphology import download_morphology
from entitysdk.exception import IteratorResultError
from entitysdk.models.cell_morphology import CellMorphology
from entitysdk.models.cell_morphology_protocol import CellMorphologyProtocol
from entitysdk.types import AssetLabel, CellMorphologyGenerationType


def _mock_asset_response(
    asset_id,
    *,
    path="foo.asc",
    content_type="application/asc",
    label="morphology",
):
    return {
        "id": str(asset_id),
        "path": path,
        "full_path": path,
        "is_directory": False,
        "content_type": content_type,
        "label": label,
        "size": 100,
        "status": "created",
        "meta": {},
        "sha256_digest": "sha256_digest",
        "storage_type": "aws_s3_internal",
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

    asset = _mock_asset_response(asset_id)

    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/cell-morphology/{morph_id}/assets/{asset_id}",
        match_headers=request_headers,
        json=asset,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/cell-morphology/{morph_id}/assets/{asset_id}/download",
        match_headers=request_headers,
        content="foo",
    )

    morphology = CellMorphology(
        id=morph_id,
        name="foo",
        cell_morphology_protocol=CellMorphologyProtocol(
            generation_type=CellMorphologyGenerationType.placeholder
        ),
        assets=[asset],
    )

    output_path = download_morphology(
        client=client,
        morphology=morphology,
        output_dir=tmp_path,
        file_type="asc",
    )

    assert output_path.is_file()

    with pytest.raises(IteratorResultError, match="Iterable is empty."):
        download_morphology(
            client=client,
            morphology=morphology,
            output_dir=tmp_path,
            file_type="swc",
        )


def test_download_morphology_selects_asset_by_label(
    tmp_path,
    client,
    httpx_mock,
    api_url,
    request_headers,
):
    """Test selecting between morphology assets with the same content type."""
    morph_id = uuid.uuid4()
    morphology_asset_id = uuid.uuid4()
    spiny_asset_id = uuid.uuid4()

    morphology_asset = _mock_asset_response(
        morphology_asset_id,
        path="morphology.h5",
        content_type="application/x-hdf5",
        label="morphology",
    )
    spiny_asset = _mock_asset_response(
        spiny_asset_id,
        path="morphology_with_spines.h5",
        content_type="application/x-hdf5",
        label="morphology_with_spines",
    )

    for asset_id, asset in [
        (morphology_asset_id, morphology_asset),
        (spiny_asset_id, spiny_asset),
    ]:
        httpx_mock.add_response(
            method="GET",
            url=f"{api_url}/cell-morphology/{morph_id}/assets/{asset_id}",
            match_headers=request_headers,
            json=asset,
        )
        httpx_mock.add_response(
            method="GET",
            url=f"{api_url}/cell-morphology/{morph_id}/assets/{asset_id}/download",
            match_headers=request_headers,
            content="foo",
        )

    morphology = CellMorphology(
        id=morph_id,
        name="foo",
        cell_morphology_protocol=CellMorphologyProtocol(
            generation_type=CellMorphologyGenerationType.placeholder
        ),
        assets=[morphology_asset, spiny_asset],
    )

    output_path = download_morphology(
        client=client,
        morphology=morphology,
        output_dir=tmp_path,
        file_type="h5",
        asset_label=AssetLabel.morphology_with_spines,
    )

    assert output_path.name == "morphology_with_spines.h5"
    assert output_path.is_file()
