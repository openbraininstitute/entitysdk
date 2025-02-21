"""Entity SDK client."""

import httpx

from entitysdk.common import ProjectContext
from entitysdk.core import Entity
from entitysdk.serdes import deserialize_entity, serialize_entity
from entitysdk.util import make_db_api_request


class Client:
    """Client for entitysdk."""

    def __init__(self, api_url: str, project_context: ProjectContext | None = None) -> None:
        """Initialize client."""
        self.api_url = api_url
        self.project_context = project_context
        self._http_client = httpx.Client()

    def _url(self, route: str, resource_id: str | None = None):
        """Get url for route and resource id."""
        route = f"{self.api_url}/{route}"
        return f"{route}/{resource_id}" if resource_id else route

    def _project_context(self, override_context: ProjectContext | None) -> ProjectContext:
        context = override_context or self.project_context

        if not context:
            raise ValueError("A project context must be specified.")

        return context

    def get(
        self,
        resource_id: str,
        *,
        entity_type: type[Entity],
        project_context: ProjectContext | None = None,
        token: str,
    ) -> Entity:
        """Get entity from resource id."""
        route = entity_type.route
        if route is None:
            raise TypeError(
                f"Entity type {entity_type} does not have a corresponding route in entitycore."
            )
        url = self._url(route=str(route), resource_id=resource_id)
        project_context = self._project_context(override_context=project_context)
        return get_entity(
            url=url,
            entity_type=entity_type,
            project_context=project_context,
            token=token,
            http_client=self._http_client,
        )

    def register(
        self, entity: Entity, *, project_context: ProjectContext | None = None, token: str
    ) -> Entity:
        """Register entity."""
        route = entity.route
        if route is None:
            raise TypeError(
                f"Entity type {type(entity)} does not have a corresponding route in entitycore."
            )
        url = self._url(route=str(entity.route), resource_id=None)
        project_context = self._project_context(override_context=project_context)
        return register_entity(
            url=url,
            entity=entity,
            project_context=project_context,
            token=token,
            http_client=self._http_client,
        )


def get_entity(
    url: str,
    entity_type: type[Entity],
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> Entity:
    """Instantiate entity with model ``entity_type`` from resource id."""
    response = make_db_api_request(
        url=url,
        method="GET",
        json=None,
        project_context=project_context,
        token=token,
        http_client=http_client,
    )

    return deserialize_entity(response.json(), entity_type)


def register_entity(
    url: str,
    *,
    entity: Entity,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> Entity:
    """Register entity."""
    json_data = serialize_entity(entity)

    response = make_db_api_request(
        url=url,
        method="POST",
        json=json_data,
        project_context=project_context,
        token=token,
        http_client=http_client,
    )

    return deserialize_entity(response.json(), type(entity))
