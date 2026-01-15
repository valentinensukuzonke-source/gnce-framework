from __future__ import annotations
from typing import Any


def assert_mutable(adra: dict, *, context: str = "") -> None:
    """
    Constitutional immutability guard.

    If an ADRA is finalized, it must never be mutated again.
    """
    if not isinstance(adra, dict):
        return

    if adra.get("finalized") is True:
        raise RuntimeError(
            "GNCE_CONSTITUTIONAL_BREACH: "
            "Attempted mutation of finalized ADRA"
            + (f" ({context})" if context else "")
        )
