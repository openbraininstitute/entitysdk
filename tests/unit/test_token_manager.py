import os
from unittest.mock import patch

import pytest

from entitysdk import token_manager as test_module
from entitysdk.exception import EntitySDKError


@patch.dict(os.environ, {"TOKEN": "Foo"}, clear=True)
def test_token_from_env():
    token_manager = test_module.TokenFromEnv(env_var_name="TOKEN")
    assert token_manager.get_token() == "Foo"


def test_token_from_env__raises():
    token_manager = test_module.TokenFromEnv(env_var_name="TOKEN")

    with pytest.raises(EntitySDKError, match="Environment variable 'TOKEN' not found."):
        token_manager.get_token()


def test_TokenFromValue():
    token_manager = test_module.TokenFromValue(value="foo")
    assert token_manager.get_token() == "foo"


def test_TokenFromFunction():
    token_manager = test_module.TokenFromFunction(function=lambda: "foo")
    assert token_manager.get_token() == "foo"
