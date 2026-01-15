# gnce/gn_kernel/federation/mode_resolver.py
from __future__ import annotations

from typing import Optional

VALID_MODES = {"OFF", "HASH_ONLY", "REDACTED", "FULL"}


def resolve_mode(enabled: bool, configured_mode: Optional[str]) -> str:
    """
    Resolve the effective federation mode.

    Constitutional rules:
    - If not enabled → OFF
    - Mode must be one of VALID_MODES
    - Invalid values collapse to OFF
    """
    if not enabled:
        return "OFF"

    if not configured_mode:
        return "OFF"

    mode = str(configured_mode).upper().strip()
    return mode if mode in VALID_MODES else "OFF"
