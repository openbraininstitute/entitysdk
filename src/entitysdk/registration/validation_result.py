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
SUFFIX_TO_NAME = {
    "currentscape": "currentscape",
    "evo_parameter_density": "evo_parameter_density",
    "optimisation": "optimisation",
    "parameters_distribution": "parameters_distribution",
    "scores": "scores",
    "traces": "traces",
    "thumbnail": None,  # skip thumbnails
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
        file_name=_detect_validation_name(figure_file.stem),
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


def _detect_validation_name(filename_stem: str) -> str | None:
    """Detect the ValidationResult name from a figure filename.

    The filename follows BluePyEModel's pattern where the suffix appears
    after the last "__" separator. For currentscape files, the suffix is
    followed by ".protocol.location".

    Examples:
      "emodel=cADpyr__...__seed=1__traces" -> "traces"
      "emodel=cADpyr__...__seed=1__currentscape.APWaveform_280.soma" -> "currentscape"
      "emodel=cADpyr__...__seed=1__scores" -> "scores"
      "emodel=IN_dAC__iteration=1b8100e__seed=11__evo_parameter_density" -> "evo_parameter_density"

    Returns:
        The ValidationResult name, or None if the suffix is not recognised
        or should be skipped (e.g., thumbnail).
    """
    # Split on "__" to get the suffix part (last segment)
    parts = filename_stem.split("__")
    if not parts:
        return None

    suffix_part = parts[-1]  # e.g., "traces" or "currentscape.APWaveform_280.soma"

    # Check each known suffix against the start of the suffix_part
    for suffix, name in SUFFIX_TO_NAME.items():
        if suffix_part == suffix or suffix_part.startswith(suffix + "."):
            return name

    return None
