"""Tests for emodel optimization TaskResult registration."""

import uuid
from unittest.mock import patch

from entitysdk.models import Asset, TaskResult
from entitysdk.registration.task_result.emodel_optimization import (
    register_emodel_optimization_result,
)
from entitysdk.types import AssetLabel, AssetStatus, ContentType, StorageType

from .conftest import mock_asset_json


def test_register_emodel_optimization_result(
    client,
    tmp_path,
    register_entity_responder,
    upload_file_responder,
):
    register_entity_responder(("task-result",))
    upload_file_responder()

    analysis_dir = tmp_path / "analysis"
    analysis_dir.mkdir()
    (analysis_dir / "plot-a.png").write_bytes(b"png")
    (analysis_dir / "plot-b.png").write_bytes(b"png")

    checkpoint_file = tmp_path / "checkpoint.h5"
    summary_file = tmp_path / "summary.json"
    checkpoint_file.write_bytes(b"hdf5")
    summary_file.write_text("{}")

    directory_asset = Asset.model_validate(
        mock_asset_json(
            asset_id=uuid.uuid4(),
            path="analysis-figures",
            is_directory=True,
            content_type=ContentType.application_vnd_directory,
            label=AssetLabel.emodel_analysis_figures,
            status=AssetStatus.created,
            storage_type=StorageType.aws_s3_internal,
        )
    )

    with patch.object(client, "upload_directory", return_value=directory_asset) as upload_directory:
        registered = register_emodel_optimization_result(
            client=client,
            name="optimization-result",
            description="optimization description",
            authorized_public=True,
            hdf5_checkpoint_file=checkpoint_file,
            analysis_figures_dir=analysis_dir,
            summary_file=summary_file,
        )

    assert isinstance(registered, TaskResult)
    assert registered.id is not None
    assert registered.name == "optimization-result"
    upload_directory.assert_called_once()
    upload_call = upload_directory.call_args.kwargs
    assert upload_call["entity_id"] == registered.id
    assert upload_call["label"] == AssetLabel.emodel_analysis_figures
    assert set(upload_call["paths"].values()) == {
        analysis_dir / "plot-a.png",
        analysis_dir / "plot-b.png",
    }
