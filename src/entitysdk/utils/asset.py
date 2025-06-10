"""Asset related utitilies."""

from collections.abc import Iterator
from typing import Any

from entitysdk.exception import EntitySDKError
from entitysdk.models.asset import Asset


def filter_assets(assets: list[Asset], selection: dict[str, Any]) -> Iterator[Asset]:
    """Filter assets according to selection dictionary."""
    if not assets:
        return iter([])

    if selection.keys() > assets[0].model_fields.keys():
        raise EntitySDKError(
            "Selection keys are not matching asset metadata keys.\n"
            f"Selection: {sorted(selection.keys())}\n"
            f"Available: {sorted(assets[0].model_fields.keys())}"
        )

    def _selection_predicate(asset: Asset) -> bool:
        attributes = vars(asset)
        for key, value in selection.items():
            if attributes[key] != value:
                return False
        return True

    return filter(_selection_predicate, assets)
