"""Tests for ValidationResult registration."""

import uuid

import pytest

from entitysdk.models import ValidationResult
from entitysdk.registration.validation_result import register_validation_result_figure
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
