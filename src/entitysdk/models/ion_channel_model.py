"""Ion channel model."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.base import BaseModel
from entitysdk.models.contribution import Contribution
from entitysdk.models.scientific_artifact import ScientificArtifact


class UseIon(BaseModel):
    """Specifies how an ion is used in the mod file (USEION behavior)."""

    ion_name: Annotated[
        str,
        Field(
            description="The name of the ion involved.",
            examples=["Ca"],
        ),
    ]
    read: Annotated[
        list[str] | None,
        Field(
            description="Variables listed in the READ statement for this ion.",
            examples=[["eca", "ica"]],
        ),
    ]
    write: Annotated[
        list[str] | None,
        Field(
            description="Variables listed in the WRITE statement for this ion.",
            examples=[["ica"]],
        ),
    ]
    valence: Annotated[
        int | None,
        Field(
            description="VALENCE of the ion, if specified.",
            examples=[2],
        ),
    ]
    main_ion: Annotated[
        bool | None,
        Field(
            description="Whether this ion is the main ion for the mechanism.",
            examples=[True],
        ),
    ] = None


class NeuronBlock(BaseModel):
    """Variables declared in the NEURON block of the mod file."""

    global_: Annotated[
        list[dict[str, str | None]] | None,
        Field(
            description="Variables listed in the GLOBAL statement, with associated units.",
            examples=[[{"celsius": "degree C"}]],
            alias="global",
        ),
    ] = None
    range: Annotated[
        list[dict[str, str | None]] | None,
        Field(
            description="Variables listed in the RANGE statement, with associated units.",
            examples=[[{"gCa_HVAbar": "S/cm2"}, {"ica": "mA/cm2"}]],
        ),
    ] = None
    useion: Annotated[
        list[UseIon] | None,
        Field(
            description="Ion-specific READ/WRITE/VALENCE declarations from USEION.",
        ),
    ] = None
    nonspecific: Annotated[
        list[dict[str, str | None]] | None,
        Field(
            description="Variables listed in NONSPECIFIC_CURRENT statements.",
            examples=[[{"ihcn": "mA/cm2"}]],
        ),
    ] = None


class IonChannelModel(ScientificArtifact):
    """Ion channel mechanism model."""

    name: Annotated[
        str,
        Field(
            description="The name of the ion channel model "
            "(e.g., the SUFFIX or POINT_PROCESS name).",
            examples=["Ca_HVA"],
        ),
    ]
    nmodl_suffix: Annotated[
        str,
        Field(
            description="The SUFFIX of the ion channel model as defined in the NMODL file ",
            examples=["Ca_HVA"],
        ),
    ]
    description: Annotated[
        str,
        Field(
            description="A description of the ion channel mechanism.",
            examples=["High-voltage activated calcium channel"],
        ),
    ]
    contributions: Annotated[
        list[Contribution] | None,
        Field(description="List of contributions related to this mechanism."),
    ] = None
    is_ljp_corrected: Annotated[
        bool,
        Field(
            description="Whether the mechanism is corrected for liquid junction potential.",
        ),
    ] = False
    is_temperature_dependent: Annotated[
        bool,
        Field(
            description="Whether the mechanism includes temperature dependence "
            "(e.g. via q10 factor).",
        ),
    ]
    temperature_celsius: Annotated[
        int,
        Field(description="The temperature at which the mechanism has been built to work on."),
    ]
    is_stochastic: Annotated[
        bool | None,
        Field(
            description="Whether the mechanism has stochastic behavior.",
        ),
    ] = False
    neuron_block: Annotated[
        NeuronBlock,
        Field(description="Variables declared in the NEURON block of the mod file."),
    ]
    legacy_id: list[str] | None = None
