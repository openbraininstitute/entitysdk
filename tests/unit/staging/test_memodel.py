import json
from unittest import mock

import h5py
import pytest

from entitysdk.staging import memodel as memodel_mod


class FakeMType:
    pref_label = "L5_TTPC1"


class FakeCalibration:
    threshold_current = 0.234
    holding_current = -0.123


class FakeMEModel:
    def __init__(self, with_calibration=True):
        self.id = "fake_id"
        self.mtypes = [FakeMType()]
        self.calibration_result = FakeCalibration() if with_calibration else None


@pytest.fixture
def fake_memodel():
    return FakeMEModel()


@pytest.fixture
def fake_memodel_no_calib():
    return FakeMEModel(with_calibration=False)


@pytest.fixture
def fake_client():
    return mock.Mock()


def test_stage_sonata_from_memodel_success(tmp_path, fake_memodel, fake_client):
    config_path = tmp_path / "circuit_config.json"
    config_path.write_text("{}")

    with (
        mock.patch.object(memodel_mod, "download_memodel") as mock_dl,
        mock.patch.object(memodel_mod, "generate_sonata_files_from_memodel") as mock_gen,
    ):
        result = memodel_mod.stage_sonata_from_memodel(
            fake_client, fake_memodel, output_dir=tmp_path
        )
        assert result == config_path
        mock_dl.assert_called_once()
        mock_gen.assert_called_once()


def test_stage_sonata_from_memodel_no_calibration(tmp_path, fake_memodel_no_calib, fake_client):
    with mock.patch.object(memodel_mod, "download_memodel"):
        with pytest.raises(ValueError, match="has no calibration result"):
            memodel_mod.stage_sonata_from_memodel(
                fake_client, fake_memodel_no_calib, output_dir=tmp_path
            )


def test_stage_sonata_from_memodel_missing_config(tmp_path, fake_memodel, fake_client):
    with (
        mock.patch.object(memodel_mod, "download_memodel"),
        mock.patch.object(memodel_mod, "generate_sonata_files_from_memodel"),
    ):
        with pytest.raises(FileNotFoundError, match="Expected circuit config not found"):
            memodel_mod.stage_sonata_from_memodel(fake_client, fake_memodel, output_dir=tmp_path)


def test_generate_sonata_files_from_memodel_creates_structure(tmp_path):
    memodel_path = tmp_path / "memodel"
    hoc_dir = memodel_path / "hoc"
    morph_dir = memodel_path / "morphology"
    mech_dir = memodel_path / "mechanisms"

    hoc_dir.mkdir(parents=True)
    morph_dir.mkdir()
    mech_dir.mkdir()

    (hoc_dir / "cell.hoc").write_text("hoc content")
    (morph_dir / "cell.asc").write_text("morph content")
    (mech_dir / "mech.mod").write_text("mod content")

    output_path = tmp_path / "sonata"
    memodel_mod.generate_sonata_files_from_memodel(
        memodel_path=memodel_path,
        output_path=output_path,
        mtype="L5_TTPC1",
        threshold_current=0.2,
        holding_current=-0.1,
    )

    assert (output_path / "hocs" / "cell.hoc").exists()
    assert (output_path / "morphologies" / "cell.asc").exists()
    assert (output_path / "mechanisms" / "mech.mod").exists()
    assert (output_path / "network" / "nodes.h5").exists()
    assert (output_path / "circuit_config.json").exists()
    assert (output_path / "node_sets.json").exists()

    # Validate content inside nodes.h5
    with h5py.File(output_path / "network" / "nodes.h5", "r") as f:
        group = f["nodes"]["All"]["0"]
        assert group["mtype"][0].decode() == "L5_TTPC1"
        assert group["dynamics_params"]["holding_current"][0] == pytest.approx(-0.1)
        assert group["dynamics_params"]["threshold_current"][0] == pytest.approx(0.2)


def test_create_json_configs(tmp_path):
    hoc_file = tmp_path / "cell.hoc"
    morph_file = tmp_path / "cell.asc"
    hoc_file.write_text("hoc content")
    morph_file.write_text("morph content")
    network_dir = tmp_path / "network"

    memodel_mod.create_nodes_file(
        hoc_file=str(hoc_file),
        morph_file=str(morph_file),
        output_path=network_dir,
        mtype="L5_TTPC1",
        threshold_current=0.2,
        holding_current=-0.1,
    )

    assert (network_dir / "nodes.h5").exists()

    memodel_mod.create_circuit_config(output_path=tmp_path)
    with open(tmp_path / "circuit_config.json") as f:
        config = json.load(f)
        assert "networks" in config
        assert config["networks"]["nodes"][0]["nodes_file"] == "$NETWORK_DIR/nodes.h5"

    memodel_mod.create_node_sets_file(output_path=tmp_path)
    with open(tmp_path / "node_sets.json") as f:
        node_sets = json.load(f)
        assert node_sets["All"]["node_id"] == [0]


def test_missing_files_raise(tmp_path):
    memodel_path = tmp_path / "memodel"
    memodel_path.mkdir()
    (memodel_path / "morphology").mkdir()
    (memodel_path / "mechanisms").mkdir()
    with pytest.raises(FileNotFoundError, match="No .hoc files found"):
        memodel_mod.generate_sonata_files_from_memodel(
            memodel_path=memodel_path,
            output_path=tmp_path,
            mtype="Test",
            threshold_current=0.2,
            holding_current=-0.1,
        )
