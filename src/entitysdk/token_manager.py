"""Token manager module."""

import os
from collections.abc import Callable
from typing import Protocol

from entitysdk.exception import EntitySDKError
from entitysdk.types import Token


class TokenManager(Protocol):
    """Protocol for token managers."""

    def get_token(self) -> str:
        """Get the token."""


class TokenFromEnv:
    """Token manager that gets the token from an environment variable."""

    def __init__(self, env_var_name: str) -> None:
        """Initialize token manager with an environment variable name."""
        self._env_var_name = env_var_name

    def get_token(self) -> Token:
        """Get the token from the environment variable."""
        try:
            return os.environ[self._env_var_name]
        except KeyError:
            raise EntitySDKError(
                f"Environment variable '{self._env_var_name}' not found."
            ) from None


class TokenFromValue:
    """Token manager that uses a fixed value as a token."""

    def __init__(self, value: Token) -> None:
        """Initialize token manager with a fixed value."""
        self._value = value

    def get_token(self) -> Token:
        """Get the token from the stored variable."""
        return self._value


class TokenFromFunction:
    """Token manager that calls a function to get a token."""

    def __init__(self, function: Callable[[], Token]) -> None:
        """Initialize token manager with a function to call later."""
        self._function = function

    def get_token(self) -> Token:
        """Get the token by calling the function."""
        return self._function()
