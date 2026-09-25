"""Tests for ValidationResult registration."""

import uuid
from unittest.mock import MagicMock

import pytest

from entitysdk.models import ValidationResult
from entitysdk.registration.validation_result import (
    _detect_validation_name,
    register_validation_result_figure,
)
from entitysdk.types import ContentType

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
        ("emodel=cADpyr__seed=1__parameters_distribution", "parameters_distribution"),
        ("emodel=cADpyr__seed=1__thumbnail", None),
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
    ("figure_stem", "expected_upload_file_name"),
    [
        ("emodel=cADpyr__seed=1__traces", "traces"),
        ("emodel=cADpyr__seed=1__thumbnail", None),
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

    register_validation_result_figure(
        client=client,
        authorized_public=True,
        figure_file=figure_file,
        passed=True,
        validated_entity_id=uuid.uuid4(),
    )

    assert captured_file_name["file_name"] == expected_upload_file_name
