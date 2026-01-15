# gnce/gn_kernel/regimes/SOX/applicability.py

from typing import Any, Dict

def is_applicable(payload: Dict[str, Any]) -> bool:
    profile = payload.get("sox_profile") or {}
    return profile.get("public_company") is True
