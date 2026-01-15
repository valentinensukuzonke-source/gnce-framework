"""
GNCE resolver for BSA_AML (LIVE WIRED).

- If a native rules engine exists (bsa_aml_rules.evaluate_bsa_aml_rules), we delegate to it.
- Otherwise, we emit a small set of deterministic obligations based on payload signals.
"""
from __future__ import annotations

from typing import Any, Dict, List


def resolve(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Prefer dedicated rules module when available.
    try:
        from gnce.gn_kernel.rules.bsa_aml_rules import evaluate_bsa_aml_rules  # type: ignore
        return evaluate_bsa_aml_rules(payload)  # pragma: no cover
    except Exception:
        pass

    policies: List[Dict[str, Any]] = []
    ri = payload.get("risk_indicators") or {}
    vc = (ri.get("violation_category") or "")
    vc_norm = str(vc).strip().upper()


    # BSA_AML_SAR_FILING
    if vc_norm in ('SUSPICIOUS_ACTIVITY','MONEY_LAUNDERING','SANCTIONS_EVASION'):
        policies.append(_policy(
            policy_id="BSA_AML_SAR_FILING",
            article="31 CFR 1020.320",
            title="BSA_AML_SAR_FILING",
            category="BSA_AML obligation",
            status="VIOLATED",
            severity=_severity_from_control("HIGH"),
            control_severity="HIGH",
            notes="Suspicious activity flagged; SAR/controls required.",
            evidence=_evidence(payload),
        ))
    else:
        policies.append(_policy(
            policy_id="BSA_AML_SAR_FILING",
            article="31 CFR 1020.320",
            title="BSA_AML_SAR_FILING",
            category="BSA_AML obligation",
            status="SATISFIED",
            severity="LOW",
            control_severity="HIGH",
            notes="Not triggered.",
            evidence=_evidence(payload),
        ))

    # BSA_AML_KYC_CIP
    if vc_norm in ('KYC_FAILURE','CIP_FAILURE'):
        policies.append(_policy(
            policy_id="BSA_AML_KYC_CIP",
            article="31 CFR 1020.220",
            title="BSA_AML_KYC_CIP",
            category="BSA_AML obligation",
            status="VIOLATED",
            severity=_severity_from_control("MEDIUM"),
            control_severity="MEDIUM",
            notes="Customer identification/KYC failure flagged.",
            evidence=_evidence(payload),
        ))
    else:
        policies.append(_policy(
            policy_id="BSA_AML_KYC_CIP",
            article="31 CFR 1020.220",
            title="BSA_AML_KYC_CIP",
            category="BSA_AML obligation",
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
        "domain": "BSA_AML",
        "regime": "BSA_AML",
        "framework": "BSA_AML",
        "domain_id": "BSA_AML",
        "article": article,
        "category": category,
        "title": title,
        "status": status,
        "severity": severity,
        "control_severity": control_severity,
        "impact_on_verdict": "BLOCK" if status == "VIOLATED" and severity in ("HIGH", "CRITICAL") else "NON_BLOCKING",
        "trigger_type": "BSA_AML_OBLIGATION",
        "rule_ids": [policy_id],
        "notes": notes,
        "remediation": "" if status != "VIOLATED" else "Review and remediate compliance controls.",
        "violation_detail": "" if status != "VIOLATED" else notes,
        "evidence": evidence,
    }
