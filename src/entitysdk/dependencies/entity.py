"""Entity dependencies."""

from entitysdk.exception import DependencyError
from entitysdk.models.entity import Entity


def ensure_has_id(model: Entity) -> Entity:
    """Ensure entity has id."""
    if model.id is None:
        raise DependencyError(f"Model has no id: {repr(model)}")
    return model


def ensure_has_assets(model: Entity) -> Entity:
    """Ensure entity has assets."""
    if not model.assets:
        raise DependencyError(f"Model has no assets: {repr(model)}")
    return model
