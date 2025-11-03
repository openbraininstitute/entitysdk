"""Analysis notebook template model."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.base import BaseModel
from entitysdk.models.entity import Entity
from entitysdk.types import AnalysisScale, EntityType


class PythonDependency(BaseModel):
    """Python Dependency."""

    version: Annotated[str, Field(examples=[">=3.10,<3.12"], title="Version")]


class DockerDependency(BaseModel):
    """Docker Dependency."""

    image_repository: Annotated[
        str, Field(examples=["openbraininstitute/obi-notebook-image"], title="Image Repository")
    ]
    image_tag: Annotated[str | None, Field(examples=[">=2025.09.24-2"], title="Image Tag")] = None
    image_digest: Annotated[
        str | None,
        Field(
            description="SHA256 digest",
            examples=["3406990b6e4c7192317b6fdc5680498744f6142f01f0287f4ee0420d8c74063c"],
            title="Image Digest",
        ),
    ] = None
    docker_version: Annotated[
        str | None, Field(examples=[">=20.10,<29.0"], title="Docker Version")
    ] = None


class AnalysisNotebookTemplateInputType(BaseModel):
    """InputType for AnalysisNotebookTemplate."""

    name: Annotated[str, Field(title="Name")]
    entity_type: EntityType
    is_list: Annotated[bool | None, Field(title="Is List")] = False
    count_min: Annotated[int | None, Field(ge=0, title="Count Min")] = 1
    count_max: Annotated[int | None, Field(ge=0, title="Count Max")] = 1


class AnalysisNotebookTemplateSpecifications(BaseModel):
    """Specifications for AnalysisNotebookTemplate."""

    schema_version: Annotated[int | None, Field(title="Schema Version")] = 1
    python: PythonDependency | None = None
    docker: DockerDependency | None = None
    inputs: Annotated[list[AnalysisNotebookTemplateInputType] | None, Field(title="Inputs")] = []


class AnalysisNotebookTemplate(Entity):
    """Analysis notebook template model."""

    specifications: AnalysisNotebookTemplateSpecifications | None = None
    scale: AnalysisScale
