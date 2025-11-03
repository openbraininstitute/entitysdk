"""Analysis notebook environment model."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.base import BaseModel
from entitysdk.models.entity import Entity


class PythonRuntimeInfo(BaseModel):
    """Python Runtime Information."""

    version: Annotated[
        str,
        Field(
            description="Output of `platform.python_version()`",
            examples=["3.9.21"],
            title="Version",
        ),
    ]
    implementation: Annotated[
        str,
        Field(
            description="Output of `platform.python_implementation()`",
            examples=["CPython"],
            title="Implementation",
        ),
    ]
    executable: Annotated[
        str,
        Field(
            description="Output of `sys.executable`",
            examples=["/usr/bin/python"],
            title="Executable",
        ),
    ]


class DockerRuntimeInfo(BaseModel):
    """Docker Runtime Information."""

    image_repository: Annotated[
        str, Field(examples=["openbraininstitute/obi-notebook-image"], title="Image Repository")
    ]
    image_tag: Annotated[str, Field(examples=["2025.09.24-2"], title="Image Tag")]
    image_digest: Annotated[
        str | None,
        Field(
            description="SHA256 digest",
            examples=["3406990b6e4c7192317b6fdc5680498744f6142f01f0287f4ee0420d8c74063c"],
            title="Image Digest",
        ),
    ] = None
    docker_version: Annotated[str | None, Field(examples=["28.4.0"], title="Docker Version")] = None


class OsRuntimeInfo(BaseModel):
    """OS Runtime Information."""

    system: Annotated[
        str, Field(description="Output of `platform.system()`", examples=["Linux"], title="System")
    ]
    release: Annotated[
        str,
        Field(
            description="Output of `platform.release()`",
            examples=["5.14.0-427.28.1.el9_4.x86_64"],
            title="Release",
        ),
    ]
    version: Annotated[
        str,
        Field(
            description="Output of `platform.version()`",
            examples=["#1 SMP PREEMPT_DYNAMIC Fri Aug 2 03:44:10 EDT 2024"],
            title="Version",
        ),
    ]
    machine: Annotated[
        str,
        Field(description="Output of `platform.machine()`", examples=["x86_64"], title="Machine"),
    ]
    processor: Annotated[
        str,
        Field(
            description="Output of `platform.processor()`", examples=["x86_64"], title="Processor"
        ),
    ]


class RuntimeInfo(BaseModel):
    """Runtime Information."""

    schema_version: Annotated[int | None, Field(title="Schema Version")] = 1
    python: PythonRuntimeInfo
    docker: DockerRuntimeInfo | None = None
    os: OsRuntimeInfo | None = None


class AnalysisNotebookEnvironment(Entity):
    """Analysis notebook environment model."""

    runtime_info: RuntimeInfo | None
