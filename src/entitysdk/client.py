"""Identifiable SDK client."""

import io
import os
from collections.abc import Iterator
from pathlib import Path

import httpx

from entitysdk import route, serdes
from entitysdk.common import ProjectContext
from entitysdk.models.asset import Asset, LocalAssetMetadata
from entitysdk.models.core import Identifiable
from entitysdk.result import IteratorResult
from entitysdk.util import make_db_api_request, stream_paginated_request


class Client:
    """Client for entitysdk."""

    def __init__(
        self,
        api_url: str,
        project_context: ProjectContext | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        """Initialize client.

        Args:
            api_url: The API URL to entitycore service.
            project_context: Project context.
            http_client: Optional HTTP client to use.
        """
        self.api_url = api_url.rstrip("/")
        self.project_context = project_context
        self._http_client = http_client or httpx.Client()

    def _project_context(self, override_context: ProjectContext | None) -> ProjectContext:
        context = override_context or self.project_context

        if context is None:
            raise ValueError("A project context must be specified.")

        return context

    def get_entity(
        self,
        entity_id: str,
        *,
        entity_type: type[Identifiable],
        with_assets: bool = True,
        project_context: ProjectContext | None = None,
        token: str,
    ) -> Identifiable:
        """Get entity from resource id.

        Args:
            entity_id: Resource id of the entity.
            entity_type: Type of the entity.
            with_assets: Whether to include assets in the response.
            project_context: Optional project context.
            token: Authorization access token.

        Returns:
            entity_type instantiated by deserializing the response.
        """
        entity = get_entity(
            url=route.get_entities_endpoint(
                api_url=self.api_url, entity_type=entity_type, entity_id=entity_id
            ),
            entity_type=entity_type,
            project_context=self._project_context(override_context=project_context),
            token=token,
            http_client=self._http_client,
        )
        if with_assets and "assets" in entity_type.model_fields:
            assets = get_entity_assets(
                url=route.get_assets_endpoint(
                    api_url=self.api_url,
                    entity_type=entity_type,
                    entity_id=entity_id,
                ),
                project_context=self._project_context(override_context=project_context),
                token=token,
                http_client=self._http_client,
            )
            entity = entity.evolve(assets=assets)

        return entity

    def search_entity(
        self,
        *,
        entity_type: type[Identifiable],
        query: dict | None = None,
        limit: int = 0,
        project_context: ProjectContext | None = None,
        token: str,
    ) -> IteratorResult[Identifiable]:
        """Search for entities.

        Args:
            entity_type: Type of the entity.
            query: Query parameters.
            limit: Limit the number of entities to yield. Default is 0, no limit.
            project_context: Optional project context.
            token: Authorization access token.
        """
        return search_entities(
            url=route.get_entities_endpoint(api_url=self.api_url, entity_type=entity_type),
            entity_type=entity_type,
            query=query,
            limit=limit,
            project_context=self._project_context(override_context=project_context),
            token=token,
            http_client=self._http_client,
        )

    def register_entity(
        self, entity: Identifiable, *, project_context: ProjectContext | None = None, token: str
    ) -> Identifiable:
        """Register entity.

        Args:
            entity: Identifiable to register.
            project_context: Optional project context.
            token: Authorization access token.

        Returns:
            Registered entity with id.
        """
        return register_entity(
            url=route.get_entities_endpoint(api_url=self.api_url, entity_type=type(entity)),
            entity=entity,
            project_context=self._project_context(override_context=project_context),
            token=token,
            http_client=self._http_client,
        )

    def update_entity(
        self,
        entity_id: str,
        entity_type: type[Identifiable],
        attrs_or_entity: dict | Identifiable,
        *,
        project_context: ProjectContext | None = None,
        token: str,
    ) -> Identifiable:
        """Update an entity.

        Args:
            entity_id: Id of the entity to update.
            entity_type: Type of the entity.
            attrs_or_entity: Attributes or entity to update.
            project_context: Optional project context.
            token: Authorization access token.
        """
        return update_entity(
            url=route.get_entities_endpoint(
                api_url=self.api_url, entity_type=entity_type, entity_id=entity_id
            ),
            entity_type=entity_type,
            attrs_or_entity=attrs_or_entity,
            project_context=self._project_context(override_context=project_context),
            token=token,
            http_client=self._http_client,
        )

    def upload_file(
        self,
        *,
        entity_id: str,
        entity_type: type[Identifiable],
        file_path: os.PathLike,
        file_content_type: str,
        file_name: str | None = None,
        file_metadata: dict | None = None,
        project_context: ProjectContext | None = None,
        token: str,
    ) -> Asset:
        """Upload asset to an existing entity's endpoint from a file path."""
        path = Path(file_path)
        asset_metadata = LocalAssetMetadata(
            file_name=file_name or path.name,
            content_type=file_content_type,
            metadata=file_metadata,
        )
        return upload_asset_file(
            url=route.get_assets_endpoint(
                api_url=self.api_url,
                entity_type=entity_type,
                entity_id=entity_id,
                asset_id=None,
            ),
            asset_path=path,
            asset_metadata=asset_metadata,
            project_context=self._project_context(override_context=project_context),
            token=token,
            http_client=self._http_client,
        )

    def upload_content(
        self,
        *,
        entity_id: str,
        entity_type: type[Identifiable],
        file_content: io.BufferedIOBase,
        file_name: str,
        file_content_type: str,
        file_metadata: dict | None = None,
        project_context: ProjectContext | None = None,
        token: str,
    ) -> Asset:
        """Upload asset to an existing entity's endpoint from a file-like object."""
        asset_metadata = LocalAssetMetadata(
            file_name=file_name,
            content_type=file_content_type,
            metadata=file_metadata or {},
        )
        return upload_asset_content(
            url=route.get_assets_endpoint(
                api_url=self.api_url,
                entity_type=entity_type,
                entity_id=entity_id,
                asset_id=None,
            ),
            asset_content=file_content,
            asset_metadata=asset_metadata,
            project_context=self._project_context(override_context=project_context),
            token=token,
            http_client=self._http_client,
        )

    def download_content(
        self,
        *,
        entity_id: str,
        entity_type: type[Identifiable],
        asset_id: str,
        project_context: ProjectContext | None = None,
        token: str,
    ) -> bytes:
        """Download asset content.

        Args:
            entity_id: Id of the entity.
            entity_type: Type of the entity.
            asset_id: Id of the asset.
            project_context: Optional project context.
            token: Authorization access token.

        Returns:
            Asset content in bytes.
        """
        assets_route = route.get_assets_endpoint(
            api_url=self.api_url,
            entity_type=entity_type,
            entity_id=entity_id,
            asset_id=asset_id,
        )
        return download_asset_content(
            f"{assets_route}/download",
            project_context=self._project_context(override_context=project_context),
            token=token,
            http_client=self._http_client,
        )

    def download_file(
        self,
        *,
        entity_id: str,
        entity_type: type[Identifiable],
        asset_id: str,
        output_path: os.PathLike,
        project_context: ProjectContext | None = None,
        token: str,
    ) -> None:
        """Download asset file to a file path.

        Args:
            entity_id: Id of the entity.
            entity_type: Type of the entity.
            asset_id: Id of the asset.
            output_path: Path to save the file to.
            project_context: Optional project context.
            token: Authorization access token.
        """
        assets_route = route.get_assets_endpoint(
            api_url=self.api_url,
            entity_type=entity_type,
            entity_id=entity_id,
            asset_id=asset_id,
        )
        return download_asset_file(
            url=f"{assets_route}/download",
            output_path=Path(output_path),
            project_context=self._project_context(override_context=project_context),
            token=token,
            http_client=self._http_client,
        )

    def delete_asset(
        self,
        *,
        entity_id: str,
        entity_type: type[Identifiable],
        asset_id: str,
        project_context: ProjectContext | None = None,
        token: str,
    ) -> Asset:
        """Delete an entity's asset."""
        return delete_asset(
            url=route.get_assets_endpoint(
                api_url=self.api_url,
                entity_type=entity_type,
                entity_id=entity_id,
                asset_id=asset_id,
            ),
            project_context=self._project_context(override_context=project_context),
            token=token,
            http_client=self._http_client,
        )

    def update_asset_file(
        self,
        *,
        entity_id: str,
        entity_type: type[Identifiable],
        asset_id: str,
        file_path: os.PathLike,
        file_content_type: str,
        file_name: str | None = None,
        file_metadata: dict | None = None,
        project_context: ProjectContext | None = None,
        token: str,
    ) -> Asset:
        """Update an entity's asset file.

        Note: This operation is not atomic. Deletion can succeed and upload can fail.
        """
        self.delete_asset(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=asset_id,
            project_context=project_context,
            token=token,
        )
        return self.upload_file(
            entity_id=entity_id,
            entity_type=entity_type,
            file_path=file_path,
            file_content_type=file_content_type,
            file_name=file_name,
            file_metadata=file_metadata,
            project_context=project_context,
            token=token,
        )


def search_entities(
    url: str,
    *,
    entity_type: type[Identifiable],
    query: dict | None = None,
    limit: int,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> IteratorResult[Identifiable]:
    """Search for entities.

    Args:
        url: URL of the resource.
        entity_type: Type of the entity.
        query: Query parameters
        limit: Limit the number of entities to return.
        project_context: Project context.
        token: Authorization access token.
        http_client: HTTP client.

    Returns:
        List of entities.
    """
    iterator: Iterator[dict] = stream_paginated_request(
        url=url,
        method="GET",
        parameters=query,
        limit=limit,
        project_context=project_context,
        token=token,
        http_client=http_client,
    )
    return IteratorResult(
        serdes.deserialize_entity(json_data, entity_type) for json_data in iterator
    )


def get_entity(
    url: str,
    entity_type: type[Identifiable],
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> Identifiable:
    """Instantiate entity with model ``entity_type`` from resource id."""
    response = make_db_api_request(
        url=url,
        method="GET",
        json=None,
        project_context=project_context,
        token=token,
        http_client=http_client,
    )

    return serdes.deserialize_entity(response.json(), entity_type)


def get_entity_assets(
    url: str,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> list[Asset]:
    """Get entity assets.

    Args:
        url: URL of the resource.
        project_context: Project context.
        token: Authorization access token.
        http_client: HTTP client.

    Returns:
        List of assets.
    """
    response = make_db_api_request(
        url=url,
        method="GET",
        project_context=project_context,
        token=token,
        http_client=http_client,
    )
    return [serdes.deserialize_entity(asset, Asset) for asset in response.json()["data"]]


def register_entity(
    url: str,
    *,
    entity: Identifiable,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> Identifiable:
    """Register entity."""
    json_data = serdes.serialize_entity(entity)

    response = make_db_api_request(
        url=url,
        method="POST",
        json=json_data,
        project_context=project_context,
        token=token,
        http_client=http_client,
    )
    return serdes.deserialize_entity(response.json(), type(entity))


def update_entity(
    url: str,
    *,
    entity_type: type[Identifiable],
    attrs_or_entity: dict | Identifiable,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> Identifiable:
    """Update entity."""
    if isinstance(attrs_or_entity, dict):
        json_data = serdes.serialize_dict(attrs_or_entity)
    else:
        json_data = serdes.serialize_entity(attrs_or_entity)

    response = make_db_api_request(
        url=url,
        method="PATCH",
        json=json_data,
        project_context=project_context,
        token=token,
        http_client=http_client,
    )

    json_data = response.json()

    return serdes.deserialize_entity(json_data, entity_type)


def upload_asset_file(
    url: str,
    *,
    asset_path: Path,
    asset_metadata: LocalAssetMetadata,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> Asset:
    """Upload asset to an existing entity's endpoint from a file path."""
    with open(asset_path, "rb") as file_content:
        return upload_asset_content(
            url=url,
            asset_content=file_content,
            asset_metadata=asset_metadata,
            project_context=project_context,
            token=token,
            http_client=http_client,
        )


def upload_asset_content(
    url: str,
    *,
    asset_content: io.BufferedIOBase,
    asset_metadata: LocalAssetMetadata,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> Asset:
    """Upload asset to an existing entity's endpoint from a file-like object."""
    files = {
        "file": (
            asset_metadata.file_name,
            asset_content,
            asset_metadata.content_type,
        )
    }
    response = make_db_api_request(
        url=url,
        method="POST",
        files=files,
        project_context=project_context,
        token=token,
        http_client=http_client,
    )
    return serdes.deserialize_entity(response.json(), Asset)


def download_asset_file(
    url: str,
    *,
    output_path: Path,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> None:
    """Download asset file to a file path.

    Args:
        url: URL of the asset.
        output_path: Path to save the file to.
        project_context: Project context.
        token: Authorization access token.
        http_client: HTTP client.
    """
    bytes_content = download_asset_content(
        url=url,
        project_context=project_context,
        token=token,
        http_client=http_client,
    )
    output_path.write_bytes(bytes_content)


def download_asset_content(
    url: str,
    *,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> bytes:
    """Download asset content.

    Args:
        url: URL of the asset.
        project_context: Project context.
        token: Authorization access token.
        http_client: HTTP client.

    Returns:
        Asset content in bytes.
    """
    response = make_db_api_request(
        url=url,
        method="GET",
        project_context=project_context,
        token=token,
        http_client=http_client,
    )
    return response.content


def delete_asset(
    url: str,
    *,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> Asset:
    """Delete asset."""
    response = make_db_api_request(
        url=url,
        method="DELETE",
        project_context=project_context,
        token=token,
        http_client=http_client,
    )
    return serdes.deserialize_entity(response.json(), Asset)
