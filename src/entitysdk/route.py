"""Route handling."""

from urllib.parse import urljoin

from entitysdk.exception import RouteNotFoundError
from entitysdk.models.core import Identifiable

# Mapping of entity type to api route name.
_ROUTES = {
    "Activity": "activity",
    "BrainLocation": "brain_location",
    "BrainRegion": "brain_region",
    "Entity": "entity",
    "License": "license",
    "Organization": "organization",
    "Person": "person",
    "ReconstructionMorphology": "reconstruction_morphology",
    "Species": "species",
    "Strain": "strain",
    "Taxonomy": "taxonomy",
}


def get_route_name(entity_type: type[Identifiable]) -> str:
    """Get the base route for an entity type."""
    class_name = entity_type.__name__

    try:
        return _ROUTES[class_name]
    except KeyError as e:
        raise RouteNotFoundError(
            f"Route for entity type {class_name} not found in routes. "
            f"Existing routes: {sorted(_ROUTES.keys())}"
        ) from e


def get_api_endpoint(
    api_url: str, entity_type: type[Identifiable], entity_id: str | None = None
) -> str:
    """Get the API endpoint for an entity type."""
    route_name = get_route_name(entity_type)
    endpoint = route_name if entity_id is None else f"{route_name}/{entity_id}"
    return urljoin(api_url, endpoint)
