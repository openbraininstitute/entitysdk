"""Identifiable SDK client."""

import io
import os
from pathlib import Path

import httpx

from entitysdk import core, route
from entitysdk.common import ProjectContext
from entitysdk.exception import EntitySDKError
from entitysdk.models.asset import Asset, LocalAssetMetadata
from entitysdk.models.core import Identifiable
from entitysdk.result import IteratorResult
from entitysdk.token_manager import TokenManager
from entitysdk.types import ID, DeploymentEnvironment
from entitysdk.util import build_api_url


class Client:
    """Client for entitysdk."""

    def __init__(
        self,
        api_url: str | None = None,
        project_context: ProjectContext | None = None,
        http_client: httpx.Client | None = None,
        token_manager: TokenManager | None = None,
        environment: DeploymentEnvironment | str | None = None,
    ) -> None:
        """Initialize client.

        Args:
            api_url: The API URL to entitycore service.
            project_context: Project context.
            http_client: Optional HTTP client to use.
            token_manager: Optional token manager to use.
            environment: Deployment environent.
        """
        try:
            environment = DeploymentEnvironment(environment) if environment else None
        except ValueError:
            raise EntitySDKError(
                f"'{environment}' is not a valid DeploymentEnvironment. "
                f"Choose one of: {[str(env) for env in DeploymentEnvironment]}"
            ) from None

        self.api_url = self._handle_api_url(
            api_url=api_url,
            environment=environment,
        )
        self.project_context = project_context
        self._http_client = http_client or httpx.Client()
        self._token_manager = token_manager

    @staticmethod
    def _handle_api_url(api_url: str | None, environment: DeploymentEnvironment | None) -> str:
        """Return or create api url."""
        match (api_url, environment):
            case (str(), None):
                return api_url
            case (None, DeploymentEnvironment()):
                return build_api_url(environment=environment)
            case (None, None):
                raise EntitySDKError("Neither api_url nor environment have been defined.")
            case (str(), DeploymentEnvironment()):
                raise EntitySDKError("Either the api_url or environment must be defined, not both.")
            case _:
                raise EntitySDKError("Either api_url or environment is of the wrong type.")

    def _get_token(self, override_token: str | None = None) -> str:
        """Get a token either from an override or from the token manager.

        Args:
            override_token: Optional override token.

        Returns:
            Token.
        """
        if override_token:
            return override_token
        if self._token_manager is None:
            raise EntitySDKError("Either override_token or token_manager must be provided.")
        return self._token_manager.get_token()

    def _optional_user_context(
        self, override_context: ProjectContext | None
    ) -> ProjectContext | None:
        return override_context or self.project_context

    def _required_user_context(self, override_context: ProjectContext | None) -> ProjectContext:
        context = self._optional_user_context(override_context)
        if context is None:
            raise EntitySDKError("A project context is mandatory for this operation.")
        return context

    def get_entity(
        self,
        entity_id: ID,
        *,
        entity_type: type[Identifiable],
        with_assets: bool = True,
        project_context: ProjectContext | None = None,
        token: str | None = None,
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
        url = route.get_entities_endpoint(
            api_url=self.api_url,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        token = self._get_token(override_token=token)
        context = self._optional_user_context(override_context=project_context)
        entity = core.get_entity(
            url=url,
            token=token,
            entity_type=entity_type,
            project_context=context,
            http_client=self._http_client,
        )
        if with_assets and "assets" in entity_type.model_fields:
            url = route.get_assets_endpoint(
                api_url=self.api_url,
                entity_type=entity_type,
                entity_id=entity_id,
            )
            assets = core.get_entity_assets(
                url=url,
                token=token,
                project_context=context,
                http_client=self._http_client,
            )
            entity = entity.evolve(assets=assets)

        return entity

    def search_entity(
        self,
        *,
        entity_type: type[Identifiable],
        query: dict | None = None,
        limit: int | None = None,
        project_context: ProjectContext | None = None,
        token: str | None = None,
    ) -> IteratorResult[Identifiable]:
        """Search for entities.

        Args:
            entity_type: Type of the entity.
            query: Query parameters.
            limit: Optional limit of the number of entities to yield. Default is None.
            project_context: Optional project context.
            token: Authorization access token.
        """
        url = route.get_entities_endpoint(api_url=self.api_url, entity_type=entity_type)
        token = self._get_token(override_token=token)
        context = self._optional_user_context(override_context=project_context)
        return core.search_entities(
            url=url,
            query=query,
            limit=limit,
            token=token,
            project_context=context,
            entity_type=entity_type,
            http_client=self._http_client,
        )

    def register_entity(
        self,
        entity: Identifiable,
        *,
        project_context: ProjectContext | None = None,
        token: str | None = None,
    ) -> Identifiable:
        """Register entity.

        Args:
            entity: Identifiable to register.
            project_context: Optional project context.
            token: Authorization access token.

        Returns:
            Registered entity with id.
        """
        url = route.get_entities_endpoint(api_url=self.api_url, entity_type=type(entity))
        context = self._required_user_context(override_context=project_context)
        token = self._get_token(override_token=token)
        return core.register_entity(
            url=url,
            token=token,
            entity=entity,
            project_context=context,
            http_client=self._http_client,
        )

    def update_entity(
        self,
        entity_id: ID,
        entity_type: type[Identifiable],
        attrs_or_entity: dict | Identifiable,
        *,
        project_context: ProjectContext | None = None,
        token: str | None = None,
    ) -> Identifiable:
        """Update an entity.

        Args:
            entity_id: Id of the entity to update.
            entity_type: Type of the entity.
            attrs_or_entity: Attributes or entity to update.
            project_context: Optional project context.
            token: Authorization access token.
        """
        url = route.get_entities_endpoint(
            api_url=self.api_url,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        token = self._get_token(override_token=token)
        context = self._required_user_context(override_context=project_context)
        return core.update_entity(
            url=url,
            token=token,
            project_context=context,
            entity_type=entity_type,
            attrs_or_entity=attrs_or_entity,
            http_client=self._http_client,
        )

    def upload_file(
        self,
        *,
        entity_id: ID,
        entity_type: type[Identifiable],
        file_path: os.PathLike,
        file_content_type: str,
        file_name: str | None = None,
        file_metadata: dict | None = None,
        project_context: ProjectContext | None = None,
        token: str | None = None,
    ) -> Asset:
        """Upload asset to an existing entity's endpoint from a file path."""
        path = Path(file_path)
        url = route.get_assets_endpoint(
            api_url=self.api_url,
            entity_type=entity_type,
            entity_id=entity_id,
            asset_id=None,
        )
        token = self._get_token(override_token=token)
        context = self._required_user_context(override_context=project_context)
        asset_metadata = LocalAssetMetadata(
            file_name=file_name or path.name,
            content_type=file_content_type,
            metadata=file_metadata,
        )
        return core.upload_asset_file(
            url=url,
            token=token,
            asset_path=path,
            project_context=context,
            asset_metadata=asset_metadata,
            http_client=self._http_client,
        )

    def upload_content(
        self,
        *,
        entity_id: ID,
        entity_type: type[Identifiable],
        file_content: io.BufferedIOBase,
        file_name: str,
        file_content_type: str,
        file_metadata: dict | None = None,
        project_context: ProjectContext | None = None,
        token: str,
    ) -> Asset:
        """Upload asset to an existing entity's endpoint from a file-like object."""
        url = route.get_assets_endpoint(
            api_url=self.api_url,
            entity_type=entity_type,
            entity_id=entity_id,
            asset_id=None,
        )
        asset_metadata = LocalAssetMetadata(
            file_name=file_name,
            content_type=file_content_type,
            metadata=file_metadata or {},
        )
        token = self._get_token(override_token=token)
        context = self._required_user_context(override_context=project_context)
        return core.upload_asset_content(
            url=url,
            token=token,
            project_context=context,
            asset_content=file_content,
            asset_metadata=asset_metadata,
            http_client=self._http_client,
        )

    def download_content(
        self,
        *,
        entity_id: ID,
        entity_type: type[Identifiable],
        asset_id: str,
        project_context: ProjectContext | None = None,
        token: str | None = None,
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
        url = (
            route.get_assets_endpoint(
                api_url=self.api_url,
                entity_type=entity_type,
                entity_id=entity_id,
                asset_id=asset_id,
            )
            + "/download"
        )
        token = self._get_token(override_token=token)
        context = self._optional_user_context(override_context=project_context)
        return core.download_asset_content(
            url=url,
            token=token,
            project_context=context,
            http_client=self._http_client,
        )

    def download_file(
        self,
        *,
        entity_id: ID,
        entity_type: type[Identifiable],
        asset_id: str,
        output_path: os.PathLike,
        project_context: ProjectContext | None = None,
        token: str | None = None,
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
        url = (
            route.get_assets_endpoint(
                api_url=self.api_url,
                entity_type=entity_type,
                entity_id=entity_id,
                asset_id=asset_id,
            )
            + "/download"
        )
        token = self._get_token(override_token=token)
        context = self._optional_user_context(override_context=project_context)
        return core.download_asset_file(
            url=url,
            token=token,
            project_context=context,
            output_path=Path(output_path),
            http_client=self._http_client,
        )

    def delete_asset(
        self,
        *,
        entity_id: ID,
        entity_type: type[Identifiable],
        asset_id: ID,
        project_context: ProjectContext | None = None,
        token: str | None = None,
    ) -> Asset:
        """Delete an entity's asset."""
        url = route.get_assets_endpoint(
            api_url=self.api_url,
            entity_type=entity_type,
            entity_id=entity_id,
            asset_id=asset_id,
        )
        token = self._get_token(override_token=token)
        context = self._required_user_context(override_context=project_context)
        return core.delete_asset(
            url=url,
            token=token,
            project_context=context,
            http_client=self._http_client,
        )

    def update_asset_file(
        self,
        *,
        entity_id: ID,
        entity_type: type[Identifiable],
        asset_id: ID,
        file_path: os.PathLike,
        file_content_type: str,
        file_name: str | None = None,
        file_metadata: dict | None = None,
        project_context: ProjectContext | None = None,
        token: str | None = None,
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
