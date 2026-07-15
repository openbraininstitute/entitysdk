import uuid

import pytest
from pydantic import ValidationError

from entitysdk.client import Client
from entitysdk.models import Asset, MTypeClass
from entitysdk.models.entity import Entity
from entitysdk.types import (
    AssetLabel,
    AssetStatus,
    ContentType,
    StorageType,
)


def _asset(*, asset_id: uuid.UUID | None) -> Asset:
    return Asset(
        id=asset_id,
        path="path/to/asset",
        full_path="full/path/to/asset",
        storage_type=StorageType.aws_s3_internal,
        label=AssetLabel.morphology,
        is_directory=False,
        content_type=ContentType.text_plain,
        size=1,
        status=AssetStatus.created,
    )


def test_register_entity_rejects_registered_input(client):
    with pytest.raises(ValidationError):
        client.register_entity(entity=Entity(id=uuid.uuid4(), name="entity"))


def test_register_entity_accepts_unregistered_input(client, httpx_mock, api_url, request_headers):
    entity_id = uuid.uuid4()
    httpx_mock.add_response(
        method="POST",
        url=f"{api_url}/entity",
        match_headers=request_headers,
        json={"id": str(entity_id), "name": "entity"},
    )

    registered = client.register_entity(entity=Entity(name="entity"))

    assert registered.id == entity_id


def test_fetch_file_rejects_unregistered_asset(client, tmp_path):
    with pytest.raises(ValidationError):
        client.fetch_file(
            entity_id=uuid.uuid4(),
            entity_type=Entity,
            asset_id=_asset(asset_id=None),
            output_path=tmp_path / "out.txt",
        )


def test_select_assets_rejects_unregistered_entity():
    with pytest.raises(ValidationError):
        Client.select_assets(Entity(name="entity"), {"label": "morphology"})


def test_download_assets_rejects_non_entity_type(client, tmp_path):
    with pytest.raises(ValidationError):
        client.download_assets(
            (uuid.uuid4(), MTypeClass),
            output_path=tmp_path,
        )


def test_fetch_assets_accepts_registered_entity(
    client, httpx_mock, api_url, request_headers, project_context, tmp_path
):
    entity_id = uuid.uuid4()
    asset_id = uuid.uuid4()

    entity = Entity(
        id=entity_id,
        name="entity",
        assets=[
            Asset(
                id=asset_id,
                path="foo.json",
                full_path="full/path/to/asset",
                storage_type=StorageType.aws_s3_internal,
                label=AssetLabel.morphology,
                is_directory=False,
                content_type=ContentType.application_json,
                size=1,
                status=AssetStatus.created,
            ),
        ],
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset_id}",
        match_headers=request_headers,
        json={
            "id": str(asset_id),
            "path": "foo.json",
            "full_path": "full/path/to/asset",
            "storage_type": "aws_s3_internal",
            "label": "morphology",
            "is_directory": False,
            "content_type": "application/json",
            "size": 1,
            "status": "created",
            "meta": {},
        },
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{api_url}/entity/{entity_id}/assets/{asset_id}/download",
        match_headers=request_headers,
        content=b"data",
    )

    downloaded = client.fetch_assets(
        entity,
        output_path=tmp_path,
        project_context=project_context,
    ).one()

    assert downloaded.asset.id == asset_id
    assert downloaded.path == tmp_path / "foo.json"
