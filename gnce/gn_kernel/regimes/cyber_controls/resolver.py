"""Resolver for GNCE Cyber Controls Regime.

The resolver is called by kernel.py during `resolve_regimes(...)`.
It should return either:
- a list of policy result dicts, OR
- a dict that contains `policies_triggered` (list) plus any extra metadata.

This implementation returns a dict with:
- policies_triggered: list[dict]
- regime_summary: lightweight counts for dashboards/debugging
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .applicability import is_applicable
from .register import REGIME_ID


@dataclass(frozen=True)
class Policy:
    policy_id: str
    title: str
    domain: str
    severity_on_violation: str
    required_fields: Tuple[str, ...]
    remediation: str


# Curated, high-signal controls (keep it tight; avoid trying to be a security suite).
_POLICIES: List[Policy] = [
    Policy(
        policy_id="CYBER_CTRL_01",
        title="Access request must include subject + resource + permission scope",
        domain="Information Security",
        severity_on_violation="HIGH",
        required_fields=("access.user_id", "access.resource", "access.permission"),
        remediation="Provide user_id, resource identifier, and permission scope before execution.",
    ),
    Policy(
        policy_id="CYBER_CTRL_02",
        title="Sensitive data must be classified before processing",
        domain="Information Security",
        severity_on_violation="HIGH",
        required_fields=("data.classification",),
        remediation="Classify data (PUBLIC/INTERNAL/CONFIDENTIAL/SECRET/TOP_SECRET) before processing.",
    ),
    Policy(
        policy_id="CYBER_CTRL_03",
        title="Key operations must declare storage + rotation policy",
        domain="Cloud Security",
        severity_on_violation="CRITICAL",
        required_fields=("keys.storage", "keys.rotation_days"),
        remediation="Declare secure key storage (e.g., HSM) and rotation cadence before key operation executes.",
    ),
    Policy(
        policy_id="CYBER_CTRL_04",
        title="Deployment/config changes require change ticket or approved automation ID",
        domain="Security Management",
        severity_on_violation="HIGH",
        required_fields=("change.change_id",),
        remediation="Attach change_id (or automation approval ID) to config/deploy action for traceability.",
    ),
    Policy(
        policy_id="CYBER_CTRL_05",
        title="Incident actions must declare incident ID + escalation route",
        domain="Incident Management",
        severity_on_violation="HIGH",
        required_fields=("incident.incident_id", "incident.escalation"),
        remediation="Provide incident_id and escalation path for incident actions (containment/notification).",
    ),
    Policy(
        policy_id="CYBER_CTRL_06",
        title="Network access changes must provide allow/deny intent and target selector",
        domain="Network Security",
        severity_on_violation="HIGH",
        required_fields=("network.intent", "network.target"),
        remediation="Provide network intent (allow/deny) and target selector (CIDR/service/tag) before execution.",
    ),
]


def _get_nested(payload: Dict[str, Any], path: str) -> Optional[Any]:
    """Get nested field using dot paths like 'access.user_id'."""
    cur: Any = payload
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        if part not in cur:
            return None
        cur = cur.get(part)
    return cur


def _mk_result(
    policy: Policy,
    status: str,
    evidence: Dict[str, Any],
    notes: str,
    violation_detail: str = "",
) -> Dict[str, Any]:
    severity = "LOW"
    impact = "Control satisfied."
    remediation = ""

    if status == "VIOLATED":
        severity = policy.severity_on_violation
        impact = "Control violated; action should be vetoed or escalated based on severity."
        remediation = policy.remediation

    if status == "NOT_APPLICABLE":
        severity = "LOW"
        impact = "Control not applicable to this action."
        remediation = ""

    return {
        "regime": REGIME_ID,
        "domain": policy.domain,
        "framework": "GNCE",
        "policy_id": policy.policy_id,
        "title": policy.title,
        "status": status,  # SATISFIED | VIOLATED | NOT_APPLICABLE | ERROR
        "severity": severity,
        "impact_on_verdict": impact,
        "notes": notes,
        "rule_ids": [policy.policy_id],
        "evidence": evidence,
        "remediation": remediation,
        "violation_detail": violation_detail,
    }


def resolve(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve cyber control obligations for a given payload."""
    applicable, reason = is_applicable(payload)
    ts = datetime.now(timezone.utc).isoformat()

    if not applicable:
        return {
            "regime_id": REGIME_ID,
            "applicable": False,
            "applicability_reason": reason,
            "resolved_at_utc": ts,
            "policies_triggered": [
                {
                    "regime": REGIME_ID,
                    "domain": "Cyber Controls",
                    "framework": "GNCE",
                    "policy_id": "CYBER_CTRL_NA",
                    "title": "Cyber Controls Regime Not Applicable",
                    "status": "NOT_APPLICABLE",
                    "severity": "LOW",
                    "impact_on_verdict": "No cyber control evaluation required for this action.",
                    "notes": f"not_applicable:{reason}",
                    "rule_ids": ["CYBER_CTRL_NA"],
                    "evidence": {"reason": reason},
                    "remediation": "",
                    "violation_detail": "",
                }
            ],
            "regime_summary": {
                "total": 1,
                "passed": 0,
                "failed": 0,
                "blocking_failures": 0,
            },
        }

    results: List[Dict[str, Any]] = []
    blocking = 0
    failed = 0
    passed = 0

    for pol in _POLICIES:
        missing: List[str] = []
        evidence: Dict[str, Any] = {"required_fields": list(pol.required_fields), "present": {}}

        for field in pol.required_fields:
            val = _get_nested(payload, field)
            present = val is not None and val != ""
            evidence["present"][field] = bool(present)
            if not present:
                missing.append(field)

        # Light applicability per-policy: only run if the action/context touches that namespace.
        # (Example: if no 'keys' section exists, treat key-policy as NOT_APPLICABLE.)
        namespace = pol.required_fields[0].split(".", 1)[0]
        if namespace not in payload:
            status = "NOT_APPLICABLE"
            results.append(
                _mk_result(
                    pol,
                    status=status,
                    evidence={"namespace": namespace, "reason": "namespace_absent"},
                    notes="Skipping control because relevant payload section is absent.",
                )
            )
            continue

        if missing:
            status = "VIOLATED"
            failed += 1
            if pol.severity_on_violation in {"HIGH", "CRITICAL"}:
                blocking += 1
            results.append(
                _mk_result(
                    pol,
                    status=status,
                    evidence=evidence,
                    notes="Missing required control fields.",
                    violation_detail=f"missing_fields:{', '.join(missing)}",
                )
            )
        else:
            status = "SATISFIED"
            passed += 1
            results.append(
                _mk_result(
                    pol,
                    status=status,
                    evidence=evidence,
                    notes="Required control fields present.",
                )
            )

    return {
        "regime_id": REGIME_ID,
        "applicable": True,
        "applicability_reason": reason,
        "resolved_at_utc": ts,
        "policies_triggered": results,
        "regime_summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "blocking_failures": blocking,
        },
    }
