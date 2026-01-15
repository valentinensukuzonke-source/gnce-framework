"""
GNCE resolver for FINRA (LIVE WIRED).

- If a native rules engine exists (finra_rules.evaluate_finra_rules), we delegate to it.
- Otherwise, we emit a small set of deterministic obligations based on payload signals.
"""
from __future__ import annotations

from typing import Any, Dict, List


def resolve(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Prefer dedicated rules module when available.
    try:
        from gnce.gn_kernel.rules.finra_rules import evaluate_finra_rules  # type: ignore
        return evaluate_finra_rules(payload)  # pragma: no cover
    except Exception:
        pass

    policies: List[Dict[str, Any]] = []
    ri = payload.get("risk_indicators") or {}
    vc = (ri.get("violation_category") or "")
    vc_norm = str(vc).strip().upper()


    # FINRA_4511_RECORDS
    if vc_norm in ('UNAPPROVED_EXPORT','RECORD_TAMPERING'):
        policies.append(_policy(
            policy_id="FINRA_4511_RECORDS",
            article="FINRA 4511",
            title="FINRA_4511_RECORDS",
            category="FINRA obligation",
            status="VIOLATED",
            severity=_severity_from_control("HIGH"),
            control_severity="HIGH",
            notes="Records export/tampering flagged without approval or controls.",
            evidence=_evidence(payload),
        ))
    else:
        policies.append(_policy(
            policy_id="FINRA_4511_RECORDS",
            article="FINRA 4511",
            title="FINRA_4511_RECORDS",
            category="FINRA obligation",
            status="SATISFIED",
            severity="LOW",
            control_severity="HIGH",
            notes="Not triggered.",
            evidence=_evidence(payload),
        ))

    # FINRA_3110_SUPERVISION
    if vc_norm in ('UNAUTHORIZED_TRADE','MARKET_MANIPULATION') or (ri.get('previous_violations') or 0) >= 2:
        policies.append(_policy(
            policy_id="FINRA_3110_SUPERVISION",
            article="FINRA 3110",
            title="FINRA_3110_SUPERVISION",
            category="FINRA obligation",
            status="VIOLATED",
            severity=_severity_from_control("MEDIUM"),
            control_severity="MEDIUM",
            notes="Supervision concern: suspicious trading/manipulation or repeated violations.",
            evidence=_evidence(payload),
        ))
    else:
        policies.append(_policy(
            policy_id="FINRA_3110_SUPERVISION",
            article="FINRA 3110",
            title="FINRA_3110_SUPERVISION",
            category="FINRA obligation",
            status="SATISFIED",
            severity="LOW",
            control_severity="MEDIUM",
            notes="Not triggered.",
            evidence=_evidence(payload),
        ))


    return policies


def _evidence(payload: Dict[str, Any]) -> Dict[str, Any]:
    ri = payload.get("risk_indicators") or {}
    meta = payload.get("meta") or {}
    return {
        "action": payload.get("action"),
        "industry_id": payload.get("industry_id"),
        "profile_id": payload.get("profile_id"),
        "harmful_content_flag": ri.get("harmful_content_flag"),
        "violation_category": ri.get("violation_category"),
        "previous_violations": ri.get("previous_violations"),
        "jurisdiction": meta.get("jurisdiction"),
    }


def _severity_from_control(control_severity: str) -> str:
    cs = (control_severity or "").upper()
    if cs in ("CRITICAL", "HIGH"):
        return cs
    if cs == "MEDIUM":
        return "MEDIUM"
    return "LOW"


def _policy(
    *,
    policy_id: str,
    article: str,
    title: str,
    category: str,
    status: str,
    severity: str,
    control_severity: str,
    notes: str,
    evidence: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "policy_id": policy_id,
        "domain": "FINRA",
        "regime": "FINRA",
        "framework": "FINRA",
        "domain_id": "FINRA",
        "article": article,
        "category": category,
        "title": title,
        "status": status,
        "severity": severity,
        "control_severity": control_severity,
        "impact_on_verdict": "BLOCK" if status == "VIOLATED" and severity in ("HIGH", "CRITICAL") else "NON_BLOCKING",
        "trigger_type": "FINRA_OBLIGATION",
        "rule_ids": [policy_id],
        "notes": notes,
        "remediation": "" if status != "VIOLATED" else "Review and remediate compliance controls.",
        "violation_detail": "" if status != "VIOLATED" else notes,
        "evidence": evidence,
    }
