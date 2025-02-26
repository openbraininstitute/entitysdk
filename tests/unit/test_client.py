from unittest.mock import Mock

import pytest

from entitysdk.client import Client
from entitysdk.core import Entity


def test_client_project_context__raises():
    client = Client(api_url="foo", project_context=None)

    with pytest.raises(ValueError, match="A project context must be specified."):
        client._project_context(override_context=None)


def test_client_search(client):
    client._http_client.request.return_value = Mock(json=lambda: {"data": []})

    res = client.search(
        entity_type=Entity,
        query={"name": "foo"},
        token="mock-token",
    )

    assert res == []


def test_client_update(client):
    client._http_client.request.return_value = Mock(json=lambda: {"id": 1})

    res = client.update(
        entity_id=1,
        entity_type=Entity,
        attrs_or_entity=Entity(id="1"),
        token="mock-token",
    )

    assert res.id == 1
