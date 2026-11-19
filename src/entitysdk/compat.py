"""Compatibility imports."""

import sys

if sys.version_info < (3, 11):  # pragma: no cover
    from backports.strenum import StrEnum
    from typing_extensions import Self
else:
    from enum import StrEnum  # noqa: F401
    from typing import Self  # noqa: F401


if sys.version_info < (3, 12):  # pragma: no cover
    from typing_extensions import Buffer, TypedDict, override
else:
    from collections.abc import Buffer  # noqa: F401
    from typing import TypedDict, override  # noqa: F401
