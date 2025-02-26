import pytest

from entitysdk import route as test_module
from entitysdk.core import Entity
from entitysdk.exception import RouteNotFoundError


def test_get_route_name():
    res = test_module.get_route_name(Entity)
    assert res == "entity"


def test_get_route_name__raises():
    with pytest.raises(RouteNotFoundError):
        test_module.get_route_name(int)


def test_get_api_endpoint():
    res = test_module.get_api_endpoint(api_url="http://localhost:8000", entity_type=Entity)
    assert res == "http://localhost:8000/entity"


def test_get_api_endpoint__with_entity_id():
    res = test_module.get_api_endpoint(
        api_url="http://localhost:8000", entity_type=Entity, entity_id="1"
    )
    assert res == "http://localhost:8000/entity/1"
