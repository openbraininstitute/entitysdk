"""Identifiable SDK client."""

import httpx

from entitysdk.common import ProjectContext
from entitysdk.core import Identifiable
from entitysdk.serdes import deserialize_entity, serialize_dict, serialize_entity
from entitysdk.util import make_db_api_request


class Client:
    """Client for entitysdk."""

    def __init__(self, api_url: str, project_context: ProjectContext | None = None) -> None:
        """Initialize client."""
        self.api_url = api_url
        self.project_context = project_context
        self._http_client = httpx.Client()

    def _url(self, route: str, entity_id: str | None = None):
        """Get url for route and resource id."""
        route = f"{self.api_url}/{route}/"
        return f"{route}{entity_id}" if entity_id else route

    def _project_context(self, override_context: ProjectContext | None) -> ProjectContext:
        context = override_context or self.project_context

        if context is None:
            raise ValueError("A project context must be specified.")

        return context

    def get(
        self,
        entity_id: str,
        *,
        entity_type: type[Identifiable],
        project_context: ProjectContext | None = None,
        token: str,
    ) -> Identifiable:
        """Get entity from resource id.

        Args:
            entity_id: Resource id of the entity.
            entity_type: Type of the entity.
            project_context: Optional project context.
            token: Authorization access token.

        Returns:
            entity_type instantatied by deserializing the response.
        """
        url = self._url(route=str(entity_type.__route__), entity_id=entity_id)
        project_context = self._project_context(override_context=project_context)
        return get_entity(
            url=url,
            entity_type=entity_type,
            project_context=project_context,
            token=token,
            http_client=self._http_client,
        )

    def search(
        self,
        *,
        entity_type: type[Identifiable],
        query: dict,
        project_context: ProjectContext | None = None,
        token: str,
    ) -> list[Identifiable]:
        """Search for entities.

        Args:
            entity_type: Type of the entity.
            query: Query parameters.
            project_context: Optional project context.
            token: Authorization access token.
        """
        url = self._url(route=str(entity_type.__route__), entity_id=None)
        return search_entities(
            url=url,
            entity_type=entity_type,
            query=query,
            project_context=self._project_context(override_context=project_context),
            token=token,
            http_client=self._http_client,
        )

    def register(
        self, entity: Identifiable, *, project_context: ProjectContext | None = None, token: str
    ) -> Identifiable:
        """Register entity.

        Args:
            entity: Identifiable to register.
            project_context: Optional project context.
            token: Authorization access token.

        Returns:
            Registered entity with id.
        """
        url = self._url(route=str(entity.__route__), entity_id=None)
        project_context = self._project_context(override_context=project_context)
        return register_entity(
            url=url,
            entity=entity,
            project_context=project_context,
            token=token,
            http_client=self._http_client,
        )

    def update(
        self,
        entity_id: str,
        entity_type: type[Identifiable],
        attrs_or_entity: dict | Identifiable,
        *,
        project_context: ProjectContext | None = None,
        token: str,
    ) -> Identifiable:
        """Update an entity.

        Args:
            entity_id: Id of the entity to update.
            entity_type: Type of the entity.
            attrs_or_entity: Attributes or entity to update.
            project_context: Optional project context.
            token: Authorization access token.
        """
        url = self._url(route=str(entity_type.__route__), entity_id=entity_id)
        project_context = self._project_context(override_context=project_context)
        return update_entity(
            url=url,
            entity_type=entity_type,
            attrs_or_entity=attrs_or_entity,
            project_context=project_context,
            token=token,
            http_client=self._http_client,
        )


def search_entities(
    url: str,
    *,
    entity_type: type[Identifiable],
    query: dict,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> list[Identifiable]:
    """Search for entities.

    Args:
        url: URL of the resource.
        entity_type: Type of the entity.
        query: Query parameters
        project_context: Project context.
        token: Authorization access token.
        http_client: HTTP client.

    Returns:
        List of entities.
    """
    response = make_db_api_request(
        url=url,
        method="GET",
        parameters=query,
        project_context=project_context,
        token=token,
        http_client=http_client,
    )
    json_data_list = response.json()["data"]
    return [deserialize_entity(json_data, entity_type) for json_data in json_data_list]


def get_entity(
    url: str,
    entity_type: type[Identifiable],
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> Identifiable:
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
    entity: Identifiable,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
) -> Identifiable:
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


def update_entity(
    url: str,
    *,
    entity_type: type[Identifiable],
    attrs_or_entity: dict | Identifiable,
    project_context: ProjectContext,
    token: str,
    http_client: httpx.Client | None = None,
):
    """Update entity."""
    if isinstance(attrs_or_entity, dict):
        json_data = serialize_dict(attrs_or_entity)
    else:
        json_data = serialize_entity(attrs_or_entity)

    response = make_db_api_request(
        url=url,
        method="PATCH",
        json=json_data,
        project_context=project_context,
        token=token,
        http_client=http_client,
    )

    json_data = response.json()

    return deserialize_entity(json_data, entity_type)
