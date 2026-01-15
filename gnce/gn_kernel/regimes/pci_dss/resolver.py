"""
GNCE resolver for PCI_DSS (LIVE WIRED).

- If a native rules engine exists (pci_dss_rules.evaluate_pci_dss_rules), we delegate to it.
- Otherwise, we emit a small set of deterministic obligations based on payload signals.
"""
from __future__ import annotations

from typing import Any, Dict, List


def resolve(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Prefer dedicated rules module when available.
    try:
        from gnce.gn_kernel.rules.pci_dss_rules import evaluate_pci_dss_rules  # type: ignore
        return evaluate_pci_dss_rules(payload)  # pragma: no cover
    except Exception:
        pass

    policies: List[Dict[str, Any]] = []
    ri = payload.get("risk_indicators") or {}
    vc = (ri.get("violation_category") or "")
    vc_norm = str(vc).strip().upper()


    # PCI_DSS_3_4_PROTECT_STORED_CHD
    if vc_norm in ('CARD_DATA_EXFIL','PCI_NONCOMPLIANT') or (payload.get('export') or {}).get('data_class') in ('CARDHOLDER','PAYMENT'):
        policies.append(_policy(
            policy_id="PCI_DSS_3_4_PROTECT_STORED_CHD",
            article="PCI DSS 3.4",
            title="PCI_DSS_3_4_PROTECT_STORED_CHD",
            category="PCI_DSS obligation",
            status="VIOLATED",
            severity=_severity_from_control("HIGH"),
            control_severity="HIGH",
            notes="Cardholder/payment data indicated without compliant protections.",
            evidence=_evidence(payload),
        ))
    else:
        policies.append(_policy(
            policy_id="PCI_DSS_3_4_PROTECT_STORED_CHD",
            article="PCI DSS 3.4",
            title="PCI_DSS_3_4_PROTECT_STORED_CHD",
            category="PCI_DSS obligation",
            status="SATISFIED",
            severity="LOW",
            control_severity="HIGH",
            notes="Not triggered.",
            evidence=_evidence(payload),
        ))

    # PCI_DSS_7_1_ACCESS_CONTROL
    if vc_norm in ('UNAUTHORIZED_ACCESS','UNAUTHORIZED_EXPORT') and (payload.get('payment') is not None or (payload.get('export') or {}).get('data_class') in ('CARDHOLDER','PAYMENT')):
        policies.append(_policy(
            policy_id="PCI_DSS_7_1_ACCESS_CONTROL",
            article="PCI DSS 7.1",
            title="PCI_DSS_7_1_ACCESS_CONTROL",
            category="PCI_DSS obligation",
            status="VIOLATED",
            severity=_severity_from_control("HIGH"),
            control_severity="HIGH",
            notes="Unauthorized access/export involving payment data.",
            evidence=_evidence(payload),
        ))
    else:
        policies.append(_policy(
            policy_id="PCI_DSS_7_1_ACCESS_CONTROL",
            article="PCI DSS 7.1",
            title="PCI_DSS_7_1_ACCESS_CONTROL",
            category="PCI_DSS obligation",
            status="SATISFIED",
            severity="LOW",
            control_severity="HIGH",
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
        "domain": "PCI_DSS",
        "regime": "PCI_DSS",
        "framework": "PCI_DSS",
        "domain_id": "PCI_DSS",
        "article": article,
        "category": category,
        "title": title,
        "status": status,
        "severity": severity,
        "control_severity": control_severity,
        "impact_on_verdict": "BLOCK" if status == "VIOLATED" and severity in ("HIGH", "CRITICAL") else "NON_BLOCKING",
        "trigger_type": "PCI_DSS_OBLIGATION",
        "rule_ids": [policy_id],
        "notes": notes,
        "remediation": "" if status != "VIOLATED" else "Review and remediate compliance controls.",
        "violation_detail": "" if status != "VIOLATED" else notes,
        "evidence": evidence,
    }
