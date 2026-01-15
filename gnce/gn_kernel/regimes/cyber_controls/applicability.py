"""Applicability rules for GNCE Cyber Controls Regime.

Only applies when a payload represents a cyber-relevant action or provides
cyber-control context.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

_CYBER_ACTION_PREFIXES = (
    "SECURITY_",
    "CYBER_",
    "IAM_",
    "ACCESS_",
    "NETWORK_",
    "CLOUD_",
    "DEPLOY_",
    "CONFIG_",
    "KEY_",
    "ENCRYPT_",
    "DLP_",
    "INCIDENT_",
    "PATCH_",
)

def is_applicable(payload: Dict[str, Any]) -> Tuple[bool, str]:
    """Return (applicable, reason)."""
    action = str(payload.get("action", "")).upper()
    if action and any(action.startswith(pfx) for pfx in _CYBER_ACTION_PREFIXES):
        return True, f"action_prefix:{action.split('_', 1)[0]}"

    # Explicit context flags.
    if payload.get("cyber_context") or payload.get("security_context") or payload.get("cyber_controls"):
        return True, "explicit_cyber_context"

    # Sensitive-data handling should bind cyber controls.
    data = payload.get("data") or {}
    if isinstance(data, dict) and str(data.get("classification", "")).upper() in {"CONFIDENTIAL", "SECRET", "TOP_SECRET"}:
        return True, "sensitive_data_classification"

    return False, "not_cyber_relevant"
