"""Subject model."""

from datetime import timedelta
from typing import Annotated

from pydantic import Field

from entitysdk.models.entity import Entity
from entitysdk.models.taxonomy import Species, Strain
from entitysdk.types import AgePeriod, Sex


class Subject(Entity):
    """Subject model."""

    sex: Annotated[
        Sex,
        Field(title="Sex", description="Sex of the subject"),
    ]
    weight: Annotated[
        float | None,
        Field(title="Weight", description="Weight in grams", gt=0.0),
    ] = None
    age_value: Annotated[
        timedelta | None,
        Field(title="Age value", description="Age value interval.", gt=timedelta(0)),
    ] = None
    age_min: Annotated[
        timedelta | None,
        Field(title="Minimum age range", description="Minimum age range", gt=timedelta(0)),
    ] = None
    age_max: Annotated[
        timedelta | None,
        Field(title="Maximum age range", description="Maximum age range", gt=timedelta(0)),
    ] = None
    age_period: AgePeriod | None = None
    species: Annotated[
        Species,
        Field(
            description="The species of the subject.",
        ),
    ]
    strain: Annotated[
        Strain | None,
        Field(
            description="The optional strain of the subject.",
        ),
    ] = None
