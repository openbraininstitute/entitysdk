"""Types definitions."""

import os
import sys
import uuid

if sys.version_info < (3, 11):  # pragma: no cover
    from backports.strenum import StrEnum
else:
    from enum import StrEnum

from entitysdk._server_schemas import ActivityType as ActivityType
from entitysdk._server_schemas import AgePeriod as AgePeriod
from entitysdk._server_schemas import AssetLabel as AssetLabel
from entitysdk._server_schemas import AssetStatus as AssetStatus

# control which enums will be publicly available from the server schemas
from entitysdk._server_schemas import CircuitBuildCategory as CircuitBuildCategory
from entitysdk._server_schemas import CircuitScale as CircuitScale
from entitysdk._server_schemas import ContentType as ContentType
from entitysdk._server_schemas import DerivationType as DerivationType
from entitysdk._server_schemas import ElectricalRecordingOrigin as ElectricalRecordingOrigin
from entitysdk._server_schemas import (
    ElectricalRecordingStimulusShape as ElectricalRecordingStimulusShape,
)
from entitysdk._server_schemas import (
    ElectricalRecordingStimulusType as ElectricalRecordingStimulusType,
)
from entitysdk._server_schemas import ElectricalRecordingType as ElectricalRecordingType
from entitysdk._server_schemas import EMCellMeshGenerationMethod as EMCellMeshGenerationMethod
from entitysdk._server_schemas import EMCellMeshType as EMCellMeshType
from entitysdk._server_schemas import EntityType as EntityType
from entitysdk._server_schemas import PublicationType as PublicationType
from entitysdk._server_schemas import Sex as Sex
from entitysdk._server_schemas import SimulationExecutionStatus as SimulationExecutionStatus
from entitysdk._server_schemas import SingleNeuronSimulationStatus as SingleNeuronSimulationStatus
from entitysdk._server_schemas import SlicingDirectionType as SlicingDirectionType
from entitysdk._server_schemas import StorageType as StorageType
from entitysdk._server_schemas import StructuralDomain as StructuralDomain
from entitysdk._server_schemas import ValidationStatus as ValidationStatus

ID = uuid.UUID
Token = str
StrOrPath = str | os.PathLike[str]


class DeploymentEnvironment(StrEnum):
    """Deployment environment."""

    staging = "staging"
    production = "production"
