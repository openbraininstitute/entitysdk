"""Identifiable SDK client."""

import concurrent.futures
import io
import os
from pathlib import Path
from typing import Any, TypeVar, cast

import httpx

from entitysdk import core, route
from entitysdk.common import ProjectContext
from entitysdk.exception import EntitySDKError
from entitysdk.models.asset import (
    Asset,
    DetailedFileList,
    ExistingAssetMetadata,
    LocalAssetMetadata,
)
from entitysdk.models.core import Identifiable
from entitysdk.models.entity import Entity
from entitysdk.result import IteratorResult
from entitysdk.schemas.asset import DownloadedAssetFile
from entitysdk.token_manager import TokenFromValue, TokenManager
from entitysdk.types import (
    ID,
    AssetLabel,
    ContentType,
    DeploymentEnvironment,
    DerivationType,
    StorageType,
    Token,
)
from entitysdk.util import (
    build_api_url,
    create_intermediate_directories,
    validate_filename_extension_consistency,
)
from entitysdk.utils.asset import filter_assets

TIdentifiable = TypeVar("TIdentifiable", bound=Identifiable)


class Client:
    """Client for entitysdk."""

    def __init__(
        self,
        *,
        api_url: str | None = None,
        project_context: ProjectContext | None = None,
        http_client: httpx.Client | None = None,
        token_manager: TokenManager | Token,
        environment: DeploymentEnvironment | str | None = None,
    ) -> None:
        """Initialize client.

        Args:
            api_url: The API URL to entitycore service.
            project_context: Project context.
            http_client: Optional HTTP client to use.
            token_manager: Token manager or token to be used for authentication.
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
        self._token_manager = (
            TokenFromValue(token_manager) if isinstance(token_manager, Token) else token_manager
        )

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
        entity_type: type[TIdentifiable],
        project_context: ProjectContext | None = None,
    ) -> TIdentifiable:
        """Get entity from resource id.

        Args:
            entity_id: Resource id of the entity.
            entity_type: Type of the entity.
            project_context: Optional project context.

        Returns:
            entity_type instantiated by deserializing the response.
        """
        url = route.get_entities_endpoint(
            api_url=self.api_url,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        context = self._optional_user_context(override_context=project_context)
        return core.get_entity(
            url=url,
            entity_type=entity_type,
            project_context=context,
            http_client=self._http_client,
            token=self._token_manager.get_token(),
        )

    def search_entity(
        self,
        *,
        entity_type: type[TIdentifiable],
        query: dict | None = None,
        limit: int | None = None,
        project_context: ProjectContext | None = None,
    ) -> IteratorResult[TIdentifiable]:
        """Search for entities.

        Args:
            entity_type: Type of the entity.
            query: Query parameters.
            limit: Optional limit of the number of entities to yield. Default is None.
            project_context: Optional project context.
        """
        url = route.get_entities_endpoint(api_url=self.api_url, entity_type=entity_type)
        context = self._optional_user_context(override_context=project_context)
        return core.search_entities(
            url=url,
            query=query,
            limit=limit,
            project_context=context,
            entity_type=entity_type,
            http_client=self._http_client,
            token=self._token_manager.get_token(),
        )

    def get_entity_derivations(
        self,
        *,
        entity_id: ID,
        entity_type: type[Entity],
        derivation_type: DerivationType,
        project_context: ProjectContext | None = None,
    ) -> IteratorResult[Entity]:
        """Get all the derivation for an entity."""
        return core.get_entity_derivations(
            api_url=self.api_url,
            entity_id=entity_id,
            entity_type=entity_type,
            derivation_type=derivation_type,
            project_context=self._required_user_context(override_context=project_context),
            token=self._token_manager.get_token(),
        )

    def register_entity(
        self,
        entity: TIdentifiable,
        *,
        project_context: ProjectContext | None = None,
    ) -> TIdentifiable:
        """Register entity.

        Args:
            entity: Identifiable to register.
            project_context: Optional project context.

        Returns:
            Registered entity with id.
        """
        url = route.get_entities_endpoint(api_url=self.api_url, entity_type=type(entity))
        context = self._required_user_context(override_context=project_context)
        return core.register_entity(
            url=url,
            entity=entity,
            project_context=context,
            http_client=self._http_client,
            token=self._token_manager.get_token(),
        )

    def update_entity(
        self,
        entity_id: ID,
        entity_type: type[TIdentifiable],
        attrs_or_entity: dict | Identifiable,
        *,
        project_context: ProjectContext | None = None,
    ) -> TIdentifiable:
        """Update an entity.

        Args:
            entity_id: Id of the entity to update.
            entity_type: Type of the entity.
            attrs_or_entity: Attributes or entity to update.
            project_context: Optional project context.
        """
        url = route.get_entities_endpoint(
            api_url=self.api_url,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        context = self._required_user_context(override_context=project_context)
        return core.update_entity(
            url=url,
            project_context=context,
            entity_type=entity_type,
            attrs_or_entity=attrs_or_entity,
            http_client=self._http_client,
            token=self._token_manager.get_token(),
        )

    def upload_file(
        self,
        *,
        entity_id: ID,
        entity_type: type[Identifiable],
        file_path: os.PathLike,
        file_content_type: ContentType,
        file_name: str | None = None,
        file_metadata: dict | None = None,
        asset_label: AssetLabel,
        project_context: ProjectContext | None = None,
    ) -> Asset:
        """Upload asset to an existing entity's endpoint from a file path."""
        path = Path(file_path)
        url = route.get_assets_endpoint(
            api_url=self.api_url,
            entity_type=entity_type,
            entity_id=entity_id,
            asset_id=None,
        )
        context = self._required_user_context(override_context=project_context)
        asset_metadata = LocalAssetMetadata(
            file_name=file_name or path.name,
            content_type=file_content_type,
            metadata=file_metadata,
            label=asset_label,
        )
        return core.upload_asset_file(
            url=url,
            asset_path=path,
            project_context=context,
            asset_metadata=asset_metadata,
            http_client=self._http_client,
            token=self._token_manager.get_token(),
        )

    def upload_content(
        self,
        *,
        entity_id: ID,
        entity_type: type[Identifiable],
        file_content: io.BufferedIOBase,
        file_name: str,
        file_content_type: ContentType,
        file_metadata: dict | None = None,
        asset_label: AssetLabel,
        project_context: ProjectContext | None = None,
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
            label=asset_label,
        )
        context = self._required_user_context(override_context=project_context)
        return core.upload_asset_content(
            url=url,
            project_context=context,
            asset_content=file_content,
            asset_metadata=asset_metadata,
            http_client=self._http_client,
            token=self._token_manager.get_token(),
        )

    def upload_directory(
        self,
        *,
        entity_id: ID,
        entity_type: type[Identifiable],
        name: str,
        paths: dict[os.PathLike, os.PathLike],
        metadata: dict | None = None,
        label: AssetLabel,
        project_context: ProjectContext | None = None,
    ) -> Asset:
        """Attach directory to an entity from with a group of paths."""
        url = (
            route.get_assets_endpoint(
                api_url=self.api_url,
                entity_type=entity_type,
                entity_id=entity_id,
                asset_id=None,
            )
            + "/directory/upload"
        )
        context = self._required_user_context(override_context=project_context)

        paths = {Path(k): Path(v) for k, v in paths.items()}

        return core.upload_asset_directory(
            url=url,
            name=name,
            paths=paths,
            metadata=metadata,
            label=label,
            project_context=context,
            http_client=self._http_client,
            token=self._token_manager.get_token(),
        )

    def list_directory(
        self,
        *,
        entity_id: ID,
        entity_type: type[Identifiable],
        asset_id: ID,
        project_context: ProjectContext | None = None,
    ) -> DetailedFileList:
        """List directory existing entity's endpoint from a directory path."""
        url = (
            route.get_assets_endpoint(
                api_url=self.api_url,
                entity_type=entity_type,
                entity_id=entity_id,
                asset_id=asset_id,
            )
            + "/list"
        )
        context = self._required_user_context(override_context=project_context)
        return core.list_directory(
            url=url,
            project_context=context,
            http_client=self._http_client,
            token=self._token_manager.get_token(),
        )

    def download_directory(
        self,
        *,
        entity_id: ID,
        entity_type: type[Identifiable],
        asset_id: ID,
        output_path: os.PathLike,
        project_context: ProjectContext | None = None,
        ignore_directory_name: bool = False,
        max_concurrent: int = 1,
    ) -> list[Path]:
        """Download directory of assets."""
        output_path = Path(output_path)

        if output_path.exists() and output_path.is_file():
            raise EntitySDKError(f"{output_path} exists and is a file")
        output_path.mkdir(parents=True, exist_ok=True)

        context = self._optional_user_context(override_context=project_context)

        asset = cast(Asset, asset_id) if isinstance(asset_id, Asset) else None

        if not ignore_directory_name:
            if asset is None:
                asset_endpoint = route.get_assets_endpoint(
                    api_url=self.api_url,
                    entity_type=entity_type,
                    entity_id=cast(ID, entity_id),
                    asset_id=asset_id,
                )
                asset = core.get_entity(
                    asset_endpoint,
                    entity_type=Asset,
                    project_context=context,
                    http_client=self._http_client,
                    token=self._token_manager.get_token(),
                )

            output_path /= asset.path

        contents = self.list_directory(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=asset_id if isinstance(asset_id, ID) else asset.id,
            project_context=project_context,
        )

        if max_concurrent == 1:
            paths = [
                self.download_file(
                    entity_id=entity_id,
                    entity_type=entity_type,
                    asset_id=asset if asset else asset_id,
                    output_path=output_path / path,
                    asset_path=path,
                    project_context=context,
                )
                for path in contents.files
            ]
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                futures = [
                    executor.submit(
                        self.download_file,
                        entity_id=entity_id,
                        entity_type=entity_type,
                        asset_id=asset if asset else asset_id,
                        output_path=output_path / path,
                        asset_path=path,
                        project_context=context,
                    )
                    for path in contents.files
                ]
                result = concurrent.futures.wait(futures)
                paths = [res.result() for res in result.done]

        return paths

    def download_content(
        self,
        *,
        entity_id: ID,
        entity_type: type[Identifiable],
        asset_id: ID,
        asset_path: os.PathLike | None = None,
        project_context: ProjectContext | None = None,
    ) -> bytes:
        """Download asset content.

        Args:
            entity_id: Id of the entity.
            entity_type: Type of the entity.
            asset_id: Id of the asset.
            asset_path: for asset directories, the path within the directory to the file.
            project_context: Optional project context.

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
        context = self._optional_user_context(override_context=project_context)
        return core.download_asset_content(
            url=url,
            project_context=context,
            asset_path=asset_path,
            http_client=self._http_client,
            token=self._token_manager.get_token(),
        )

    def download_file(
        self,
        *,
        entity_id: ID,
        entity_type: type[Identifiable],
        asset_id: ID | Asset,
        output_path: os.PathLike,
        asset_path: os.PathLike | None = None,
        project_context: ProjectContext | None = None,
    ) -> Path:
        """Download asset file to a file path.

        Args:
            entity_id: Id of the entity.
            entity_type: Type of the entity.
            asset_id: Id of the asset.
            output_path: Either be a file path to write the file to or an output directory.
            asset_path: for asset directories, the path within the directory to the file.
            project_context: Optional project context.

        Returns:
            Output file path.
        """
        context = self._optional_user_context(override_context=project_context)

        asset_endpoint = route.get_assets_endpoint(
            api_url=self.api_url,
            entity_type=entity_type,
            entity_id=entity_id,
            asset_id=asset_id if isinstance(asset_id, ID) else asset_id.id,
        )

        if isinstance(asset_id, ID):
            asset = core.get_entity(
                asset_endpoint,
                entity_type=Asset,
                project_context=context,
                http_client=self._http_client,
                token=self._token_manager.get_token(),
            )
        else:
            asset = asset_id

        path: Path = Path(output_path)
        if asset.is_directory:
            if not asset_path:
                raise EntitySDKError("Directory from directories require an `asset_path`")
        else:
            if asset_path:
                raise EntitySDKError("Cannot pass `asset_path` to non-directories")

            path = (
                path / asset.path
                if path.is_dir()
                else validate_filename_extension_consistency(path, Path(asset.path).suffix)
            )
        create_intermediate_directories(path)
        return core.download_asset_file(
            url=f"{asset_endpoint}/download",
            project_context=context,
            asset_path=asset_path,
            output_path=path,
            http_client=self._http_client,
            token=self._token_manager.get_token(),
        )

    @staticmethod
    def select_assets(entity: Entity, selection: dict) -> IteratorResult:
        """Select assets from entity based on selection."""
        return IteratorResult(filter_assets(entity.assets, selection))

    def download_assets(
        self,
        entity_or_id: Entity | tuple[ID, type[Entity]],
        *,
        selection: dict[str, Any] | None = None,
        output_path: Path,
        project_context: ProjectContext | None = None,
    ) -> IteratorResult:
        """Download assets."""

        def _download_entity_asset(asset):
            if asset.is_directory:
                raise NotImplementedError("Downloading asset directories is not supported yet.")
            else:
                path = self.download_file(
                    entity_id=entity.id,
                    entity_type=type(entity),
                    asset_id=asset.id,
                    output_path=output_path,
                    project_context=context,
                )

            return DownloadedAssetFile(
                asset=asset,
                path=path,
            )

        context = self._optional_user_context(override_context=project_context)
        if isinstance(entity_or_id, tuple):
            entity_id, entity_type = entity_or_id
            entity = self.get_entity(
                entity_id=entity_id,
                entity_type=entity_type,
                project_context=context,
            )
        else:
            entity = entity_or_id

        if not issubclass(type(entity), Entity):
            raise EntitySDKError(f"Type {type(entity)} has no assets.")

        # make mypy happy as it doesn't get the correct type :(
        entity = cast(Entity, entity)

        if not entity.assets:
            raise EntitySDKError(f"Entity {entity.id} ({entity.name}) has no assets.")

        assets = filter_assets(entity.assets, selection) if selection else entity.assets
        return IteratorResult(map(_download_entity_asset, assets))

    def delete_asset(
        self,
        *,
        entity_id: ID,
        entity_type: type[Identifiable],
        asset_id: ID,
        project_context: ProjectContext | None = None,
    ) -> Asset:
        """Delete an entity's asset."""
        url = route.get_assets_endpoint(
            api_url=self.api_url,
            entity_type=entity_type,
            entity_id=entity_id,
            asset_id=asset_id,
        )
        context = self._required_user_context(override_context=project_context)
        return core.delete_asset(
            url=url,
            project_context=context,
            http_client=self._http_client,
            token=self._token_manager.get_token(),
        )

    def update_asset_file(
        self,
        *,
        entity_id: ID,
        entity_type: type[Identifiable],
        asset_id: ID,
        file_path: os.PathLike,
        file_content_type: ContentType,
        file_name: str | None = None,
        file_metadata: dict | None = None,
        project_context: ProjectContext | None = None,
    ) -> Asset:
        """Update an entity's asset file.

        Note: This operation is not atomic. Deletion can succeed and upload can fail.
        """
        deleted_asset = self.delete_asset(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=asset_id,
            project_context=project_context,
        )
        return self.upload_file(
            entity_id=entity_id,
            entity_type=entity_type,
            file_path=file_path,
            file_content_type=file_content_type,
            file_name=file_name,
            file_metadata=file_metadata,
            project_context=project_context,
            asset_label=deleted_asset.label,
        )

    def register_asset(
        self,
        *,
        entity_id: ID,
        entity_type: type[Identifiable],
        name: str,
        storage_path: str,
        storage_type: StorageType,
        is_directory: bool,
        content_type: ContentType,
        asset_label: AssetLabel,
        project_context: ProjectContext | None = None,
    ) -> Asset:
        """Register a file or directory already existing."""
        url = (
            route.get_assets_endpoint(
                api_url=self.api_url,
                entity_type=entity_type,
                entity_id=entity_id,
                asset_id=None,
            )
            + "/register"
        )
        asset_metadata = ExistingAssetMetadata(
            path=name,
            full_path=storage_path,
            storage_type=storage_type,
            is_directory=is_directory,
            content_type=content_type,
            label=asset_label,
        )
        context = self._required_user_context(override_context=project_context)
        return core.register_asset(
            url=url,
            project_context=context,
            asset_metadata=asset_metadata,
            http_client=self._http_client,
            token=self._token_manager.get_token(),
        )
