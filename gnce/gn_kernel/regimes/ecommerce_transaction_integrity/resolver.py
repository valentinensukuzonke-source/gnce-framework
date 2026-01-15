# gnce/gn_kernel/regimes/ecommerce_transaction_integrity/resolver.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
from gnce.gn_kernel.shared.fraud_signals import fraud_band

def resolve(payload: dict, obligation: dict) -> dict:
    band = fraud_band(payload)
    ...


def resolve(payload: Dict[str, Any], *, profile: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Emit transaction-binding obligations for ecommerce financial actions.

    This is intentionally shaped like other regime resolvers:
      - deterministic
      - returns a list[policy_obligation_dict]
      - never mutates input
    """
    ri = payload.get("risk_indicators") or {}
    fraud_suspected = bool(ri.get("fraud_suspected"))
    harmful_flag = bool(ri.get("harmful_content_flag"))
    violation_category = (ri.get("violation_category") or "").upper()
    previous_violations = int(ri.get("previous_violations") or 0)

    action = (payload.get("action") or "").upper()

    # A simple, deterministic transactional integrity obligation:
    # If the platform itself is flagging fraud abuse patterns, GNCE should block the action.
    violated = (
        action == "REFUND_REQUEST"
        and (fraud_suspected or violation_category == "FRAUD_SUSPECTED" or harmful_flag)
        and previous_violations >= 1
    )

    policies: List[Dict[str, Any]] = []
    policies.append({
        "domain": "Ecommerce Transaction Integrity",
        "regime": "ECOMMERCE_TRANSACTION_INTEGRITY",
        "framework": "Transactional Integrity & Abuse Prevention",
        "domain_id": "ECOMMERCE_TRANSACTION_INTEGRITY",
        "article": "ETI-1",
        "category": "Refund abuse / fraud suspected",
        "title": "Block suspicious refund requests",
        "status": "VIOLATED" if violated else "SATISFIED",
        # Severity should match your constitutional veto threshold behavior:
        # - CRITICAL triggers immediate pre-execution block.
        "severity": "CRITICAL" if violated else "LOW",
        "control_severity": "CRITICAL",
        "impact_on_verdict": (
            "BLOCKING - suspected refund fraud. Hard DENY."
            if violated else
            "No fraud signal detected."
        ),
        "trigger_type": "TRANSACTION_INTEGRITY",
        "rule_ids": ["ETI_REFUND_FRAUD_BLOCK"],
        "notes": (
            f"Harmful/fraud signal present: fraud_suspected={fraud_suspected}, "
            f"category={violation_category}, previous_violations={previous_violations}"
            if violated else
            "No fraud signal detected for this action."
        ),
        "evidence": {
            "action": action,
            "user_id": payload.get("user_id"),
            "harmful_content_flag": harmful_flag,
            "violation_category": violation_category or None,
            "previous_violations": previous_violations,
            "fraud_suspected": fraud_suspected,
        },
        "remediation": (
            "Block the refund request and route to Transaction Integrity review; "
            "collect evidence and re-run GNCE after mitigation."
            if violated else
            "Proceed with refund processing."
        ),
        "violation_detail": (
            f"fraud_suspected={fraud_suspected}, violation_category={violation_category}, "
            f"previous_violations={previous_violations}"
            if violated else
            ""
        ),
        "enforcement_scope": "TRANSACTION",
    })
    return policies
