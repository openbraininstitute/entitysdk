"""Shared helpers and fixtures for registration tests."""

import json
import re
import uuid
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urlparse

import httpx
import pytest

from entitysdk.types import AssetLabel, AssetStatus, ContentType, StorageType

EXTRACTED_DATA_DIR = Path(__file__).resolve().parents[1] / "models" / "data" / "extracted" / "one"

REGISTER_ENTITY_ROUTES = (
    "emodel",
    "memodel",
    "etype-classification",
    "mtype-classification",
    "derivation",
    "validation-result",
    "task-result",
)

REGISTER_ENTITY_BODY_FIELDS = (
    "entity_id",
    "etype_class_id",
    "mtype_class_id",
    "validated_entity_id",
    "name",
    "description",
    "passed",
    "authorized_public",
    "score",
    "seed",
    "iteration",
    "task_result_type",
    "lifecycle_status",
    "validation_status",
    "threshold_current",
    "holding_current",
)

ROUTE_TO_FIXTURE: dict[str, str | None] = dict.fromkeys(REGISTER_ENTITY_ROUTES)
ROUTE_TO_FIXTURE.update(
    {
        "emodel": "emodel",
        "memodel": "memodel",
        "etype-classification": "etype-classification",
        "mtype-classification": "mtype-classification",
        "derivation": "derivation",
        "validation-result": "validation-result",
        "task-result": "task-result",
    }
)


def load_extracted_json(route: str, filename: str | None = None) -> dict:
    """Load a JSON payload from extracted model trace data."""
    directory = EXTRACTED_DATA_DIR / route
    if filename is None:
        filename = sorted(directory.glob("content_*.json"))[0].name
    return json.loads((directory / filename).read_text())


def build_register_response(route: str, body: dict) -> dict:
    """Merge API fixture data with request fields needed for deserialization."""
    fixture_name = ROUTE_TO_FIXTURE.get(route)
    fixture = load_extracted_json(fixture_name) if fixture_name else {}
    response = {**fixture, "id": str(uuid.uuid4())}
    for field in REGISTER_ENTITY_BODY_FIELDS:
        if field in body:
            response[field] = body[field]
    return response


def mock_asset_json(*, asset_id: uuid.UUID | None = None, **overrides) -> dict:
    """Build a minimal asset API response payload."""
    payload = {
        "id": str(asset_id or uuid.uuid4()),
        "path": "path/to/asset",
        "full_path": "full/path/to/asset",
        "is_directory": False,
        "content_type": ContentType.text_plain,
        "size": 100,
        "status": AssetStatus.created,
        "meta": {},
        "sha256_digest": "sha256_digest",
        "label": AssetLabel.morphology,
        "storage_type": StorageType.aws_s3_internal,
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def register_entity_responder(httpx_mock, api_url) -> Callable[..., None]:
    """Register callbacks that assign ids to entity registration POST responses."""

    def _install(routes: tuple[str, ...] | None = None) -> None:
        del routes

        def callback(request: httpx.Request) -> httpx.Response:
            route = request.url.path.rsplit("/", maxsplit=1)[-1]
            body = json.loads(request.content.decode())
            response = build_register_response(route, body)
            return httpx.Response(200, json=response)

        parsed = urlparse(api_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        route_pattern = "|".join(re.escape(route) for route in REGISTER_ENTITY_ROUTES)
        httpx_mock.add_callback(
            callback,
            method="POST",
            url=re.compile(re.escape(base) + rf"/(?:{route_pattern})$"),
            is_reusable=True,
        )

    return _install


@pytest.fixture
def upload_file_responder(httpx_mock, api_url) -> Callable[[], None]:
    """Register a callback for single-file asset uploads."""

    def _install() -> None:
        def callback(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=mock_asset_json())

        parsed = urlparse(api_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        httpx_mock.add_callback(
            callback,
            method="POST",
            url=re.compile(re.escape(base) + r"/[\w-]+/[^/]+/assets$"),
            is_reusable=True,
        )

    return _install
