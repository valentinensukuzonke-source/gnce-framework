"""gnce/gn_kernel/regimes/hipaa/resolver.py

HIPAA executable regime resolver.

Goal:
- Produce deterministic L4 policy obligations for HIPAA Privacy/Security surfaces.
- DENY on clear unauthorized PHI access/export signals (especially when caller flags harmful/unauthorized).
- Stay backwards-compatible with the kernel's executable-regime plumbing:
  resolver(payload) -> list[dict]
"""

from __future__ import annotations

from typing import Any, Dict, List


def _canon(x: Any) -> str:
    return str(x or "").strip().upper().replace(" ", "_").replace("-", "_")


def resolve(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    payload = payload or {}
    meta = payload.get("meta") or {}
    ri = payload.get("risk_indicators") or {}

    action = _canon(payload.get("action"))
    industry = _canon(payload.get("industry_id"))
    jurisdiction = _canon(meta.get("jurisdiction"))

    violation_category = str(ri.get("violation_category") or "").strip().upper()
    harmful_flag = bool(ri.get("harmful_content_flag"))

    record_access = payload.get("record_access") or {}
    export = payload.get("export") or {}

    # Infer whether PHI is in-scope. If callers provide hipaa_profile, respect it;
    # otherwise infer from healthcare industry + healthcare-shaped actions.
    hipaa_profile = payload.get("hipaa_profile") or {}
    handles_phi = hipaa_profile.get("handles_phi")
    if handles_phi is None:
        handles_phi = bool(industry == "HEALTHCARE" or action in {"ACCESS_RECORD", "EXPORT_DATA"} or record_access or export)

    # --- Primary blocking condition: unauthorized access / disclosure of PHI
    # We treat explicit caller flags as authoritative signals.
    unauthorized_access = violation_category in {"UNAUTHORIZED_ACCESS", "PHI_UNAUTHORIZED_ACCESS", "UNAUTHORIZED_PHI_ACCESS"}
    noncompliant_export = violation_category in {"DATA_EXPORT_NONCOMPLIANT", "PHI_EXPORT_NONCOMPLIANT", "UNLAWFUL_EXPORT"}

    # Additional heuristic: ACCESS_RECORD with no break-glass + unknown reason + harmful flag
    if action == "ACCESS_RECORD" and harmful_flag:
        reason = _canon(record_access.get("reason"))
        break_glass = bool(record_access.get("break_glass"))
        if (not break_glass) and (reason in {"", "UNKNOWN", "N/A"}):
            unauthorized_access = True

    # Additional heuristic: EXPORT_DATA with lawful_basis NONE/empty
    if action == "EXPORT_DATA":
        lawful_basis = _canon(export.get("lawful_basis"))
        if lawful_basis in {"", "NONE", "NULL", "N/A"}:
            # don't overreach for non-healthcare; but for PHI we treat as noncompliant
            if handles_phi:
                noncompliant_export = True

    policies: List[Dict[str, Any]] = []

    def emit(
        article: str,
        rule_id: str,
        title: str,
        category: str,
        status: str,
        severity: str,
        control_severity: str,
        why: str,
        impact_on_verdict: str,
    ) -> None:
        policies.append(
            {
                "policy_id": rule_id,
                "article": article,
                "title": title,
                "category": category,
                "status": status,
                "severity": severity,
                "control_severity": control_severity,
                "trigger_type": "HIPAA_OBLIGATION",
                "impact_on_verdict": impact_on_verdict,
                "notes": why,
                "rule_ids": [rule_id],
                # evidence is intentionally small+deterministic
                "evidence": {
                    "action": action,
                    "jurisdiction": jurisdiction,
                    "handles_phi": bool(handles_phi),
                    "harmful_content_flag": harmful_flag,
                    "violation_category": violation_category,
                    "previous_violations": ri.get("previous_violations"),
                    "break_glass": record_access.get("break_glass"),
                    "lawful_basis": export.get("lawful_basis"),
                },
                "remediation": "",
                "violation_detail": "",
            }
        )

    # If not applicable, emit a single NA surface so trace remains explicit.
    if not (jurisdiction == "US" and handles_phi):
        emit(
            article="HIPAA Applicability",
            rule_id="HIPAA_APPLICABILITY_NA",
            title="HIPAA applicability",
            category="Applicability",
            status="NOT_APPLICABLE",
            severity="LOW",
            control_severity="LOW",
            why="Not applicable: HIPAA applies to US PHI handling contexts.",
            impact_on_verdict="Neutral non-applicable surface.",
        )
        return policies

    # --- Blocking violations (map to core HIPAA technical safeguards / privacy limits)
    if unauthorized_access:
        emit(
            article="45 CFR §164.312(a)",
            rule_id="HIPAA_164_312_ACCESS_CONTROL",
            title="Access control",
            category="Access control",
            status="VIOLATED",
            severity="CRITICAL",
            control_severity="HIGH",
            why="Unauthorized access signal present (violation_category=UNAUTHORIZED_ACCESS or equivalent).",
            impact_on_verdict="BLOCKING",
        )
    else:
        emit(
            article="45 CFR §164.312(a)",
            rule_id="HIPAA_164_312_ACCESS_CONTROL",
            title="Access control",
            category="Access control",
            status="SATISFIED",
            severity="LOW",
            control_severity="HIGH",
            why="Not triggered: PHI must be protected by technical access controls.",
            impact_on_verdict="NON_BLOCKING",
        )

    if noncompliant_export:
        emit(
            article="45 CFR §164.502(b)",
            rule_id="HIPAA_164_502_MIN_NECESSARY",
            title="Minimum necessary standard",
            category="Minimum necessary standard",
            status="VIOLATED",
            severity="HIGH",
            control_severity="HIGH",
            why="Noncompliant PHI export signal present (no lawful basis / DATA_EXPORT_NONCOMPLIANT).",
            impact_on_verdict="BLOCKING",
        )
    else:
        emit(
            article="45 CFR §164.502(b)",
            rule_id="HIPAA_164_502_MIN_NECESSARY",
            title="Minimum necessary standard",
            category="Minimum necessary standard",
            status="SATISFIED",
            severity="LOW",
            control_severity="HIGH",
            why="Not triggered: Use/disclosure of PHI must be limited to the minimum necessary.",
            impact_on_verdict="NON_BLOCKING",
        )

    # Audit controls are important; treat as blocking only when caller flags a breach-ish condition.
    if harmful_flag and unauthorized_access:
        emit(
            article="45 CFR §164.312(b)",
            rule_id="HIPAA_164_312_AUDIT_LOGS",
            title="Audit controls",
            category="Audit controls",
            status="VIOLATED",
            severity="HIGH",
            control_severity="MEDIUM",
            why="Unauthorized access flagged; auditability must be enforced.",
            impact_on_verdict="BLOCKING",
        )
    else:
        emit(
            article="45 CFR §164.312(b)",
            rule_id="HIPAA_164_312_AUDIT_LOGS",
            title="Audit controls",
            category="Audit controls",
            status="SATISFIED",
            severity="LOW",
            control_severity="MEDIUM",
            why="Not triggered: Systems must record and examine activity involving PHI.",
            impact_on_verdict="NON_BLOCKING",
        )

    # Breach notification is typically procedural; surface as SATISFIED unless explicitly breached.
    emit(
        article="45 CFR §164.404",
        rule_id="HIPAA_164_404_BREACH_NOTIFICATION",
        title="Breach notification",
        category="Breach notification",
        status="SATISFIED",
        severity="LOW",
        control_severity="CRITICAL",
        why="Not triggered: Covered entities must notify individuals of PHI breaches when a breach is confirmed.",
        impact_on_verdict="NON_BLOCKING",
    )

    return policies


# Backwards-compatible alias (some regimes import obligations()).
def obligations(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    return resolve(payload)
