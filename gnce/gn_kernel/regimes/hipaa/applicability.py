"""gnce/gn_kernel/regimes/hipaa/applicability.py

Return whether HIPAA regime should run for a payload.

Principle:
- HIPAA is US-only in GNCE (this repo).
- Apply when payload appears to involve healthcare + PHI handling.
"""

from __future__ import annotations

from typing import Any, Dict


def _canon(x: Any) -> str:
    return str(x or "").strip().upper().replace(" ", "_").replace("-", "_")


def is_applicable(payload: Dict[str, Any]) -> bool:
    payload = payload or {}
    meta = payload.get("meta") or {}

    jurisdiction = _canon(meta.get("jurisdiction"))
    if jurisdiction != "US":
        return False

    industry = _canon(payload.get("industry_id"))
    action = _canon(payload.get("action"))

    # explicit hint wins
    hipaa_profile = payload.get("hipaa_profile") or {}
    if hipaa_profile.get("handles_phi") is True:
        return True
    if hipaa_profile.get("handles_phi") is False:
        return False

    # infer from healthcare-like actions/fields
    if industry == "HEALTHCARE":
        return True
    if action in {"ACCESS_RECORD", "EXPORT_DATA", "SCHEDULE_APPOINTMENT"}:
        return True
    if payload.get("record_access") or payload.get("export") or payload.get("appointment"):
        return True

    return False
