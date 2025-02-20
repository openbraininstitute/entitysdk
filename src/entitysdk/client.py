from dataclasses import dataclass

from entitysdk.common import ProjectContext
from entitysdk.core import Entity
from entitysdk.serdes import deserialize_entity, serialize_entity
from entitysdk.util import make_request


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
        model_cls: Entity,
        project_context: ProjectContext | None = None,
        token: str,
    ):
        """Get entity from resource id."""
        url = self._url(route=model_cls.route, resource_id=resource_id)
        project_context = self._project_context(override_context=project_context)
        return get_entity(
            url=url,
            model_cls=model_cls,
            project_context=project_context,
            token=token,
        )

    def register(
        self, entity: Entity, *, project_context: ProjectContext | None = None, token: str
    ):
        """Register entity."""
        assert entity.id is None
        url = self._url(route=entity.route, resource_id=None)
        project_context = self._project_context(override_context=project_context)
        return register_entity(
            url=url,
            entity=entity,
            project_context=project_context,
            token=token,
        )


def get_entity(url: str, model_cls: Entity, project_context: ProjectContext, token: str):
    """Instantiate entity with model ``model_cls`` from resource id."""
    response = make_request(
        method="GET",
        url=url,
        headers={
            "project-id": project_context.project_id,
            "virtual-lab-id": project_context.virtual_lab_id,
            "Authorization": f"Bearer {token}",
        },
    )

    return deserialize_entity(response.json(), model_cls)


def register_entity(url: str, *, entity: Entity, project_context: ProjectContext, token: str):
    """Register entity."""
    json_data = serialize_entity(entity)

    response = make_request(
        method="POST",
        url=url,
        headers={
            "project-id": project_context.project_id,
            "virtual-lab-id": project_context.virtual_lab_id,
            "Authorization": f"Bearer {token}",
        },
        json=json_data,
    )

    return deserialize_entity(response.json(), entity.__class__)
