import uuid
from unittest import mock

import pytest

from entitysdk import models, types
from entitysdk.models.derivation import Derivation
from entitysdk.models.entity import Entity
from entitysdk.staging import emodel_optimisation as staging


@pytest.fixture
def extraction_task_result_id():
    return uuid.uuid4()


@pytest.fixture
def extraction_task_result(extraction_task_result_id):
    return models.TaskResult(
        id=extraction_task_result_id,
        task_result_type=types.TaskResultType.efeature_extraction__result,
        assets=[
            models.Asset(
                id=uuid.uuid4(),
                content_type=types.ContentType.application_json,
                label=types.AssetLabel.efeature_extraction_features,
                path="features.json",
                full_path="/features.json",
                size=0,
                is_directory=False,
                storage_type=types.StorageType.aws_s3_internal,
            )
        ],
    )


@pytest.fixture
def morphology_id():
    return uuid.uuid4()


@pytest.fixture
def cell_morphology(morphology_id, mtype):
    return models.CellMorphology(
        id=morphology_id,
        name="cell-morphology",
        description="cell-morphology-description",
        cell_morphology_protocol=models.CellMorphologyProtocol(
            generation_type=types.CellMorphologyGenerationType.placeholder,
        ),
        brain_region=models.BrainRegion(
            name="my-region",
            annotation_value=1,
            acronym="region",
            hierarchy_id=uuid.uuid4(),
            color_hex_triplet="foo",
            parent_structure_id=None,
        ),
        subject=models.Subject(
            sex=types.Sex.male,
            species=models.Species(name="fake-species", taxonomy_id="foo"),
        ),
        mtypes=[mtype],
        assets=[
            models.Asset(
                id=uuid.uuid4(),
                content_type=types.ContentType.application_swc,
                label=types.AssetLabel.morphology,
                path="morph.swc",
                full_path="/morph.swc",
                size=0,
                is_directory=False,
                storage_type=types.StorageType.aws_s3_internal,
                status="created",
            )
        ],
    )


@pytest.fixture
def ion_channel_model():
    return models.IonChannelModel(
        id=uuid.uuid4(),
        name="icm",
        nmodl_suffix="icm",
        description="icm description",
        subject=models.Subject(
            sex=types.Sex.male,
            species={"name": "foo", "taxonomy_id": "bar"},
        ),
        brain_region={
            "name": "foo",
            "annotation_value": 997,
            "acronym": "bar",
            "parent_structure_id": None,
            "hierarchy_id": str(uuid.uuid4()),
            "color_hex_triplet": "#FFFFFF",
        },
        is_temperature_dependent=False,
        temperature_celsius=34,
        neuron_block=models.NeuronBlock(),
        assets=[
            models.Asset(
                id=uuid.uuid4(),
                content_type=types.ContentType.application_mod,
                label=types.AssetLabel.neuron_mechanisms,
                path="icm.mod",
                full_path="/icm.mod",
                size=0,
                is_directory=False,
                storage_type=types.StorageType.aws_s3_internal,
                status="created",
            )
        ],
    )


def test_stage_extraction_features_with_entity(tmp_path, extraction_task_result):
    client = mock.Mock()
    client.fetch_assets.return_value.one.return_value = mock.Mock()

    target = staging.stage_extraction_features(
        client,
        extraction_task_result=extraction_task_result,
        emodel_name="my_emodel",
        output_dir=tmp_path,
    )

    assert target == tmp_path / "config" / "features" / "my_emodel.json"
    client.fetch_assets.assert_called_once_with(
        entity_or_id=extraction_task_result,
        selection={"label": types.AssetLabel.efeature_extraction_features},
        output_path=target,
    )


def test_stage_extraction_features_with_entity_id(tmp_path, extraction_task_result_id):
    client = mock.Mock()
    client.fetch_assets.return_value.one.return_value = mock.Mock()

    target = staging.stage_extraction_features(
        client,
        extraction_task_result=(extraction_task_result_id, models.TaskResult),
        emodel_name="my_emodel",
        output_dir=tmp_path,
    )

    assert target.name == "my_emodel.json"
    client.fetch_assets.assert_called_once()
    assert client.fetch_assets.call_args.kwargs["entity_or_id"] == (
        extraction_task_result_id,
        models.TaskResult,
    )


def test_stage_morphology_with_entity(tmp_path, cell_morphology, morphology_id):
    client = mock.Mock()
    client.fetch_assets.return_value.one.return_value = mock.Mock()

    morph_filename = staging.stage_morphology(
        client,
        morphology=cell_morphology,
        output_dir=tmp_path,
    )

    assert morph_filename == f"{morphology_id}.swc"
    client.fetch_assets.assert_called_once_with(
        entity_or_id=cell_morphology,
        selection={
            "label": types.AssetLabel.morphology,
            "content_type": types.ContentType.application_swc,
        },
        output_path=tmp_path / "morphologies" / morph_filename,
    )


def test_stage_morphology_with_entity_id(tmp_path, morphology_id):
    client = mock.Mock()
    client.fetch_assets.return_value.one.return_value = mock.Mock()

    morph_filename = staging.stage_morphology(
        client,
        morphology=(morphology_id, models.CellMorphology),
        output_dir=tmp_path,
    )

    assert morph_filename == f"{morphology_id}.swc"
    assert client.fetch_assets.call_args.kwargs["entity_or_id"] == (
        morphology_id,
        models.CellMorphology,
    )


def test_stage_mechanisms_with_entities(tmp_path, ion_channel_model):
    client = mock.Mock()
    client.fetch_assets.return_value.one.return_value = mock.Mock()

    mech_dir = staging.stage_mechanisms(
        client,
        ion_channel_models=[ion_channel_model],
        output_dir=tmp_path,
    )

    assert mech_dir == tmp_path / "mechanisms"
    client.fetch_assets.assert_called_once_with(
        entity_or_id=ion_channel_model,
        selection={"content_type": types.ContentType.application_mod},
        output_path=mech_dir,
    )


def test_stage_mechanisms_with_entity_ids(tmp_path, ion_channel_model):
    client = mock.Mock()
    client.fetch_assets.return_value.one.return_value = mock.Mock()

    staging.stage_mechanisms(
        client,
        ion_channel_models=[(ion_channel_model.id, models.IonChannelModel)],
        output_dir=tmp_path,
    )

    assert client.fetch_assets.call_args.kwargs["entity_or_id"] == (
        ion_channel_model.id,
        models.IonChannelModel,
    )


def test_stage_traces_with_entity(extraction_task_result):
    client = mock.Mock()
    trace_id = uuid.uuid4()
    client.search_entity.return_value = [
        Derivation(
            id=uuid.uuid4(),
            used=Entity(id=trace_id, type=types.EntityType.electrical_cell_recording),
            generated=extraction_task_result,
        )
    ]

    trace_ids = staging.stage_traces(client, extraction_task_result)

    assert trace_ids == [str(trace_id)]
    client.search_entity.assert_called_once_with(
        entity_type=Derivation,
        query={"generated__id": extraction_task_result.id},
    )


def test_stage_traces_with_entity_id(extraction_task_result_id):
    client = mock.Mock()
    client.search_entity.return_value = []

    trace_ids = staging.stage_traces(
        client,
        (extraction_task_result_id, models.TaskResult),
    )

    assert trace_ids == []
    client.search_entity.assert_called_once_with(
        entity_type=Derivation,
        query={"generated__id": extraction_task_result_id},
    )


def test_derive_mtype_with_entity(cell_morphology, mtype):
    client = mock.Mock()

    mtype_label = staging.derive_mtype(client, cell_morphology)

    assert mtype_label == mtype.pref_label
    client.get_entity.assert_not_called()


def test_derive_mtype_with_entity_id(cell_morphology, morphology_id, mtype):
    client = mock.Mock()
    client.get_entity.return_value = cell_morphology

    mtype_label = staging.derive_mtype(
        client,
        (morphology_id, models.CellMorphology),
    )

    assert mtype_label == mtype.pref_label
    client.get_entity.assert_called_once_with(
        entity_id=morphology_id,
        entity_type=models.CellMorphology,
    )


def test_derive_mtype_returns_none_when_missing(cell_morphology):
    client = mock.Mock()
    morphology_without_mtypes = cell_morphology.model_copy(update={"mtypes": []})

    assert staging.derive_mtype(client, morphology_without_mtypes) is None
