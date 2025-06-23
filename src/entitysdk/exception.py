"""Exception classes."""


class EntitySDKError(Exception):
    """Base exception class for EntitySDK."""


class RouteNotFoundError(EntitySDKError):
    """Raised when a route is not found."""


class IteratorResultError(EntitySDKError):
    """Raised when the result of an iterator is not as expected."""


class DependencyError(EntitySDKError):
    """Raised when a dependency check fails."""


class StagingError(EntitySDKError):
    """Raised when a staging operation has failed."""
