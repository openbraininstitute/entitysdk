"""Ion channel models."""

from typing import Annotated

from pydantic import Field

from entitysdk.models.core import Identifiable


class IonChannel(Identifiable):
    """Ion channel model."""

    name: Annotated[
        str,
        Field(
            title="Ion channel name",
            description="Name of the ion channel.",
            example="Kv1.1",
        ),
    ]
    description: Annotated[
        str,
        Field(
            title="Description",
            description="Description of the ion channel.",
        ),
    ]
    label: Annotated[
        str,
        Field(
            title="Ion channel label",
            description="Unique label for the ion channel.",
            example="K<SUB>v</SUB>1.1",
        ),
    ]
    gene: Annotated[
        str,
        Field(
            title="Gene",
            description=("The gene that encodes the ion channel, from the RGD database."),
            example="Kcna1",
        ),
    ]
    synonyms: Annotated[
        list[str],
        Field(
            title="Synonyms",
            description="Other names for the ion channel.",
            example=["HBK1", "Kcn1", "MBK1", "RCK1", "AEMK", "HUK1", "Shak", "Kcna", "Kcpvd"],
        ),
    ]
