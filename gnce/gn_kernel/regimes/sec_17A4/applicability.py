# gnce/gn_kernel/regimes/sec_17A4/applicability.py
from __future__ import annotations
from typing import Any, Dict


def is_applicable(payload: Dict[str, Any]) -> bool:
    prof = payload.get("sec_17a4_profile") or {}
    if not isinstance(prof, dict):
        return False

    # Only applies if they are a broker-dealer (or equivalent flag)
    return bool(prof.get("broker_dealer"))
