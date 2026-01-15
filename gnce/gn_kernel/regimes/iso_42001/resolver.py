"""
GNCE resolver for ISO_42001 (LIVE WIRED).

- If a native rules engine exists (iso_42001_rules.evaluate_iso_42001_rules), we delegate to it.
- Otherwise, we emit a small set of deterministic obligations based on payload signals.
"""
from __future__ import annotations

from typing import Any, Dict, List


def resolve(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Prefer dedicated rules module when available.
    try:
        from gnce.gn_kernel.rules.iso_42001_rules import evaluate_iso_42001_rules  # type: ignore
        return evaluate_iso_42001_rules(payload)  # pragma: no cover
    except Exception:
        pass

    policies: List[Dict[str, Any]] = []
    ri = payload.get("risk_indicators") or {}
    vc = (ri.get("violation_category") or "")
    vc_norm = str(vc).strip().upper()


    # ISO_42001_5_1_GOVERNANCE
    if bool((payload.get('ai_profile') or {}).get('is_ai_system')) and not bool((payload.get('ai_profile') or {}).get('governance_controls')):
        policies.append(_policy(
            policy_id="ISO_42001_5_1_GOVERNANCE",
            article="ISO/IEC 42001 5.1",
            title="ISO_42001_5_1_GOVERNANCE",
            category="ISO_42001 obligation",
            status="VIOLATED",
            severity=_severity_from_control("MEDIUM"),
            control_severity="MEDIUM",
            notes="AI system indicated but governance_controls missing/false.",
            evidence=_evidence(payload),
        ))
    else:
        policies.append(_policy(
            policy_id="ISO_42001_5_1_GOVERNANCE",
            article="ISO/IEC 42001 5.1",
            title="ISO_42001_5_1_GOVERNANCE",
            category="ISO_42001 obligation",
            status="SATISFIED",
            severity="LOW",
            control_severity="MEDIUM",
            notes="Not triggered.",
            evidence=_evidence(payload),
        ))

    # ISO_42001_8_2_RISK_TREATMENT
    if bool((payload.get('ai_profile') or {}).get('is_ai_system')) and bool(ri.get('harmful_content_flag')):
        policies.append(_policy(
            policy_id="ISO_42001_8_2_RISK_TREATMENT",
            article="ISO/IEC 42001 8.2",
            title="ISO_42001_8_2_RISK_TREATMENT",
            category="ISO_42001 obligation",
            status="VIOLATED",
            severity=_severity_from_control("MEDIUM"),
            control_severity="MEDIUM",
            notes="AI system indicated and harmful_content_flag=true; risk treatment controls required.",
            evidence=_evidence(payload),
        ))
    else:
        policies.append(_policy(
            policy_id="ISO_42001_8_2_RISK_TREATMENT",
            article="ISO/IEC 42001 8.2",
            title="ISO_42001_8_2_RISK_TREATMENT",
            category="ISO_42001 obligation",
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
        "domain": "ISO_42001",
        "regime": "ISO_42001",
        "framework": "ISO_42001",
        "domain_id": "ISO_42001",
        "article": article,
        "category": category,
        "title": title,
        "status": status,
        "severity": severity,
        "control_severity": control_severity,
        "impact_on_verdict": "BLOCK" if status == "VIOLATED" and severity in ("HIGH", "CRITICAL") else "NON_BLOCKING",
        "trigger_type": "ISO_42001_OBLIGATION",
        "rule_ids": [policy_id],
        "notes": notes,
        "remediation": "" if status != "VIOLATED" else "Review and remediate compliance controls.",
        "violation_detail": "" if status != "VIOLATED" else notes,
        "evidence": evidence,
    }
