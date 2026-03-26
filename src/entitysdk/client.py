"""Identifiable SDK client."""

import concurrent.futures
import io
import os
from pathlib import Path
from typing import Any, TypeVar, cast

import httpx
from pydantic import validate_call

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
from entitysdk.schemas.asset import DownloadedAssetFile, MultipartUploadTransferConfig
from entitysdk.token_manager import TokenFromValue, TokenManager
from entitysdk.types import (
    ID,
    AssetLabel,
    AssetStatus,
    ContentType,
    DeploymentEnvironment,
    DerivationType,
    FetchContentStrategy,
    FetchFileStrategy,
    StorageType,
    StrOrPath,
    Token,
)
from entitysdk.utils.asset import filter_assets
from entitysdk.utils.store import LocalAssetStore
from entitysdk.utils.url import (
    build_api_url,
)

TEntity = TypeVar("TEntity", bound=Entity)
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
        local_store: LocalAssetStore | None = None,
    ) -> None:
        """Initialize client.

        Args:
            api_url: The API URL to entitycore service.
            project_context: Project context.
            http_client: Optional HTTP client to use.
            token_manager: Token manager or token to be used for authentication.
            environment: Deployment environent.
            local_store: LocalAssetStore object for using a local store.
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
        self._local_store = local_store

    @staticmethod
    def _handle_api_url(api_url: str | None, environment: DeploymentEnvironment | None) -> str:
        """Return or create an API URL."""
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
        """Return an optional project context."""
        return override_context or self.project_context

    def _required_user_context(self, override_context: ProjectContext | None) -> ProjectContext:
        """Return a required project context."""
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
        options: dict | None = None,
        admin: bool = False,
    ) -> TIdentifiable:
        """Get entity from resource id.

        Args:
            entity_id: Resource id of the entity.
            entity_type: Type of the entity.
            project_context: Optional project context.
            options: Optional dict with options to be passed.
            admin: Whether to use the admin endpoint or not.

        Returns:
            entity_type instantiated by deserializing the response.
        """
        url = route.get_entities_endpoint(
            api_url=self.api_url,
            entity_type=entity_type,
            entity_id=entity_id,
            admin=admin,
        )
        context = (
            self._optional_user_context(override_context=project_context) if not admin else None
        )
        return core.get_entity(
            url=url,
            options=options,
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
        """Get all derivations for an entity.

        Args:
            entity_id: Resource id of the entity.
            entity_type: Type of the entity.
            derivation_type: Derivation type to filter by.
            project_context: Optional project context.

        Returns:
            An iterator over derivation entities.
        """
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
        context = self._optional_user_context(override_context=project_context)
        return core.register_entity(
            url=url,
            entity=entity,
            project_context=context,
            http_client=self._http_client,
            token=self._token_manager.get_token(),
        )

    def get_entity_assets(
        self,
        entity_id: ID,
        *,
        entity_type: type[TEntity],
        project_context: ProjectContext | None = None,
        admin: bool = False,
    ) -> IteratorResult[Asset]:
        """Get all assets of an entity.

        Args:
            entity_id: Resource id of the entity.
            entity_type: Type of the entity.
            project_context: Optional project context.
            admin: Whether to use the admin endpoint or not.

        Returns:
            An iterator over assets.
        """
        context = (
            self._optional_user_context(override_context=project_context) if not admin else None
        )
        return core.get_entity_assets(
            api_url=self.api_url,
            entity_id=entity_id,
            entity_type=entity_type,
            project_context=context,
            http_client=self._http_client,
            token=self._token_manager.get_token(),
            admin=admin,
        )

    def update_entity(
        self,
        entity_id: ID,
        entity_type: type[TIdentifiable],
        attrs_or_entity: dict | Identifiable,
        *,
        project_context: ProjectContext | None = None,
        admin: bool = False,
    ) -> TIdentifiable:
        """Update an entity.

        Args:
            entity_id: Id of the entity to update.
            entity_type: Type of the entity.
            attrs_or_entity: Attributes or entity to update.
            project_context: Optional project context.
            admin: whether to use the admin endpoint or not.
        """
        url = route.get_entities_endpoint(
            api_url=self.api_url,
            entity_type=entity_type,
            entity_id=entity_id,
            admin=admin,
        )
        context = (
            self._optional_user_context(override_context=project_context) if not admin else None
        )
        return core.update_entity(
            url=url,
            project_context=context,
            entity_type=entity_type,
            attrs_or_entity=attrs_or_entity,
            http_client=self._http_client,
            token=self._token_manager.get_token(),
        )

    def delete_entity(
        self,
        entity_id: ID,
        entity_type: type[Identifiable],
        *,
        admin: bool = False,
    ) -> None:
        """Delete an entity.

        Args:
            entity_id: Resource id of the entity to delete.
            entity_type: Type of the entity.
            admin: Whether to use the admin endpoint or not.
        """
        url = route.get_entities_endpoint(
            api_url=self.api_url,
            entity_type=entity_type,
            entity_id=entity_id,
            admin=admin,
        )
        core.delete_entity(
            url=url,
            entity_type=entity_type,
            http_client=self._http_client,
            token=self._token_manager.get_token(),
        )

    def upload_file(
        self,
        *,
        entity_id: ID,
        entity_type: type[Entity],
        file_path: os.PathLike,
        file_content_type: ContentType,
        file_name: str | None = None,
        file_metadata: dict | None = None,
        asset_label: AssetLabel,
        project_context: ProjectContext | None = None,
        transfer_config: MultipartUploadTransferConfig | None = None,
    ) -> Asset:
        """Upload a file to an entity.

        Args:
            entity_id: Resource id of the entity.
            entity_type: Type of the entity.
            file_path: Path to the local file to upload.
            file_content_type: MIME content type for the uploaded file.
            file_name: Optional override for the uploaded filename.
            file_metadata: Optional extra metadata to attach to the asset.
            asset_label: Label for the asset.
            project_context: Optional project context.
            transfer_config: Optional multipart upload configuration.

        Returns:
            The created Asset.
        """
        context = self._required_user_context(override_context=project_context)

        asset_path = Path(file_path)

        asset_metadata = LocalAssetMetadata(
            file_name=file_name or asset_path.name,
            content_type=file_content_type,
            metadata=file_metadata,
            label=asset_label,
        )
        return core.upload_asset_file(
            api_url=self.api_url,
            entity_id=entity_id,
            entity_type=entity_type,
            asset_path=asset_path,
            asset_metadata=asset_metadata,
            http_client=self._http_client,
            project_context=context,
            token_manager=self._token_manager,
            transfer_config=transfer_config,
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
        """Upload file-like content to an entity.

        Args:
            entity_id: Resource id of the entity.
            entity_type: Type of the entity.
            file_content: File-like object containing binary content.
            file_name: Filename to report to the backend.
            file_content_type: MIME content type for the uploaded content.
            file_metadata: Optional extra metadata to attach to the asset.
            asset_label: Label for the asset.
            project_context: Optional project context.

        Returns:
            The created Asset.
        """
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
        """Attach a local directory to an entity.

        Args:
            entity_id: Resource id of the entity.
            entity_type: Type of the entity.
            name: Directory name to attach.
            paths: Mapping of relative paths to local paths (or the other
                way around, depending on the backend expectations).
            metadata: Optional extra metadata to attach to the directory asset.
            label: Label for the asset.
            project_context: Optional project context.

        Returns:
            The created directory Asset.
        """
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
        """List files in a directory asset.

        Args:
            entity_id: Resource id of the entity.
            entity_type: Type of the entity.
            asset_id: Directory asset id.
            project_context: Optional project context.

        Returns:
            A `DetailedFileList` describing the directory contents.
        """
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

    @validate_call
    def fetch_directory(
        self,
        *,
        entity_id: ID,
        entity_type: type[Identifiable],
        asset_id: ID | Asset,
        output_path: Path,
        project_context: ProjectContext | None = None,
        ignore_directory_name: bool = False,
        max_concurrent: int = 1,
        strategy: FetchFileStrategy = FetchFileStrategy.link_or_download,
    ) -> list[Path]:
        """Fetch a directory asset to a local output directory.

        Args:
            entity_id: Resource id of the entity owning the directory.
            entity_type: Entity type.
            asset_id: Directory asset id, or an `Asset` object.
            output_path: Local output base path to write files to.
            project_context: Optional project context.
            ignore_directory_name: If `True`, do not create an extra nested
                folder for the directory name.
            max_concurrent: Maximum number of concurrent downloads.
            strategy: Strategy controlling how files are materialized.

        Returns:
            List of output file paths that were created.

        Raises:
            EntitySDKError: If `output_path` exists and is a file.
        """
        if output_path.is_file():
            raise EntitySDKError(f"{output_path} exists and is a file")

        output_path.mkdir(parents=True, exist_ok=True)

        context = self._optional_user_context(override_context=project_context)

        if isinstance(asset_id, Asset):
            asset = asset_id
            asset_id = asset.id
        else:
            asset = None

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
            asset_id=asset_id,
            project_context=project_context,
        )

        if max_concurrent == 1:
            paths = [
                self.fetch_file(
                    entity_id=entity_id,
                    entity_type=entity_type,
                    asset_id=asset or asset_id,
                    output_path=output_path / path,
                    asset_path=path,
                    project_context=context,
                    strategy=strategy,
                )
                for path in contents.files
            ]
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                futures = [
                    executor.submit(
                        self.fetch_file,
                        entity_id=entity_id,
                        entity_type=entity_type,
                        asset_id=asset or asset_id,
                        output_path=output_path / path,
                        asset_path=path,
                        project_context=context,
                        strategy=strategy,
                    )
                    for path in contents.files
                ]
                result = concurrent.futures.wait(futures)
                paths = [res.result() for res in result.done]

        return paths

    def download_directory(
        self,
        *,
        entity_id: ID,
        entity_type: type[Identifiable],
        asset_id: ID | Asset,
        output_path: os.PathLike,
        project_context: ProjectContext | None = None,
        ignore_directory_name: bool = False,
        max_concurrent: int = 1,
    ) -> list[Path]:
        """Download a directory asset to local disk.

        Args:
            entity_id: Resource id of the entity owning the directory.
            entity_type: Entity type.
            asset_id: Directory asset id, or an `Asset` object.
            output_path: Local output base path to write files to.
            project_context: Optional project context.
            ignore_directory_name: If `True`, do not create an extra nested
                folder for the directory name.
            max_concurrent: Maximum number of concurrent downloads.

        Returns:
            List of output file paths that were created.
        """
        return self.fetch_directory(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=asset_id,
            output_path=Path(output_path),
            project_context=project_context,
            ignore_directory_name=ignore_directory_name,
            max_concurrent=max_concurrent,
            strategy=FetchFileStrategy.download_only,
        )

    @validate_call
    def fetch_content(
        self,
        *,
        entity_id: ID,
        entity_type: type[Identifiable],
        asset_or_id: ID | Asset,
        asset_path: Path | None = None,
        project_context: ProjectContext | None = None,
        strategy: FetchContentStrategy = FetchContentStrategy.local_or_download,
    ) -> bytes:
        """Retrieve the binary content of an asset associated with an entity.

        Args:
            entity_id: Identifier of the entity that owns the asset.
            entity_type: The entity class/type implementing ``Identifiable``.
            asset_or_id: Identifier of the asset to retrieve.
            asset_path: For asset directories, the path within the directory for the file.
            project_context: Optional project context
            strategy: Strategy controlling how the asset file content is materialized
                (for example copying from a local store or downloading from the
                remote service).

        Returns:
            The asset content as raw bytes.
        """
        context = self._optional_user_context(override_context=project_context)
        return core.fetch_asset_content(
            api_url=self.api_url,
            entity_id=entity_id,
            entity_type=entity_type,
            asset_or_id=asset_or_id,
            asset_path=asset_path,
            project_context=context,
            http_client=self._http_client,
            token=self._token_manager.get_token(),
            local_store=self._local_store,
            strategy=strategy,
        )

    def download_content(
        self,
        *,
        entity_id: ID,
        entity_type: type[Identifiable],
        asset_id: ID,
        asset_path: StrOrPath | None = None,
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
        return self.fetch_content(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_or_id=asset_id,
            asset_path=Path(asset_path) if asset_path else None,
            project_context=project_context,
            strategy=FetchContentStrategy.download_only,
        )

    @validate_call
    def fetch_file(
        self,
        *,
        entity_id: ID,
        entity_type: type[Identifiable],
        asset_id: ID | Asset,
        output_path: Path,
        asset_path: Path | None = None,
        project_context: ProjectContext | None = None,
        strategy: FetchFileStrategy = FetchFileStrategy.link_or_download,
    ) -> Path:
        """Fetch a file asset to a local output path.

        Args:
            entity_id: Resource id of the entity owning the asset.
            entity_type: Entity type.
            asset_id: File asset id, or an `Asset` object.
            output_path: Local output path (file or directory) to write to.
            asset_path: For directory assets, path within the directory to the file.
            project_context: Optional project context.
            strategy: Strategy controlling how the asset file is materialized.

        Returns:
            The path of the created local file.
        """
        context = self._optional_user_context(override_context=project_context)
        return core.fetch_asset_file(
            api_url=self.api_url,
            entity_id=entity_id,
            entity_type=entity_type,
            asset_or_id=asset_id,
            project_context=context,
            asset_path=asset_path,
            output_path=output_path,
            http_client=self._http_client,
            token=self._token_manager.get_token(),
            local_store=self._local_store,
            strategy=strategy,
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
        return self.fetch_file(
            entity_id=entity_id,
            entity_type=entity_type,
            asset_id=asset_id,
            output_path=Path(output_path),
            project_context=project_context,
            asset_path=Path(asset_path) if asset_path else None,
            strategy=FetchFileStrategy.download_only,
        )

    @staticmethod
    def select_assets(entity: Entity, selection: dict) -> IteratorResult:
        """Select assets from an entity based on a selection dict.

        Args:
            entity: Entity whose assets should be filtered.
            selection: Selection/filter criteria.

        Returns:
            An iterator over matching assets.
        """
        return IteratorResult(filter_assets(entity.assets, selection))

    @validate_call
    def fetch_assets(
        self,
        entity_or_id: Entity | tuple[ID, type[Entity]],
        *,
        selection: dict[str, Any] | None = None,
        output_path: Path,
        project_context: ProjectContext | None = None,
        strategy: FetchFileStrategy = FetchFileStrategy.link_or_download,
    ):
        """Fetch assets belonging to an entity.

        Args:
            entity_or_id: Either an `Entity` object or a tuple of
                (`entity_id`, `entity_type`).
            selection: Optional selection/filter dict.
            output_path: Local output directory base path.
            project_context: Optional project context.
            strategy: Strategy controlling how each file is materialized.

        Returns:
            An iterator yielding `DownloadedAssetFile` objects.
        """

        def _fetch_entity_asset(asset):
            if asset.is_directory:
                raise NotImplementedError("Downloading asset directories is not supported yet.")
            else:
                path = self.fetch_file(
                    entity_id=entity.id,
                    entity_type=type(entity),
                    asset_id=asset.id,
                    output_path=output_path,
                    project_context=context,
                    strategy=strategy,
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

        if not entity.assets:
            raise EntitySDKError(f"Entity {entity.id} ({entity.name}) has no assets.")

        assets = filter_assets(entity.assets, selection) if selection else entity.assets

        if not all(asset.status == AssetStatus.created for asset in assets):
            raise EntitySDKError(
                f"Entity {entity.id} has assets that are uploading and cannot be downloaded."
            )
        return IteratorResult(map(_fetch_entity_asset, assets))

    def download_assets(
        self,
        entity_or_id: Entity | tuple[ID, type[Entity]],
        *,
        selection: dict[str, Any] | None = None,
        output_path: Path,
        project_context: ProjectContext | None = None,
    ) -> IteratorResult:
        """Download assets belonging to an entity.

        Args:
            entity_or_id: Either an `Entity` object or a tuple of (`entity_id`, `entity_type`).
            selection: Optional selection/filter dict.
            output_path: Local output directory base path.
            project_context: Optional project context.

        Returns:
            An iterator yielding `DownloadedAssetFile` objects.
        """
        return self.fetch_assets(
            entity_or_id=entity_or_id,
            selection=selection,
            output_path=output_path,
            project_context=project_context,
            strategy=FetchFileStrategy.download_only,
        )

    def delete_asset(
        self,
        *,
        entity_id: ID,
        entity_type: type[Identifiable],
        asset_id: ID,
        project_context: ProjectContext | None = None,
        admin: bool = False,
    ) -> Asset:
        """Delete an entity's asset.

        Args:
            entity_id: Resource id of the entity owning the asset.
            entity_type: Entity type.
            asset_id: Asset id to delete.
            project_context: Optional project context.
            admin: Whether to use the admin endpoint or not.

        Returns:
            The deleted Asset (as returned by the backend).
        """
        url = route.get_assets_endpoint(
            api_url=self.api_url,
            entity_type=entity_type,
            entity_id=entity_id,
            asset_id=asset_id,
            admin=admin,
        )
        context = (
            self._required_user_context(override_context=project_context) if not admin else None
        )
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
        entity_type: type[Entity],
        asset_id: ID,
        file_path: os.PathLike,
        file_content_type: ContentType,
        file_name: str | None = None,
        file_metadata: dict | None = None,
        project_context: ProjectContext | None = None,
    ) -> Asset:
        """Update an entity's asset file.

        Note: This operation is not atomic. Deletion can succeed and upload can fail.

        Args:
            entity_id: Resource id of the entity owning the asset.
            entity_type: Entity type.
            asset_id: Asset id to update.
            file_path: Path to the local file to upload.
            file_content_type: MIME content type for the uploaded file.
            file_name: Optional override for the uploaded filename.
            file_metadata: Optional extra metadata to attach to the asset.
            project_context: Optional project context.

        Returns:
            The updated Asset (as created by re-uploading).
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
        """Register a file or directory already existing.

        Args:
            entity_id: Resource id of the entity owning the asset.
            entity_type: Entity type.
            name: Asset name/path relative to the entity.
            storage_path: Full storage path (backend-specific).
            storage_type: Backend storage type.
            is_directory: Whether the asset represents a directory.
            content_type: MIME content type.
            asset_label: Label for the asset.
            project_context: Optional project context.

        Returns:
            The registered Asset.
        """
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
