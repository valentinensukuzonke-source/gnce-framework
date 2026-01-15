# gnce/gn_kernel/regimes/glba/applicability.py
from typing import Dict, Any


def is_applicable(payload: Dict[str, Any]) -> bool:
    profile = payload.get("glba_profile") or {}
    return bool(profile.get("handles_npi"))
