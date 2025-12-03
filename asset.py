#!/bin/env python3

import logging
from rich import print
import uuid

import click
from obi_auth import get_token

from entitysdk import Client, ProjectContext, models

#logging.basicConfig(level=logging.DEBUG)

str_to_model = {name.lower(): getattr(models, name) for name in dir(models) if name[0].isupper()}


@click.group()
def cli():
    """Main CLI group."""


@cli.command
@click.option("--vlab")
@click.option("--project")
@click.option("--entity-type")
@click.option("--id")
def ls(vlab, project, entity_type, id):

    token = get_token(environment="staging")

    project_context = ProjectContext(
            project_id=uuid.UUID(project),
            virtual_lab_id=uuid.UUID(vlab)
        )

    client = Client(
        project_context=project_context,
        environment='staging',
        token_manager=token
        )

    entity_type = str_to_model[entity_type.lower()]

    ret = client.search_entity(entity_type=entity_type, query={"id": id}).all()
    assert len(ret) == 1
    ret = ret[0]

    print(f"{id} ({ret.name} / {ret.description} )- {len(ret.assets)} assets:")
    for a in ret.assets:
        print(f"\t{a.id}: [green]{a.label} /[/green] / {a.path} / {a.full_path} / {a.content_type} / {a.size}")


@cli.command
@click.option("--vlab")
@click.option("--project")
@click.option("--entity-type")
@click.option("--id")
@click.option("--asset-id")
def get(vlab, project, entity_type, id, asset_id):

    token = get_token(environment="staging")

    project_context = ProjectContext(
            project_id=uuid.UUID(project),
            virtual_lab_id=uuid.UUID(vlab)
        )

    client = Client(
        project_context=project_context,
        environment='staging',
        token_manager=token
        )

    entity_type = str_to_model[entity_type.lower()]

    client.download_file(entity_id=id, entity_type=entity_type, asset_id=uuid.UUID(asset_id), output_path="out.nrrd")

@cli.command
@click.option("--vlab")
@click.option("--project")
@click.option("--entity-type")
@click.option("--id")
@click.option('--delete-entity', is_flag=True, default=False)
def rm(vlab, project, entity_type, id, delete_entity):

    token = get_token(environment="staging")

    project_context = ProjectContext(
            project_id=uuid.UUID(project),
            virtual_lab_id=uuid.UUID(vlab)
        )

    client = Client(
        project_context=project_context,
        environment='staging',
        token_manager=token
        )

    entity_type = str_to_model[entity_type.lower()]

    ret = client.search_entity(entity_type=entity_type, query={"id": id}).one()

    for asset in ret.assets:
        client.delete_asset(
            entity_id=id,
            entity_type=entity_type,
            asset_id=asset.id,
            project_context=project_context,
            hard=True,
        )

    if delete_entity:
        client.delete_entity(ret.id, entity_type=entity_type)


if __name__ == "__main__":
    cli()
