from pathlib import Path
from unittest import mock

import pytest

from entitysdk.staging import circuit as circuit_mod
from entitysdk.types import FetchFileStrategy


@pytest.fixture
def fake_client(tmp_path):
    client = mock.Mock()
    client.fetch_directory.return_value = [tmp_path / "circuit_config.json"]
    return client


def _stage(client, tmp_path, **kwargs):
    with (
        mock.patch.object(circuit_mod, "ensure_has_id"),
        mock.patch.object(circuit_mod, "ensure_has_assets"),
    ):
        return circuit_mod.stage_circuit(
            client, model=mock.Mock(id="circuit-id"), output_dir=tmp_path, **kwargs
        )


def test_stage_circuit_returns_the_config_path(fake_client, tmp_path):
    assert _stage(fake_client, tmp_path) == Path(tmp_path) / "circuit_config.json"


def test_stage_circuit_links_or_downloads_by_default(fake_client, tmp_path):
    _stage(fake_client, tmp_path)

    strategy = fake_client.fetch_directory.call_args.kwargs["strategy"]
    assert strategy == FetchFileStrategy.link_or_download


@pytest.mark.parametrize(
    "strategy",
    [FetchFileStrategy.copy_or_download, FetchFileStrategy.download_only],
)
def test_stage_circuit_forwards_the_fetch_strategy(fake_client, tmp_path, strategy):
    _stage(fake_client, tmp_path, strategy=strategy)

    assert fake_client.fetch_directory.call_args.kwargs["strategy"] == strategy
