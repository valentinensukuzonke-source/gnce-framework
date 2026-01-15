"""gnce.gn_kernel.regimes.fintech_transaction_integrity.resolver

Kernel-compatible resolver for the FINTECH_TRANSACTION_INTEGRITY regime.

Key contract (GNCE v0.7.x):
- The regime's `resolver` registered in REGIME_REGISTRY MUST return a **List[Dict]**,
  where each dict is a policy/obligation evaluation record that includes at minimum:
    - regime, article, status, severity
- Returning a dict like {"policies": [...]} will cause the kernel to treat the regime as producing
  no outputs (and it will emit an UNSUPPORTED placeholder), which leads to ALLOW.

This resolver evaluates the FTI obligation catalog and returns one policy record per obligation
with status set to NOT_APPLICABLE / SATISFIED / VIOLATED.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .obligations import obligations


def _safe_get(d: Dict[str, Any], path: List[str], default=None):
    cur: Any = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def _risk_indicators(payload: Dict[str, Any]) -> Dict[str, Any]:
    ri = payload.get("risk_indicators") or {}
    return ri if isinstance(ri, dict) else {}


def _payment(payload: Dict[str, Any]) -> Dict[str, Any]:
    p = payload.get("payment") or {}
    return p if isinstance(p, dict) else {}


def _evaluate_obligation(payload: Dict[str, Any], obligation: Dict[str, Any]) -> Dict[str, Any]:
    """Return the evaluation overlay for a single obligation."""
    article = (obligation.get("article") or "").upper()

    action = (payload.get("action") or "").upper()
    ri = _risk_indicators(payload)
    payment = _payment(payload)

    violation_category = (ri.get("violation_category") or "").upper()
    harmful_flag = bool(ri.get("harmful_content_flag", False))
    prev_violations = int(ri.get("previous_violations", 0) or 0)

    fraud_score = ri.get("fraud_risk_score", None)
    aml_score = ri.get("aml_risk_score", None)

    scheme = (payment.get("scheme") or "").upper() or None
    beneficiary_country = payment.get("beneficiary_country", None)

    # Default response: Not applicable unless matched.
    out: Dict[str, Any] = {
        "status": "NOT_APPLICABLE",
        "severity": obligation.get("severity", "LOW"),
        "trigger_type": "NOT_APPLICABLE",
    }

    # --- Obligation: High-risk wire transfers (fraud) ---
    if article == "FTI:HIGH_RISK_WIRE_TRANSFER":
        # Applicable when action is WIRE_TRANSFER OR payment scheme is WIRE, and fraud indicators are high.
        is_wire = (action == "WIRE_TRANSFER") or (scheme == "WIRE")
        if not is_wire:
            return out

        # A "high risk" signal can be expressed either by category or by score.
        is_high = (violation_category == "FRAUD_HIGH_RISK") or (
            isinstance(fraud_score, (int, float)) and float(fraud_score) >= 0.90
        )

        if harmful_flag and is_high:
            return {
                "status": "VIOLATED",
                "severity": "HIGH",
                "trigger_type": "FTI_CONTROL",
                "recommended_outcome": "DENY",
                "rationale": "High-risk wire transfer flagged by fraud signals.",
                "evidence": {
                    "risk_band": "HIGH",
                    "risk_score": fraud_score,
                    "violation_category": violation_category or None,
                    "harmful_content_flag": harmful_flag,
                    "previous_violations": prev_violations,
                    "action": action,
                    "scheme": scheme,
                    "beneficiary_country": beneficiary_country,
                },
            }

        # If it is a wire transfer but not high risk, we still record that the obligation was evaluated.
        return {
            "status": "SATISFIED",
            "severity": "LOW",
            "trigger_type": "FTI_CONTROL",
            "rationale": "Wire transfer evaluated; fraud signals did not exceed block threshold.",
            "evidence": {
                "risk_score": fraud_score,
                "violation_category": violation_category or None,
                "harmful_content_flag": harmful_flag,
                "previous_violations": prev_violations,
                "action": action,
                "scheme": scheme,
                "beneficiary_country": beneficiary_country,
            },
        }

    # --- Obligation: High-risk AML transfer (AML/KYC) ---
    if article == "FTI:HIGH_RISK_AML_TRANSFER":
        # Applicable when initiating a transfer (or similar), and AML indicators are high.
        is_transfer = action in {"INITIATE_TRANSFER", "TRANSFER", "PAYMENT", "SEND_MONEY"}
        if not is_transfer:
            return out

        is_high = (violation_category == "AML_RISK") or (
            isinstance(aml_score, (int, float)) and float(aml_score) >= 0.90
        )

        if harmful_flag and is_high:
            return {
                "status": "VIOLATED",
                "severity": "HIGH",
                "trigger_type": "FTI_CONTROL",
                "recommended_outcome": "DENY",
                "rationale": "AML/KYC high-risk transfer flagged by AML signals.",
                "evidence": {
                    "risk_band": "HIGH",
                    "risk_score": aml_score,
                    "violation_category": violation_category or None,
                    "harmful_content_flag": harmful_flag,
                    "previous_violations": prev_violations,
                    "action": action,
                    "scheme": scheme,
                    "beneficiary_country": beneficiary_country,
                },
            }

        return {
            "status": "SATISFIED",
            "severity": "LOW",
            "trigger_type": "FTI_CONTROL",
            "rationale": "Transfer evaluated; AML signals did not exceed block threshold.",
            "evidence": {
                "risk_score": aml_score,
                "violation_category": violation_category or None,
                "harmful_content_flag": harmful_flag,
                "previous_violations": prev_violations,
                "action": action,
                "scheme": scheme,
                "beneficiary_country": beneficiary_country,
            },
        }

    # --- Obligation: Medium-risk transaction monitoring ---
    if article == "FTI:MEDIUM_RISK_TRANSACTION":
        # Applicable to most transaction-like actions.
        is_tx = action in {"INITIATE_TRANSFER", "WIRE_TRANSFER", "CARD_PAYMENT", "PAYMENT", "TRANSFER", "SEND_MONEY"}
        if not is_tx:
            return out

        # Medium band if score in [0.70, 0.90), or prior violations > 0.
        # (This is intentionally permissive: it should tend to MONITOR rather than DENY.)
        score = None
        if isinstance(aml_score, (int, float)):
            score = float(aml_score)
        elif isinstance(fraud_score, (int, float)):
            score = float(fraud_score)

        is_medium = (score is not None and 0.70 <= score < 0.90) or (prev_violations >= 1)

        if is_medium:
            return {
                "status": "VIOLATED",
                "severity": "MEDIUM",
                "trigger_type": "FTI_CONTROL",
                "recommended_outcome": "ESCALATE",
                "rationale": "Transaction is medium risk; monitoring/escalation recommended.",
                "evidence": {
                    "risk_band": "MEDIUM",
                    "risk_score": score,
                    "violation_category": violation_category or None,
                    "previous_violations": prev_violations,
                    "action": action,
                    "scheme": scheme,
                    "beneficiary_country": beneficiary_country,
                },
            }

        return {
            "status": "SATISFIED",
            "severity": "LOW",
            "trigger_type": "FTI_CONTROL",
            "rationale": "Transaction evaluated; no medium/high risk signals detected.",
            "evidence": {
                "risk_score": score,
                "violation_category": violation_category or None,
                "previous_violations": prev_violations,
                "action": action,
                "scheme": scheme,
                "beneficiary_country": beneficiary_country,
            },
        }

    # Unknown article in catalog: treat as NOT_APPLICABLE but keep deterministic shape.
    return out


def resolve(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Kernel entrypoint: return a list of evaluated policy records for this regime."""
    policies: List[Dict[str, Any]] = []
    for ob in obligations():
        overlay = _evaluate_obligation(payload, ob)
        # Merge catalog + overlay, overlay takes precedence.
        policy = dict(ob)
        policy.update(overlay)

        # Defensive: ensure required keys exist (kernel expects these for L3/L4).
        policy.setdefault("regime", "FINTECH_TRANSACTION_INTEGRITY")
        policy.setdefault("domain_id", "FINTECH_TRANSACTION_INTEGRITY")
        policy.setdefault("status", "UNKNOWN")
        policy.setdefault("severity", "LOW")

        policies.append(policy)

    return policies
