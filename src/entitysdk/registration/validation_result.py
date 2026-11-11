"""ValidationResult registration."""

import logging
import tempfile
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
    "parameters_distribution": "parameter_distribution",
    "scores": "scores",
    "traces": "traces",
    "thumbnail": "thumbnail",
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
    detected = _detect_validation_name(figure_file.stem)
    validation_result = client.register_entity(
        ValidationResult(
            name="thumbnail" if detected == "thumbnail" else figure_file.stem,
            passed=passed,
            validated_entity_id=validated_entity_id,
            authorized_public=authorized_public,
        )
    )
    asset = client.upload_file(
        entity_id=validation_result.id,
        entity_type=ValidationResult,
        file_path=figure_file,
        file_name=f"{detected}{figure_file.suffix}" if detected else None,
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
        The ValidationResult name, or None if the suffix is not recognised.
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


def register_validation_result(
    *,
    client: Client,
    name: str,
    passed: bool,
    validated_entity_id: ID,
    authorized_public: bool,
    figure_files: list[Path] | None = None,
    details_text: str | None = None,
) -> ValidationResult | None:
    """Register a ValidationResult with optional figure and details assets.

    Skips registration when a ValidationResult with the same ``name`` already
    exists for ``validated_entity_id``.

    Figures are uploaded under their real filenames: downstream UIs derive
    captions and documentation from the asset path (e.g.
    ``hyperpolarization_validation.pdf`` -> "Hyperpolarization Validation").

    Args:
        client: Entitysdk client.
        name: Validation result name.
        passed: Whether the validation passed.
        validated_entity_id: ID of the validated entity (e.g. a MEModel).
        authorized_public: Whether the entity is public.
        figure_files: ``.pdf``/``.png`` figure files to upload as
            ``validation_result_figure`` assets. Missing files and unsupported
            suffixes are skipped with a warning.
        details_text: Free-text details uploaded as a ``validation_result_details``
            asset. The filename keeps the result name (space-stripped) so
            downstream UIs can match it to the result (e.g.
            "Simulatable Neuron Input Resistance Validation" ->
            ``SimulatableNeuronInputResistanceValidation_validation_details.txt``).

    Returns:
        The registered ValidationResult, or ``None`` if it already existed.
    """
    existing = client.search_entity(
        entity_type=ValidationResult,
        query={"name": name, "validated_entity_id": validated_entity_id},
    ).first()
    if existing is not None:
        L.info(
            "ValidationResult %r already exists for %s; skipping.",
            name,
            validated_entity_id,
        )
        return None

    validation_result = client.register_entity(
        ValidationResult(
            name=name,
            passed=passed,
            validated_entity_id=validated_entity_id,
            authorized_public=authorized_public,
        )
    )
    L.info(
        "Registered ValidationResult(id=%s, name=%r, passed=%s)",
        validation_result.id,
        validation_result.name,
        validation_result.passed,
    )

    for figure_file in figure_files or []:
        content_type = FIGURE_EXT_TO_CONTENT_TYPE.get(figure_file.suffix)
        if not figure_file.exists():
            L.warning("Validation figure not found: %s", figure_file)
            continue
        if content_type is None:
            L.warning("Unsupported validation figure format: %s", figure_file)
            continue
        client.upload_file(
            entity_id=validation_result.id,
            entity_type=ValidationResult,
            file_path=figure_file,
            file_content_type=content_type,
            asset_label=AssetLabel.validation_result_figure,
        )

    if details_text:
        details_name = f"{name.replace(' ', '')}_validation_details.txt"
        with tempfile.TemporaryDirectory() as tmpdir:
            details_path = Path(tmpdir) / details_name
            details_path.write_text(details_text, encoding="utf-8")
            client.upload_file(
                entity_id=validation_result.id,
                entity_type=ValidationResult,
                file_path=details_path,
                file_content_type=ContentType.text_plain,
                asset_label=AssetLabel.validation_result_details,
            )

    return validation_result


def _checked_figures(figure_files: list[Path]) -> dict[str, tuple[Path, ContentType]]:
    """Map each figure's file name to its path and content type, rejecting bad inputs."""
    figures: dict[str, tuple[Path, ContentType]] = {}
    for figure_file in figure_files:
        content_type = FIGURE_EXT_TO_CONTENT_TYPE.get(figure_file.suffix)
        if content_type is None:
            raise ValueError(f"Unsupported validation figure format: {figure_file}")
        if not figure_file.is_file():
            raise ValueError(f"Validation figure not found: {figure_file}")
        if figure_file.name in figures:
            raise ValueError(f"Several validation figures are named {figure_file.name!r}.")
        figures[figure_file.name] = (figure_file, content_type)
    return figures


def _replace_assets(
    client: Client,
    validation_result_id: ID,
    label: AssetLabel,
    files: dict[str, tuple[Path, ContentType]],
) -> None:
    """Make ``files`` the ``label`` assets of a ValidationResult, keyed by file name.

    An asset whose path is one of the new file names is replaced by that file, new
    names are uploaded, and the remaining assets with ``label`` are deleted last.
    entitycore allows one asset per path, so a same-named asset is deleted just
    before its replacement is uploaded (``Client.update_asset_file``).
    """
    existing = [
        asset
        for asset in client.get_entity_assets(
            validation_result_id, entity_type=ValidationResult
        ).all()
        if asset.label == label
    ]
    by_path = {asset.path: asset for asset in existing}
    for file_name, (file_path, content_type) in files.items():
        if file_name in by_path:
            client.update_asset_file(
                entity_id=validation_result_id,
                entity_type=ValidationResult,
                asset_id=by_path[file_name].id,
                file_path=file_path,
                file_content_type=content_type,
            )
        else:
            client.upload_file(
                entity_id=validation_result_id,
                entity_type=ValidationResult,
                file_path=file_path,
                file_content_type=content_type,
                asset_label=label,
            )
    for asset in existing:
        if asset.path not in files:
            client.delete_asset(
                entity_id=validation_result_id,
                entity_type=ValidationResult,
                asset_id=asset.id,
            )


def update_validation_result(
    *,
    client: Client,
    validation_result_id: ID,
    passed: bool,
    figure_files: list[Path] | None = None,
    details_text: str | None = None,
) -> ValidationResult:
    """Update the verdict of an existing ValidationResult and, optionally, its assets.

    Unlike :func:`register_validation_result`, nothing is looked up: the caller
    chooses the result to update. All inputs are checked before anything changes,
    and only the assets passed in are replaced.

    Args:
        client: Entitysdk client.
        validation_result_id: ID of the ValidationResult to update.
        passed: The new verdict.
        figure_files: ``.pdf``/``.png`` files that replace the result's
            ``validation_result_figure`` assets; figures not among them are
            deleted. ``None`` keeps the existing figures.
        details_text: Text that replaces the result's ``validation_result_details``
            asset (same file name as :func:`register_validation_result` uses).
            ``None`` keeps the existing details.

    Returns:
        The updated ValidationResult.

    Raises:
        ValueError: If a figure file is missing, unsupported or named like another,
            or ``details_text`` is empty. Nothing is changed then.
    """
    figures = None if figure_files is None else _checked_figures(figure_files)
    if details_text is not None and not details_text.strip():
        raise ValueError("details_text is empty; pass None to keep the existing details.")

    # The verdict first: on a result owned by another user this fails (403) before any
    # asset is touched.
    validation_result = client.update_entity(
        entity_id=validation_result_id,
        entity_type=ValidationResult,
        attrs_or_entity={"passed": passed},
    )
    if figures is not None:
        _replace_assets(client, validation_result_id, AssetLabel.validation_result_figure, figures)
    if details_text is not None:
        details_name = f"{validation_result.name.replace(' ', '')}_validation_details.txt"
        with tempfile.TemporaryDirectory() as tmpdir:
            details_path = Path(tmpdir) / details_name
            details_path.write_text(details_text, encoding="utf-8")
            _replace_assets(
                client,
                validation_result_id,
                AssetLabel.validation_result_details,
                {details_name: (details_path, ContentType.text_plain)},
            )
    L.info(
        "Updated ValidationResult(id=%s, name=%r, passed=%s)",
        validation_result.id,
        validation_result.name,
        validation_result.passed,
    )
    return validation_result


def register_memodel_validation_results(
    *,
    client: Client,
    memodel_id: ID,
    validation_dict: dict,
    authorized_public: bool,
) -> list[ValidationResult]:
    """Register per-test ValidationResults from a bluecellulab validation run.

    ``validation_dict`` is the output of ``bluecellulab``'s ``run_validations``:
    a mapping of test keys to dicts with keys ``name``, ``passed``,
    ``validation_details`` (text), and ``figures`` (list of figure paths).
    Entries without ``name``/``passed`` (e.g. ``memodel_properties``) are
    skipped, as are results already registered for ``memodel_id``.

    Args:
        client: Entitysdk client.
        memodel_id: ID of the validated MEModel.
        validation_dict: ``run_validations`` result dict.
        authorized_public: Whether the registered entities are public.

    Returns:
        The newly registered ValidationResult entities.
    """
    registered: list[ValidationResult] = []
    for value in validation_dict.values():
        if not isinstance(value, dict) or "name" not in value or "passed" not in value:
            continue
        result = register_validation_result(
            client=client,
            name=value["name"],
            passed=bool(value["passed"]),
            validated_entity_id=memodel_id,
            authorized_public=authorized_public,
            figure_files=[Path(f) for f in value.get("figures", [])],
            details_text=value.get("validation_details") or None,
        )
        if result is not None:
            registered.append(result)
    return registered
