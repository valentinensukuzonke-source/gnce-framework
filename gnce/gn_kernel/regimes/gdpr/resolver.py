"""
gnce/gn_kernel/regimes/gdpr/resolver.py

GDPR resolver (live-wired).

Design
- The kernel’s executable-regime runner expects a callable resolver.
- We emit a small set of obligations that can BLOCK when violated.
- We only encode *clear, payload-derived* violations to avoid false legal claims.

What this catches (high signal)
- EXPORT_DATA with export.lawful_basis == "NONE" (or missing) => GDPR Art. 6 violation.
- Risk indicator categories that signal unlawful export/access can also trigger Art. 6 as a proxy.
"""

from __future__ import annotations

from typing import Any, Dict, List


def _upper(x: Any) -> str:
    return str(x or "").strip().upper().replace(" ", "_").replace("-", "_")


def _meta(payload: Dict[str, Any]) -> Dict[str, Any]:
    return (payload.get("meta") or {})


def _risk(payload: Dict[str, Any]) -> Dict[str, Any]:
    return (payload.get("risk_indicators") or {})


def _export(payload: Dict[str, Any]) -> Dict[str, Any]:
    return (payload.get("export") or {})


def _is_gdpr_surface(payload: Dict[str, Any]) -> bool:
    j = _upper(_meta(payload).get("jurisdiction"))
    if j in {"EU", "UK"}:
        return True
    # Heuristic: GDPR-like signals in risk category + export.
    vc = _upper(_risk(payload).get("violation_category"))
    if vc in {"DATA_EXPORT_NONCOMPLIANT", "UNAPPROVED_EXPORT"}:
        return True
    if _upper(payload.get("action")) == "EXPORT_DATA" and bool(_export(payload)):
        return True
    return False


def _policy(
    *,
    article: str,
    title: str,
    category: str,
    status: str,
    severity: str,
    control_severity: str,
    notes: str,
    evidence: Dict[str, Any],
    remediation: str = "",
    violation_detail: str = "",
) -> Dict[str, Any]:
    return {
        "domain": "GDPR",
        "regime": "GDPR",
        "framework": "EU Privacy & Data Protection",
        "domain_id": "GDPR",
        "article": article,
        "category": category,
        "title": title,
        "status": status,
        "severity": severity,
        "control_severity": control_severity,
        "impact_on_verdict": "BLOCKING" if status in {"VIOLATED", "BLOCK"} and control_severity in {"HIGH", "CRITICAL"} else "NON_BLOCKING",
        "trigger_type": "GDPR_OBLIGATION",
        "rule_ids": [],
        "notes": notes,
        "evidence": evidence,
        "remediation": remediation,
        "violation_detail": violation_detail,
    }


def resolve(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Evaluate GDPR obligations for this payload and return `policies_triggered` records.
    """
    payload = payload or {}
    action = _upper(payload.get("action"))
    risk = _risk(payload)
    vc = _upper(risk.get("violation_category"))
    exp = _export(payload)
    lawful_basis = _upper(exp.get("lawful_basis"))

    if not _is_gdpr_surface(payload):
        return [
            _policy(
                article="GDPR:APPLICABILITY",
                title="GDPR applicability",
                category="Applicability",
                status="NOT_APPLICABLE",
                severity="LOW",
                control_severity="LOW",
                notes="No EU/UK jurisdiction or GDPR-linked indicators detected for this payload.",
                evidence={"action": action, "jurisdiction": _upper(_meta(payload).get("jurisdiction"))},
            )
        ]

    policies: List[Dict[str, Any]] = []

    # GDPR Art. 6 — Lawfulness of processing (proxy for lawful basis on export/access actions)
    art6_violation = False
    reasons: List[str] = []

    if action == "EXPORT_DATA":
        # Prefer explicit lawful basis field if present.
        if lawful_basis in {"", "NONE", "NULL"}:
            art6_violation = True
            reasons.append(f"export.lawful_basis={exp.get('lawful_basis')!r}")

        # Risk indicators can override.
        if vc in {"DATA_EXPORT_NONCOMPLIANT", "UNAPPROVED_EXPORT"}:
            art6_violation = True
            reasons.append(f"violation_category={risk.get('violation_category')!r}")

    # If the caller flags unauthorized access, we still surface Art. 6 as a privacy-law proxy
    # (the system may later introduce a dedicated access-control regime for EU health data).
    if action == "ACCESS_RECORD" and vc == "UNAUTHORIZED_ACCESS":
        art6_violation = True
        reasons.append("unauthorized access flagged")

    if art6_violation:
        policies.append(
            _policy(
                article="GDPR Art. 6",
                title="Lawfulness of processing",
                category="Lawful basis",
                status="VIOLATED",
                severity="HIGH",
                control_severity="HIGH",
                notes="Processing/export appears to lack a lawful basis (or is flagged as non-compliant).",
                evidence={
                    "action": action,
                    "violation_category": risk.get("violation_category"),
                    "export.lawful_basis": exp.get("lawful_basis"),
                    "reasons": reasons,
                },
                remediation="Provide and validate a lawful basis before processing/export; require approval workflow for exports.",
                violation_detail="; ".join(reasons),
            )
        )
    else:
        policies.append(
            _policy(
                article="GDPR Art. 6",
                title="Lawfulness of processing",
                category="Lawful basis",
                status="SATISFIED",
                severity="LOW",
                control_severity="HIGH",
                notes="No unlawful processing indicator detected for this payload.",
                evidence={
                    "action": action,
                    "violation_category": risk.get("violation_category"),
                    "export.lawful_basis": exp.get("lawful_basis"),
                },
                remediation="",
            )
        )

    return policies


__all__ = ["resolve"]
