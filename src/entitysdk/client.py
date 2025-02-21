"""Entity SDK client."""

from dataclasses import dataclass

from entitysdk.common import ProjectContext
from entitysdk.core import Entity
from entitysdk.serdes import deserialize_entity, serialize_entity
from entitysdk.util import make_db_api_request


@dataclass
class Client:
    """Client for entitysdk."""

    api_url: str
    project_context: ProjectContext | None = None

    def _url(self, route: str, resource_id: str | None = None):
        """Get url for route and resource id."""
        route = f"{self.api_url}/{route}"
        return f"{route}/{resource_id}" if resource_id else route

    def _project_context(self, override_context: ProjectContext):
        context = override_context or self.project_context

        if not context:
            raise ValueError("A project context must be specified.")

        return context

    def get(
        self,
        resource_id: str,
        *,
        entity_type: Entity,
        project_context: ProjectContext | None = None,
        token: str,
    ) -> Entity:
        """Get entity from resource id."""
        url = self._url(route=entity_type.route, resource_id=resource_id)
        project_context = self._project_context(override_context=project_context)
        return get_entity(
            url=url,
            entity_type=entity_type,
            project_context=project_context,
            token=token,
        )

    def register(
        self, entity: Entity, *, project_context: ProjectContext | None = None, token: str
    ) -> Entity:
        """Register entity."""
        url = self._url(route=entity.route, resource_id=None)
        project_context = self._project_context(override_context=project_context)
        return register_entity(
            url=url,
            entity=entity,
            project_context=project_context,
            token=token,
        )


def get_entity(
    url: str, entity_type: type[Entity], project_context: ProjectContext, token: str
) -> Entity:
    """Instantiate entity with model ``entity_type`` from resource id."""
    response = make_db_api_request(
        url=url,
        method="GET",
        json=None,
        project_context=project_context,
        token=token,
    )

    return deserialize_entity(response.json(), entity_type)


def register_entity(
    url: str, *, entity: Entity, project_context: ProjectContext, token: str
) -> Entity:
    """Register entity."""
    json_data = serialize_entity(entity)

    response = make_db_api_request(
        url=url,
        method="POST",
        json=json_data,
        project_context=project_context,
        token=token,
    )

    return deserialize_entity(response.json(), type(entity))
