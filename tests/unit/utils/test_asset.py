import uuid

import pytest

from entitysdk.exception import EntitySDKError
from entitysdk.models import Asset
from entitysdk.utils import asset as test_module


@pytest.fixture
def assets():
    return [
        Asset(
            id=uuid.uuid4(),
            path="foo/asset1",
            full_path="/foo/asset1",
            is_directory=False,
            content_type="application/json",
            size=1,
            label="json",
        ),
        Asset(
            id=uuid.uuid4(),
            path="foo/asset2",
            full_path="/foo/asset2",
            is_directory=False,
            content_type="application/csv",
            size=1,
            label="csv",
        ),
        Asset(
            id=uuid.uuid4(),
            path="foo/asset3",
            full_path="/foo/asset3",
            is_directory=False,
            content_type="application/csv",
            size=1,
            label="csv",
        ),
    ]


def test_filter_assets__none(assets):
    res = test_module.filter_assets(assets, selection={"content_type": "application/swc"})
    assert res == []


def test_filter_assets__one(assets):
    res = test_module.filter_assets(assets, selection={"content_type": "application/json"})
    assert len(res) == 1
    assert res[0].path == "foo/asset1"


def test_filter_assets__multiple_matches(assets):
    res = test_module.filter_assets(assets, selection={"content_type": "application/csv"})
    assert len(res) == 2
    assert res[0].path == "foo/asset2"
    assert res[1].path == "foo/asset3"


def test_filter_assets__empty_assets():
    res = test_module.filter_assets([], selection={"content_type": "application/csv"})
    assert res == []


def test_filter_assets__multiple_selections(assets):
    res = test_module.filter_assets(
        assets, selection={"content_type": "application/csv", "size": 1, "path": "foo/asset2"}
    )
    assert len(res) == 1
    assert res[0].path == "foo/asset2"


def test_filter_assets__empty_selection(assets):
    res = test_module.filter_assets(assets, selection={})
    assert res == assets


def test_filter_assets__invalid_keys(assets):
    with pytest.raises(EntitySDKError, match="Selection keys are not matching asset metadata keys"):
        test_module.filter_assets(assets, selection={"foo": "bar"})

    with pytest.raises(EntitySDKError, match="Selection keys are not matching asset metadata keys"):
        test_module.filter_assets(
            assets, selection={"content_type": "application/json", "foo": "bar"}
        )
