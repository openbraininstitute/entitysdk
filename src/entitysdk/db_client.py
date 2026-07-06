"""Database client with optional dry-run mode."""

import logging
import uuid
from pathlib import Path
from typing import Any, TypeVar, cast

from entitysdk.client import Client
from entitysdk.common import parse_vlab_url
from entitysdk.compat import Self
from entitysdk.models.asset import Asset, LocalAssetMetadata
from entitysdk.models.core import Identifiable
from entitysdk.types import (
    ID,
    AssetLabel,
    AssetStatus,
    ContentType,
    StorageType,
)

L = logging.getLogger(__name__)

TIdentifiable = TypeVar("TIdentifiable", bound=Identifiable)


class DbClient(Client):
    """Client that can log mutating operations instead of executing them."""

    def __init__(self, *, dry_run: bool = False, **kwargs: Any) -> None:
        """Initialize client.

        Args:
            dry_run: If ``True``, register, upload, and update operations are logged
                instead of sent to the backend.
            **kwargs: Arguments forwarded to :class:`Client`.
        """
        super().__init__(**kwargs)
        self.dry_run = dry_run

    @classmethod
    def from_vlab_url(cls, vlab_url: str, **kwargs: Any) -> Self:
        """Initialize client from a platform url containing the virtual lab and project."""
        project_context, environment = parse_vlab_url(vlab_url)
        return cls(project_context=project_context, environment=environment, **kwargs)

    def _log_dry_run(self, operation: str, *args: Any, **kwargs: Any) -> None:
        L.info("[dry-run] %s: args=%s kwargs=%s", operation, args, kwargs)

    def _dry_run_asset(
        self,
        *,
        path: str,
        content_type: ContentType,
        label: AssetLabel,
        asset_id: ID | None = None,
        is_directory: bool = False,
        storage_type: StorageType = StorageType.aws_s3_internal,
    ) -> Asset:
        return Asset(
            id=asset_id or uuid.uuid4(),
            path=path,
            full_path=f"dry-run://{path}",
            storage_type=storage_type,
            is_directory=is_directory,
            content_type=content_type,
            size=0,
            status=AssetStatus.created,
            label=label,
        )

    def register_entity(self, entity: TIdentifiable, **kwargs: Any) -> TIdentifiable:
        """Register entity."""
        if not self.dry_run:
            return super().register_entity(entity, **kwargs)

        self._log_dry_run("register_entity", entity, **kwargs)
        if entity.id is None:
            return entity.model_copy(update={"id": uuid.uuid4()})
        return entity

    def update_entity(
        self,
        entity_id: ID,
        entity_type: type[TIdentifiable],
        attrs_or_entity: dict | Identifiable,
        **kwargs: Any,
    ) -> TIdentifiable:
        """Update an entity."""
        if not self.dry_run:
            return super().update_entity(entity_id, entity_type, attrs_or_entity, **kwargs)

        self._log_dry_run("update_entity", entity_id, entity_type, attrs_or_entity, **kwargs)
        if isinstance(attrs_or_entity, dict):
            return entity_type.model_validate({"id": entity_id, **attrs_or_entity})
        return cast(TIdentifiable, attrs_or_entity)

    def upload_file(self, **kwargs: Any) -> Asset:
        """Upload a file to an entity."""
        if not self.dry_run:
            return super().upload_file(**kwargs)

        file_path = Path(kwargs["file_path"])
        file_content_type = kwargs["file_content_type"]
        asset_label = kwargs["asset_label"]
        asset_metadata = LocalAssetMetadata(
            file_name=kwargs.get("file_name") or file_path.name,
            content_type=file_content_type,
            metadata=kwargs.get("file_metadata"),
            label=asset_label,
        )
        self._log_dry_run("upload_file", asset_metadata=asset_metadata, **kwargs)
        return self._dry_run_asset(
            path=asset_metadata.file_name,
            content_type=file_content_type,
            label=asset_label,
        )

    def upload_content(self, **kwargs: Any) -> Asset:
        """Upload file-like content to an entity."""
        if not self.dry_run:
            return super().upload_content(**kwargs)

        file_name = kwargs["file_name"]
        file_content_type = kwargs["file_content_type"]
        asset_label = kwargs["asset_label"]
        asset_metadata = LocalAssetMetadata(
            file_name=file_name,
            content_type=file_content_type,
            metadata=kwargs.get("file_metadata") or {},
            label=asset_label,
        )
        self._log_dry_run("upload_content", asset_metadata=asset_metadata, **kwargs)
        return self._dry_run_asset(
            path=file_name,
            content_type=file_content_type,
            label=asset_label,
        )

    def upload_directory(self, **kwargs: Any) -> Asset:
        """Attach a local directory to an entity."""
        if not self.dry_run:
            return super().upload_directory(**kwargs)

        name = kwargs["name"]
        label = kwargs["label"]
        paths = {Path(k): Path(v) for k, v in kwargs["paths"].items()}
        self._log_dry_run("upload_directory", paths=paths, **kwargs)
        return self._dry_run_asset(
            path=name,
            content_type=ContentType.application_octet_stream,
            label=label,
            is_directory=True,
        )

    def update_asset_file(self, **kwargs: Any) -> Asset:
        """Update an entity's asset file."""
        if not self.dry_run:
            return super().update_asset_file(**kwargs)

        file_path = Path(kwargs["file_path"])
        file_content_type = kwargs["file_content_type"]
        self._log_dry_run("update_asset_file", file_path=file_path, **kwargs)
        return self._dry_run_asset(
            path=kwargs.get("file_name") or file_path.name,
            content_type=file_content_type,
            label=AssetLabel.morphology,
        )

    def register_asset(self, **kwargs: Any) -> Asset:
        """Register a file or directory already existing."""
        if not self.dry_run:
            return super().register_asset(**kwargs)

        self._log_dry_run("register_asset", **kwargs)
        return self._dry_run_asset(
            path=kwargs["name"],
            content_type=kwargs["content_type"],
            label=kwargs["asset_label"],
            is_directory=kwargs["is_directory"],
            storage_type=kwargs["storage_type"],
        )
