"""Generic dataset model."""

from entitysdk.mixin import NameDescriptionMixin
from entitysdk.models.brain_region import BrainRegion
from entitysdk.models.entity import Entity
from entitysdk.models.license import License
from entitysdk.models.subject import Subject


class GenericDataset(NameDescriptionMixin, Entity):
    """Dataset with any content, for data that doesn't fit any other entity type.

    The files are uploaded in a `generic_dataset_files` directory asset,
    with an optional `generic_dataset_readme` asset in markdown or plain text.

    A generic dataset is always private: entitycore rejects `authorized_public=True`,
    and skips the datasets when a project is made public.
    """

    subject: Subject | None = None
    brain_region: BrainRegion | None = None
    license: License | None = None
