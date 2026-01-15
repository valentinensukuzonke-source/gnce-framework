# gnce/gn_kernel/regimes/sec_17A4/resolver.py
from __future__ import annotations
from typing import Any, Dict, List


def _sec(payload: Dict[str, Any]) -> Dict[str, Any]:
    prof = payload.get("sec_17a4_profile") or {}
    return prof if isinstance(prof, dict) else {}


def resolve(payload: Dict[str, Any]) -> Dict[str, Any]:
    prof = _sec(payload)

    # If not a broker-dealer, emit nothing (kernel will treat as not run / not applicable)
    if not bool(prof.get("broker_dealer")):
        return {"policies_triggered": []}

    policies: List[Dict[str, Any]] = []

    def add(
        *,
        article: str,
        title: str,
        rule_id: str,
        status: str,
        severity: str,
        notes: str,
        remediation: str,
        evidence: Dict[str, Any],
    ) -> None:
        policies.append(
            {
                "regime": "SEC_17A4",
                "domain": "SEC Rule 17a-4 (Books and Records)",
                "framework": "Financial / Markets Compliance",
                "domain_id": "SEC_17A4",
                "article": article,
                "category": title,
                "title": title,
                "policy_id": rule_id,
                "rule_ids": [rule_id],
                "status": status,     # ✅ SATISFIED / VIOLATED / NOT_APPLICABLE
                "severity": severity, # ✅ LOW / MEDIUM / HIGH / CRITICAL
                "control_severity": severity,
                "trigger_type": "SEC_17A4_OBLIGATION",
                "notes": notes,
                "violation_detail": notes if status == "VIOLATED" else "",
                "impact_on_verdict": "BLOCKING_FAILURE" if (status == "VIOLATED" and severity in {"HIGH", "CRITICAL"}) else ("NON_BLOCKING" if status == "VIOLATED" else "Compliant under tested SEC 17a-4 obligations."),
                "remediation": remediation if status == "VIOLATED" else "No remediation required.",
                "evidence": evidence,
            }
        )

    # Evidence helper (keep it tight + audit-grade)
    base_ev = {
        "sec_17a4_profile.broker_dealer": bool(prof.get("broker_dealer")),
        "sec_17a4_profile.records_retained": prof.get("records_retained", None),
        "sec_17a4_profile.worm_storage": prof.get("worm_storage", None),
        "sec_17a4_profile.indexed_search": prof.get("indexed_search", None),
        "sec_17a4_profile.regulator_access": prof.get("regulator_access", None),
    }

    # 17a-4(b) — retention
    rr = prof.get("records_retained", None)
    if rr is None:
        add(
            article="17a-4(b)",
            title="Records retention program",
            rule_id="SEC_17A4_RETENTION_PROGRAM",
            status="NOT_APPLICABLE",
            severity="LOW",
            notes="Not assessed: records_retained not provided.",
            remediation="",
            evidence={k: base_ev[k] for k in ["sec_17a4_profile.broker_dealer", "sec_17a4_profile.records_retained"]},
        )
    elif rr is True:
        add(
            article="17a-4(b)",
            title="Records retention program",
            rule_id="SEC_17A4_RETENTION_PROGRAM",
            status="SATISFIED",
            severity="LOW",
            notes="Records retention indicated.",
            remediation="",
            evidence={k: base_ev[k] for k in ["sec_17a4_profile.broker_dealer", "sec_17a4_profile.records_retained"]},
        )
    else:
        add(
            article="17a-4(b)",
            title="Records retention program",
            rule_id="SEC_17A4_RETENTION_PROGRAM",
            status="VIOLATED",
            severity="HIGH",
            notes="Broker-dealers must retain required records under SEC 17a-4.",
            remediation="Implement retention schedules, supervisory procedures, and audit logging for required records; re-run GNCE after mitigation.",
            evidence={k: base_ev[k] for k in ["sec_17a4_profile.broker_dealer", "sec_17a4_profile.records_retained"]},
        )

    # 17a-4(f) — WORM
    worm = prof.get("worm_storage", None)
    if worm is None:
        add(
            article="17a-4(f)",
            title="WORM storage (non-rewriteable / non-erasable)",
            rule_id="SEC_17A4_WORM_STORAGE",
            status="NOT_APPLICABLE",
            severity="LOW",
            notes="Not assessed: worm_storage not provided.",
            remediation="",
            evidence={k: base_ev[k] for k in ["sec_17a4_profile.worm_storage"]},
        )
    elif worm is True:
        add(
            article="17a-4(f)",
            title="WORM storage (non-rewriteable / non-erasable)",
            rule_id="SEC_17A4_WORM_STORAGE",
            status="SATISFIED",
            severity="LOW",
            notes="WORM storage indicated.",
            remediation="",
            evidence={k: base_ev[k] for k in ["sec_17a4_profile.worm_storage"]},
        )
    else:
        add(
            article="17a-4(f)",
            title="WORM storage (non-rewriteable / non-erasable)",
            rule_id="SEC_17A4_WORM_STORAGE",
            status="VIOLATED",
            severity="CRITICAL",
            notes="Records must be preserved in a non-rewriteable, non-erasable format (WORM) when required.",
            remediation="Move record storage to compliant WORM media / immutable storage controls; validate retention + immutability; re-run GNCE.",
            evidence={k: base_ev[k] for k in ["sec_17a4_profile.worm_storage"]},
        )

    # 17a-4(f)(2)(ii) — indexing / searchability
    idx = prof.get("indexed_search", None)
    if idx is None:
        add(
            article="17a-4(f)(2)(ii)",
            title="Indexing / searchable records",
            rule_id="SEC_17A4_INDEXING",
            status="NOT_APPLICABLE",
            severity="LOW",
            notes="Not assessed: indexed_search not provided.",
            remediation="",
            evidence={k: base_ev[k] for k in ["sec_17a4_profile.indexed_search"]},
        )
    elif idx is True:
        add(
            article="17a-4(f)(2)(ii)",
            title="Indexing / searchable records",
            rule_id="SEC_17A4_INDEXING",
            status="SATISFIED",
            severity="LOW",
            notes="Indexing/search indicated.",
            remediation="",
            evidence={k: base_ev[k] for k in ["sec_17a4_profile.indexed_search"]},
        )
    else:
        add(
            article="17a-4(f)(2)(ii)",
            title="Indexing / searchable records",
            rule_id="SEC_17A4_INDEXING",
            status="VIOLATED",
            severity="MEDIUM",
            notes="Records must be indexed / searchable to support timely retrieval.",
            remediation="Implement indexing and retrieval workflows; test search across retained records; re-run GNCE.",
            evidence={k: base_ev[k] for k in ["sec_17a4_profile.indexed_search"]},
        )

    # 17a-4(f)(3)(v) — regulator access / download
    ra = prof.get("regulator_access", None)
    if ra is None:
        add(
            article="17a-4(f)(3)(v)",
            title="Regulator access and export",
            rule_id="SEC_17A4_REGULATOR_ACCESS",
            status="NOT_APPLICABLE",
            severity="LOW",
            notes="Not assessed: regulator_access not provided.",
            remediation="",
            evidence={k: base_ev[k] for k in ["sec_17a4_profile.regulator_access"]},
        )
    elif ra is True:
        add(
            article="17a-4(f)(3)(v)",
            title="Regulator access and export",
            rule_id="SEC_17A4_REGULATOR_ACCESS",
            status="SATISFIED",
            severity="LOW",
            notes="Regulator access indicated.",
            remediation="",
            evidence={k: base_ev[k] for k in ["sec_17a4_profile.regulator_access"]},
        )
    else:
        add(
            article="17a-4(f)(3)(v)",
            title="Regulator access and export",
            rule_id="SEC_17A4_REGULATOR_ACCESS",
            status="VIOLATED",
            severity="HIGH",
            notes="Regulators must be able to promptly access and export required records.",
            remediation="Enable regulator access/export capabilities and audit the process; ensure least-privilege + logging; re-run GNCE.",
            evidence={k: base_ev[k] for k in ["sec_17a4_profile.regulator_access"]},
        )

    return {"policies_triggered": policies}
