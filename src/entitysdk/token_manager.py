"""Token manager module."""

import os
from typing import Protocol

from entitysdk.exception import EntitySDKError


class TokenManager(Protocol):
    """Protocol for token managers."""

    def get_token(self) -> str:
        """Get the token."""


class TokenFromEnv:
    """Token manager that gets the token from an environment variable."""

    def __init__(self, env_var_name: str) -> None:
        """Initialize token manager with an environment variable name."""
        self._env_var_name = env_var_name

    def get_token(self) -> str:
        """Get the token from the environment variable."""
        try:
            return os.environ[self._env_var_name]
        except KeyError:
            raise EntitySDKError(
                f"Environment variable '{self._env_var_name}' not found."
            ) from None
