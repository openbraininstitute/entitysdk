"""Asset related utitilies."""

from pathlib import Path
from typing import Any

from entitysdk.exception import EntitySDKError
from entitysdk.models.asset import Asset


def filter_assets(assets: list[Asset], selection: dict[str, Any]) -> list[Asset]:
    """Filter assets according to selection dictionary."""
    if not assets:
        return []

    if not selection:
        return assets

    if not selection.keys() <= Asset.model_fields.keys():
        raise EntitySDKError(
            "Selection keys are not matching asset metadata keys.\n"
            f"Selection: {sorted(selection.keys())}\n"
            f"Available: {sorted(Asset.model_fields.keys())}"
        )

    def _selection_predicate(asset: Asset) -> bool:
        attributes = vars(asset)
        for key, value in selection.items():
            if attributes[key] != value:
                return False
        return True

    return [asset for asset in assets if _selection_predicate(asset)]


def resolve_asset_path(asset: Asset, directory_file: Path | None = None) -> Path:
    """Resolve asset path."""
    file_path = Path(asset.storage_type, asset.full_path)

    if asset.is_directory:
        if directory_file is None:
            raise EntitySDKError("Fetching a directory file requires an `asset_path`")
        return file_path / directory_file

    if directory_file is not None:
        raise EntitySDKError("Cannot pass `asset_path` to non-directories")

    return file_path
