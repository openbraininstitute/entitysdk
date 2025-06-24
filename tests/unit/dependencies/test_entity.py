from unittest.mock import Mock

import pytest

from entitysdk.dependencies import entity as test_module
from entitysdk.exception import DependencyError


def test_ensure_has_no_id():
    mock = Mock(id=None)
    with pytest.raises(DependencyError, match="Model has no id"):
        test_module.ensure_has_id(mock)

    mock = Mock(id="foo")
    res = test_module.ensure_has_id(mock)
    assert res == mock


def test_ensure_has_assets():
    mock = Mock(assets=[])

    with pytest.raises(DependencyError, match="Model has no assets"):
        test_module.ensure_has_assets(mock)

    mock = Mock(assets=["foo"])
    res = test_module.ensure_has_assets(mock)
    assert res == mock
