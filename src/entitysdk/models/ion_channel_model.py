"""Ion channel model."""

from typing import Annotated

from pydantic import Field

from entitysdk.mixin import HasAssets
from entitysdk.models.contribution import Contribution
from entitysdk.models.entity import Entity
from entitysdk.models.base import BaseModel
from entitysdk.models.morphology import Species, Strain, BrainRegion, License


class Ion(Entity):
    """Represents an ion involved in the ion channel mechanism."""

    id: Annotated[
        str,
        Field(
            description="Ontology-based identifier for the ion.",
            examples=["https://neuroshapes.org/Ca"]
        ),
    ]
    name: Annotated[
        str,
        Field(
            description="Name of the ion (e.g. 'Ca', 'Na').",
            examples=["Ca"]
        ),
    ]


class NmodlParameters(BaseModel):
    """Parameters derived from the NMODL (.mod) file."""

    global_: Annotated[
        list[str] | None,
        Field(
            description="Variables listed in the GLOBAL statement.",
            examples=[["gna", "gk"]],
        ),
    ] = None
    range: Annotated[
        list[str] | None,
        Field(
            description="Variables listed in the RANGE statement.",
            examples=[["gCa_HVAbar", "ica"]]
        ),
    ] = None
    read: Annotated[
        list[str] | None,
        Field(
            description="Variables listed in the READ statement.",
            examples=[["eca"]],
        ),
    ] = None
    suffix: Annotated[
        str | None,
        Field(
            description="SUFFIX name from the mod file.",
            examples=["Ca_HVA2"],
        ),
    ] = None
    useion: Annotated[
        list[str] | None,
        Field(
            description="List of ions in USEION statements.",
            examples=[["ca"]],
        ),
    ] = None
    write: Annotated[
        list[str] | None,
        Field(
            description="Variables in WRITE or NONSPECIFIC_CURRENT statements.",
            examples=[["ica"]],
        ),
    ] = None
    nonspecific: Annotated[
        list[str] | None,
        Field(
            description="Variables listed in NONSPECIFIC_CURRENT statements.",
            examples=[["ihcn"]],
        ),
    ] = None
    valence: Annotated[
        int | None,
        Field(
            description="VALENCE of the ion, if specified.",
            examples=[2],
        ),
    ] = None


class IonChannelModel(HasAssets, Entity):
    """Ion channel mechanism model."""

    name: Annotated[
        str,
        Field(
            description="The name of the ion channel model (e.g., the SUFFIX or POINT_PROCESS name).",
            examples=["Ca_HVA", "NaT"]
        ),
    ]
    description: Annotated[
        str,
        Field(
            description="A description of the ion channel mechanism.",
            examples=["High-voltage activated calcium channel"]
        ),
    ]
    species: Annotated[
        Species,
        Field(
            description="The species for which the mechanism applies."
        ),
    ]
    strain: Annotated[
        Strain | None,
        Field(
            description="The specific strain of the species, if applicable."
        ),
    ] = None
    brain_region: Annotated[
        BrainRegion,
        Field(
            description="The brain region where the mechanism is used or applies."
        ),
    ]
    license: Annotated[
        License | None,
        Field(
            description="License under which the mechanism is distributed."
        ),
    ] = None
    contributions: Annotated[
        list[Contribution] | None,
        Field(
            description="List of contributions related to this mechanism."
        ),
    ] = None
    is_ljp_corrected: Annotated[
        bool,
        Field(
            description="Whether the mechanism is corrected for liquid junction potential.",
        ),
    ]
    is_temperature_dependent: Annotated[
        bool,
        Field(
            description="Whether the mechanism includes temperature dependence (e.g. via q10 factor).",
        ),
    ]
    temperature_celsius: Annotated[
        int,
        Field(
            description="The temperature at which the mechanism has been built to work on."
        ),
    ]
    stochastic: Annotated[
        bool | None,
        Field(
            description="Whether the mechanism has stochastic behavior.",
        ),
    ] = False

    ions: Annotated[
        list[Ion] | None,
        Field(
            description="List of ions involved (used in USEION statements)."
        ),
    ]
    nmodl_parameters: Annotated[
        NmodlParameters,
        Field(
            description="Parameters parsed from the NMODL mechanism definition."
        ),
    ]
    acronym: Annotated[
        str | None,
        Field(
            description="The Allen Notation acronym.",
        ),
    ]
    legacy_id: list[str] | None = None