"""Asset related utitilies."""

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
