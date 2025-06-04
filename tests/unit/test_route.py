import pytest

from entitysdk import route as test_module
from entitysdk.exception import RouteNotFoundError
from entitysdk.models.entity import Entity


def test_get_route_name():
    res = test_module.get_route_name(Entity)
    assert res == "entity"


def test_get_route_name__raises():
    with pytest.raises(RouteNotFoundError):
        test_module.get_route_name(int)


def test_get_entities_endpoint(api_url):
    res = test_module.get_entities_endpoint(api_url=api_url, entity_type=Entity)
    assert res == f"{api_url}/entity"


def test_get_entities_endpoint__with_entity_id(api_url):
    res = test_module.get_entities_endpoint(api_url=api_url, entity_type=Entity, entity_id="1")
    assert res == f"{api_url}/entity/1"


def test_get_assets_endpoint(api_url):
    res = test_module.get_assets_endpoint(api_url=api_url, entity_type=Entity, entity_id="1")
    assert res == f"{api_url}/entity/1/assets"

    res = test_module.get_assets_endpoint(
        api_url=api_url, entity_type=Entity, entity_id="1", asset_id="2"
    )
    assert res == f"{api_url}/entity/1/assets/2"
