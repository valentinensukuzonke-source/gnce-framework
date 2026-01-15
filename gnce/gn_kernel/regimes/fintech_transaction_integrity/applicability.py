"""gnce.gn_kernel.regimes.fintech_transaction_integrity.applicability

FTI applicability: this regime applies to FINTECH payloads that represent
a financial transaction or onboarding event that should be subject to fraud controls.

We keep this deliberately broad so the regime *runs* and lets obligations decide NA vs violated.
"""

from __future__ import annotations

from typing import Any, Dict


_FINTECH_ACTIONS = {
    "WIRE_TRANSFER",
    "CARD_PAYMENT",
    "ACH_TRANSFER",
    "P2P_TRANSFER",
    "WITHDRAWAL",
    "DEPOSIT",
    "OPEN_ACCOUNT",
    "ACCOUNT_OPEN",
    "KYC_SUBMISSION",
}


def is_applicable(payload: Dict[str, Any]) -> bool:
    industry = str(payload.get("industry_id") or "").strip().upper()
    profile_id = str(payload.get("profile_id") or "").strip().upper()
    action = str(payload.get("action") or "").strip().upper()

    if industry == "FINTECH" or profile_id.startswith("FINTECH_"):
        # If it's any known fintech action, definitely applicable.
        if action in _FINTECH_ACTIONS:
            return True

        # If it carries fraud indicators, treat as applicable even if action is new/unknown.
        risk = payload.get("risk_indicators") or {}
        if "fraud_risk_score" in risk or "violation_category" in risk:
            return True

    return False
