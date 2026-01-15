"""
Applicability logic for SAAS_TRANSACTION_INTEGRITY.
"""
from __future__ import annotations

from typing import Any, Dict


def is_applicable(payload: Dict[str, Any]) -> bool:
    payload = payload or {}
    industry = str(payload.get("industry_id") or "").strip().upper().replace(" ", "_").replace("-", "_")
    # Apply broadly to SaaS B2B / enterprise software payloads.
    return industry in {"SAAS_B2B", "SAAS", "B2B_SAAS", "ENTERPRISE_SOFTWARE"}
