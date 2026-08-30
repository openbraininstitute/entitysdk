"""ValidationResult registration."""

import logging
from pathlib import Path

from entitysdk import Client
from entitysdk.models import ValidationResult
from entitysdk.types import ID, AssetLabel, ContentType

L = logging.getLogger(__name__)

FIGURE_EXT_TO_CONTENT_TYPE = {
    ".pdf": ContentType.application_pdf,
    ".png": ContentType.image_png,
}


def register_validation_result_figure(
    *,
    client: Client,
    authorized_public: bool,
    figure_file: Path,
    passed: bool,
    validated_entity_id: ID,
) -> ValidationResult:
    """Register ValidationResult figure."""
    content_type = FIGURE_EXT_TO_CONTENT_TYPE[figure_file.suffix]
    validation_result = client.register_entity(
        ValidationResult(
            name=figure_file.stem,
            passed=passed,
            validated_entity_id=validated_entity_id,
            authorized_public=authorized_public,
        )
    )
    asset = client.upload_file(
        entity_id=validation_result.id,
        entity_type=ValidationResult,
        file_path=figure_file,
        file_content_type=content_type,
        asset_label=AssetLabel.validation_result_figure,
    )
    L.info(
        "Registered EModel ValidationResult(id=%s, name=%s) with Asset(id=%s, path=%s)",
        validation_result.id,
        validation_result.name,
        asset.id,
        asset.path,
    )
    return validation_result
