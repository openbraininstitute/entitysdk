"""Tests for ValidationResult registration."""

import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from entitysdk.models import ValidationResult
from entitysdk.registration.validation_result import (
    _detect_validation_name,
    register_memodel_validation_results,
    register_validation_result,
    register_validation_result_figure,
)
from entitysdk.types import AssetLabel, ContentType

from .conftest import load_extracted_json


@pytest.mark.parametrize(
    ("suffix", "expected_content_type"),
    [
        (".pdf", ContentType.application_pdf),
        (".png", ContentType.image_png),
    ],
)
def test_register_validation_result_figure(
    client,
    tmp_path,
    register_entity_responder,
    upload_file_responder,
    suffix,
    expected_content_type,
):
    register_entity_responder(("validation-result",))
    upload_file_responder()

    figure_file = tmp_path / f"validation-figure{suffix}"
    figure_file.write_bytes(b"figure-content")
    validated_entity_id = uuid.uuid4()

    registered = register_validation_result_figure(
        client=client,
        authorized_public=True,
        figure_file=figure_file,
        passed=True,
        validated_entity_id=validated_entity_id,
    )

    assert isinstance(registered, ValidationResult)
    assert registered.id is not None
    assert registered.name == figure_file.stem
    assert registered.passed is True
    assert registered.validated_entity_id == validated_entity_id
    assert registered.authorized_public is True


def test_register_validation_result_figure_rejects_unknown_extension(tmp_path, client):
    figure_file = tmp_path / "figure.svg"
    figure_file.write_bytes(b"figure-content")

    with pytest.raises(KeyError):
        register_validation_result_figure(
            client=client,
            authorized_public=False,
            figure_file=figure_file,
            passed=False,
            validated_entity_id=uuid.uuid4(),
        )


def test_register_validation_result_figure_deserializes_response(
    client,
    tmp_path,
    register_entity_responder,
    upload_file_responder,
):
    register_entity_responder(("validation-result",))
    upload_file_responder()

    response_payload = load_extracted_json("validation-result")
    figure_file = tmp_path / "validation-figure.png"
    figure_file.write_bytes(b"figure-content")

    registered = register_validation_result_figure(
        client=client,
        authorized_public=response_payload["authorized_public"],
        figure_file=figure_file,
        passed=response_payload["passed"],
        validated_entity_id=uuid.UUID(response_payload["validated_entity_id"]),
    )

    assert registered.name == figure_file.stem
    assert registered.passed is response_payload["passed"]
    assert registered.authorized_public is response_payload["authorized_public"]


@pytest.mark.parametrize(
    ("filename_stem", "expected_name"),
    [
        ("emodel=cADpyr__iteration=1__seed=1__traces", "traces"),
        ("emodel=cADpyr__iteration=1__seed=1__scores", "scores"),
        (
            "emodel=cADpyr__iteration=1__seed=1__currentscape.APWaveform_280.soma",
            "currentscape",
        ),
        ("emodel=cADpyr__iteration=1__seed=1__currentscape", "currentscape"),
        (
            "emodel=IN_dAC__iteration=1b8100e__seed=11__evo_parameter_density",
            "evo_parameter_density",
        ),
        ("emodel=cADpyr__seed=1__optimisation", "optimisation"),
        ("emodel=cADpyr__seed=1__parameters_distribution", "parameter_distribution"),
        ("emodel=cADpyr__seed=1__thumbnail", "thumbnail"),
        ("emodel=cADpyr__seed=1__unknown_suffix", None),
        ("validation-figure", None),
    ],
)
def test_detect_validation_name(filename_stem, expected_name):
    assert _detect_validation_name(filename_stem) == expected_name


def test_detect_validation_name_empty_split_result():
    filename_stem = MagicMock(spec=str)
    filename_stem.split.return_value = []
    assert _detect_validation_name(filename_stem) is None


@pytest.mark.parametrize(
    ("figure_stem", "expected_upload_file_name", "expected_name"),
    [
        ("emodel=cADpyr__seed=1__traces", "traces.png", "emodel=cADpyr__seed=1__traces"),
        ("emodel=cADpyr__seed=1__thumbnail", "thumbnail.png", "thumbnail"),
        ("unrecognised-figure", None, "unrecognised-figure"),
    ],
)
def test_register_validation_result_figure_upload_file_name(
    client,
    tmp_path,
    register_entity_responder,
    upload_file_responder,
    monkeypatch,
    figure_stem,
    expected_upload_file_name,
    expected_name,
):
    register_entity_responder(("validation-result",))
    upload_file_responder()

    captured_file_name: dict[str, str | None] = {}
    original_upload_file = client.upload_file

    def upload_file_wrapper(**kwargs):
        captured_file_name["file_name"] = kwargs.get("file_name")
        return original_upload_file(**kwargs)

    monkeypatch.setattr(client, "upload_file", upload_file_wrapper)

    figure_file = tmp_path / f"{figure_stem}.png"
    figure_file.write_bytes(b"figure-content")

    registered = register_validation_result_figure(
        client=client,
        authorized_public=True,
        figure_file=figure_file,
        passed=True,
        validated_entity_id=uuid.uuid4(),
    )

    assert captured_file_name["file_name"] == expected_upload_file_name
    assert registered.name == expected_name


def test_register_validation_result_registers_and_uploads_assets(
    client,
    tmp_path,
    httpx_mock,
    register_entity_responder,
    upload_file_responder,
    search_responder,
    monkeypatch,
):
    search_responder("validation-result", [])
    register_entity_responder(("validation-result",))
    upload_file_responder()

    uploads = []
    original_upload_file = client.upload_file

    def upload_file_wrapper(**kwargs):
        uploads.append(kwargs)
        return original_upload_file(**kwargs)

    monkeypatch.setattr(client, "upload_file", upload_file_wrapper)

    figure_file = tmp_path / "hyperpolarization_validation.pdf"
    figure_file.write_bytes(b"figure-content")
    validated_entity_id = uuid.uuid4()

    registered = register_validation_result(
        client=client,
        name="Simulatable Neuron Hyperpolarization Validation",
        passed=True,
        validated_entity_id=validated_entity_id,
        authorized_public=True,
        figure_files=[figure_file],
        details_text="Validation passed.",
    )

    assert isinstance(registered, ValidationResult)
    assert registered.name == "Simulatable Neuron Hyperpolarization Validation"
    assert registered.passed is True
    assert registered.validated_entity_id == validated_entity_id

    assert len(uploads) == 2
    figure_upload, details_upload = uploads
    assert figure_upload["file_path"] == figure_file
    assert figure_upload["file_content_type"] == ContentType.application_pdf
    assert figure_upload.get("file_name") is None
    assert details_upload["file_path"].name == (
        "SimulatableNeuronHyperpolarizationValidation_validation_details.txt"
    )
    assert details_upload["file_content_type"] == ContentType.text_plain


def test_register_validation_result_skips_existing(
    client,
    httpx_mock,
    search_responder,
):
    search_responder("validation-result", [load_extracted_json("validation-result")])

    result = register_validation_result(
        client=client,
        name="Simulatable Neuron Spiking Validation",
        passed=True,
        validated_entity_id=uuid.uuid4(),
        authorized_public=False,
    )

    assert result is None


def test_register_validation_result_skips_missing_and_unknown_figures(
    client,
    tmp_path,
    httpx_mock,
    register_entity_responder,
    upload_file_responder,
    search_responder,
    monkeypatch,
):
    search_responder("validation-result", [])
    register_entity_responder(("validation-result",))
    upload_file_responder()

    uploads = []
    original_upload_file = client.upload_file

    def upload_file_wrapper(**kwargs):
        uploads.append(kwargs)
        return original_upload_file(**kwargs)

    monkeypatch.setattr(client, "upload_file", upload_file_wrapper)

    unsupported = tmp_path / "figure.svg"
    unsupported.write_bytes(b"figure-content")

    registered = register_validation_result(
        client=client,
        name="n",
        passed=False,
        validated_entity_id=uuid.uuid4(),
        authorized_public=False,
        figure_files=[tmp_path / "missing.pdf", unsupported],
    )

    assert registered is not None
    assert uploads == []


def test_register_memodel_validation_results_registers_each_test(
    client,
    tmp_path,
    httpx_mock,
    register_entity_responder,
    upload_file_responder,
    search_responder,
):
    search_responder("validation-result", [])
    register_entity_responder(("validation-result",))
    upload_file_responder()

    figure = tmp_path / "spiking_validation.pdf"
    figure.write_bytes(b"figure-content")
    thumbnail = tmp_path / "thumbnail.png"
    thumbnail.write_bytes(b"thumbnail-content")
    memodel_id = uuid.uuid4()

    validation_dict = {
        "memodel_properties": {"holding_current": 0.0, "rheobase": 0.1, "rin": 50.0},
        "spiking_test": {
            "name": "Simulatable Neuron Spiking Validation",
            "passed": True,
            "validation_details": "Validation passed.",
            "figures": [str(figure)],
        },
        "thumbnail_test": {
            "name": "thumbnail",
            "passed": True,
            "validation_details": "",
            "figures": [str(thumbnail)],
        },
        "malformed_entry": {"passed": True},
    }

    results = register_memodel_validation_results(
        client=client,
        memodel_id=memodel_id,
        validation_dict=validation_dict,
        authorized_public=False,
    )

    assert [r.name for r in results] == [
        "Simulatable Neuron Spiking Validation",
        "thumbnail",
    ]
    assert all(isinstance(r, ValidationResult) for r in results)
    assert all(r.validated_entity_id == memodel_id for r in results)


def test_register_memodel_validation_results_skips_existing(
    client,
    httpx_mock,
    search_responder,
):
    search_responder("validation-result", [load_extracted_json("validation-result")])

    results = register_memodel_validation_results(
        client=client,
        memodel_id=uuid.uuid4(),
        validation_dict={
            "spiking_test": {
                "name": "Simulatable Neuron Spiking Validation",
                "passed": True,
                "validation_details": "",
                "figures": [],
            }
        },
        authorized_public=False,
    )

    assert results == []


def _overwrite_client(matches, assets):
    """A client whose search finds ``matches`` and whose result has ``assets``."""
    client = MagicMock()
    client.search_entity.return_value.all.return_value = matches
    client.update_entity.side_effect = lambda *, entity_id, entity_type, attrs_or_entity: matches[
        0
    ].model_copy(update=attrs_or_entity)
    client.get_entity_assets.return_value.all.return_value = assets
    return client


def _existing_result(name="Simulatable Neuron Spiking Validation"):
    return ValidationResult(
        id=uuid.uuid4(), name=name, passed=False, validated_entity_id=uuid.uuid4()
    )


def test_register_validation_result_overwrite_updates_in_place(tmp_path):
    existing = _existing_result()
    figure_asset = SimpleNamespace(id=uuid.uuid4(), label=AssetLabel.validation_result_figure)
    details_asset = SimpleNamespace(id=uuid.uuid4(), label=AssetLabel.validation_result_details)
    other_asset = SimpleNamespace(id=uuid.uuid4(), label=AssetLabel.morphology)
    client = _overwrite_client([existing], [figure_asset, details_asset, other_asset])
    figure_file = tmp_path / "spiking_validation.pdf"
    figure_file.write_bytes(b"figure-content")

    result = register_validation_result(
        client=client,
        name=existing.name,
        passed=True,
        validated_entity_id=existing.validated_entity_id,
        authorized_public=False,
        figure_files=[figure_file],
        details_text="Validation passed.",
        overwrite=True,
    )

    assert result is not None
    assert result.id == existing.id
    assert result.passed is True
    client.register_entity.assert_not_called()
    client.update_entity.assert_called_once_with(
        entity_id=existing.id, entity_type=ValidationResult, attrs_or_entity={"passed": True}
    )
    deleted = [c.kwargs["asset_id"] for c in client.delete_asset.call_args_list]
    assert deleted == [figure_asset.id, details_asset.id]
    uploaded = [c.kwargs["asset_label"] for c in client.upload_file.call_args_list]
    assert uploaded == [
        AssetLabel.validation_result_figure,
        AssetLabel.validation_result_details,
    ]
    assert all(c.kwargs["entity_id"] == existing.id for c in client.upload_file.call_args_list)


def test_register_validation_result_overwrite_registers_when_missing():
    client = _overwrite_client([], [])
    client.register_entity.side_effect = lambda entity: entity.model_copy(
        update={"id": uuid.uuid4()}
    )

    result = register_validation_result(
        client=client,
        name="n",
        passed=True,
        validated_entity_id=uuid.uuid4(),
        authorized_public=False,
        overwrite=True,
    )

    assert result is not None
    client.register_entity.assert_called_once()
    client.update_entity.assert_not_called()


def test_register_validation_result_overwrite_rejects_ambiguous_match():
    client = _overwrite_client([_existing_result(), _existing_result()], [])

    with pytest.raises(ValueError, match="cannot choose the one to overwrite"):
        register_validation_result(
            client=client,
            name="Simulatable Neuron Spiking Validation",
            passed=True,
            validated_entity_id=uuid.uuid4(),
            authorized_public=False,
            overwrite=True,
        )
    client.update_entity.assert_not_called()


def test_register_memodel_validation_results_overwrite_returns_updated():
    existing = _existing_result()
    client = _overwrite_client([existing], [])

    results = register_memodel_validation_results(
        client=client,
        memodel_id=existing.validated_entity_id,
        validation_dict={
            "spiking_test": {
                "name": existing.name,
                "passed": True,
                "validation_details": "",
                "figures": [],
            }
        },
        authorized_public=False,
        overwrite=True,
    )

    assert [r.id for r in results] == [existing.id]
    assert results[0].passed is True
