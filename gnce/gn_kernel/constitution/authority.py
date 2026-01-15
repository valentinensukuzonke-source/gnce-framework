#gnce/kernel/constitution/authority.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple, Optional


# -----------------------------
# Helpers
# -----------------------------

_SEV_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
_SEV_FROM_SCORE = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_int(x: Any, default: int = 1) -> int:
    try:
        return int(x)
    except Exception:
        return default


def _norm_status(raw: Any) -> str:
    s = str(raw or "").strip().upper()
    if s in {"VIOLATED", "SATISFIED", "NOT_APPLICABLE"}:
        return s
    if s in {"N/A", "NA"}:
        return "NOT_APPLICABLE"
    return "UNKNOWN"


def _norm_severity(p: Dict[str, Any]) -> Tuple[int, str]:
    """
    Accepts either:
      - severity_score (1-4)
      - severity (1-4 or LOW/MEDIUM/HIGH/CRITICAL)
      - severity_level (LOW/MEDIUM/HIGH/CRITICAL)
    Returns: (severity_score, severity_level)
    """
    if isinstance(p.get("severity_score"), (int, float, str)):
        score = _as_int(p.get("severity_score"), 1)
        score = min(max(score, 1), 4)
        return score, _SEV_FROM_SCORE.get(score, "LOW")

    if isinstance(p.get("severity"), (int, float, str)):
        sev = p.get("severity")
        if isinstance(sev, (int, float)) or (isinstance(sev, str) and sev.strip().isdigit()):
            score = min(max(_as_int(sev, 1), 1), 4)
            return score, _SEV_FROM_SCORE.get(score, "LOW")
        s = str(sev).strip().upper()
        if s in _SEV_ORDER:
            return _SEV_ORDER[s], s

    s2 = str(p.get("severity_level") or "").strip().upper()
    if s2 in _SEV_ORDER:
        return _SEV_ORDER[s2], s2

    return 1, "LOW"


def _policy_label(p: Dict[str, Any]) -> str:
    regime = p.get("regime") or p.get("domain") or "REGIME"
    article = p.get("article") or "Article"
    status = _norm_status(p.get("status") or p.get("verdict"))
    _, sev = _norm_severity(p)
    impact = (p.get("impact_on_verdict") or p.get("rationale") or "").strip()
    tail = f": {impact}" if impact else ""
    return f"{regime} — {article} ({status} / {sev}){tail}"


def _recommended_action_from_policy(p: Dict[str, Any]) -> Optional[str]:
    r = p.get("remediation")
    if isinstance(r, str) and r.strip():
        return r.strip()
    return None




# -----------------------------
# Enforcement scope gate (v0.7.x)
# -----------------------------

# Only these severities may block execution when enforcement_scope == TRANSACTION.
_SEVERITY_BLOCKING = {"HIGH", "CRITICAL"}

def _norm_scope(raw: Any) -> str:
    s = str(raw or "").strip().upper()
    return s if s else "TRANSACTION"

def _is_transaction_blocking(p: Dict[str, Any]) -> bool:
    """
    Migration-safe enforcement gate.

    Defaults:
      - Missing enforcement_scope => TRANSACTION (v0.7.x safety)
      - Only TRANSACTION + VIOLATED + HIGH/CRITICAL may block execution
    """
    scope = _norm_scope(p.get("enforcement_scope", "TRANSACTION"))
    status = _norm_status(p.get("status") or p.get("verdict"))
    _, sev = _norm_severity(p)
    return scope == "TRANSACTION" and status == "VIOLATED" and sev in _SEVERITY_BLOCKING

# -----------------------------
# Constitutional Authority
# -----------------------------

@dataclass(frozen=True)
class ConstitutionalVerdict:
    decision_outcome: str
    severity: str
    human_oversight_required: bool
    safe_state_triggered: bool
    timestamp_utc: str
    engine_version: str
    rationale: str
    summary: Dict[str, Any]


class ConstitutionalAuthority:
    """
    GNCE Constitutional Authority (L1)

    Input: list of policy-like dicts (from executed regimes).
    Output: deterministic constitutional verdict.

    v0.7.2-RC:
      - Conservative blocking: HIGH/CRITICAL violations => DENY + safe_state_triggered
      - Any violation (even LOW/MED) => DENY + human_oversight_required
      - Adds narrative fields to make L1 "feel like a product"
      - Ensures recommended_actions is never empty (ALLOW included)
    """

    def adjudicate(self, policies: List[Dict[str, Any]], engine_version: str) -> Dict[str, Any]:
        policies = policies if isinstance(policies, list) else []

        violated: List[Dict[str, Any]] = []
        satisfied: List[Dict[str, Any]] = []
        not_applicable: List[Dict[str, Any]] = []
        unknown: List[Dict[str, Any]] = []

        max_any_score = 1
        max_any_level = "LOW"
        max_violation_score = 1
        max_violation_level = "LOW"

        for p in policies:
            if not isinstance(p, dict):
                continue

            status = _norm_status(p.get("status") or p.get("verdict"))
            score, level = _norm_severity(p)

            if score > max_any_score:
                max_any_score, max_any_level = score, level

            if status == "VIOLATED":
                violated.append(p)
                if score > max_violation_score:
                    max_violation_score, max_violation_level = score, level
            elif status == "SATISFIED":
                satisfied.append(p)
            elif status == "NOT_APPLICABLE":
                not_applicable.append(p)
            else:
                unknown.append(p)

        # Block only if a transaction-scoped policy is violated at HIGH/CRITICAL.
        blocking = [p for p in policies if _is_transaction_blocking(p)]
        has_any_violation = len(violated) > 0

        if blocking:
            decision = "DENY"
            severity = max_violation_level
            human_oversight_required = True
            safe_state_triggered = True
            rationale = (
                "Execution blocked: at least one HIGH/CRITICAL violation was detected "
                "in executed regimes (constitutional veto threshold)."
            )
        elif has_any_violation:
            # Non-blocking (e.g., PLATFORM_AUDIT/SUPERVISORY) violations should not stop the transaction.
            decision = "ALLOW"
            severity = max_violation_level
            human_oversight_required = False
            safe_state_triggered = False
            rationale = (
                "Execution authorized: violations were detected, but none are transaction-blocking "
                "(non-transaction obligations are tracked for compliance remediation)."
            )
        else:
            decision = "ALLOW"
            severity = max_any_level
            human_oversight_required = False
            safe_state_triggered = False
            rationale = "Execution authorized: no violations detected across executed regimes."

        verdict = ConstitutionalVerdict(
            decision_outcome=decision,
            severity=severity,
            human_oversight_required=human_oversight_required,
            safe_state_triggered=safe_state_triggered,
            timestamp_utc=_now_utc(),
            engine_version=str(engine_version or ""),
            rationale=rationale,
            summary={
                "policies_considered": len(policies),
                "violated": len(violated),
                "satisfied": len(satisfied),
                "not_applicable": len(not_applicable),
                "unknown": len(unknown),
                "blocking_violations": len(blocking),
                "highest_severity_any": max_any_level,
                "highest_severity_violation": (max_violation_level if has_any_violation else "LOW"),
            },
        )

        # ---------------------------------------------------------
        # L1 narrative enrichment (v0.7.2+)
        # ---------------------------------------------------------
        violations = violated
        high_viol = blocking

        because: List[str] = []
        if high_viol:
            for p in high_viol[:5]:
                because.append(_policy_label(p))
        elif violations:
            for p in violations[:5]:
                because.append(_policy_label(p))
        else:
            # ALLOW: show what *did* matter (SATISFIED signals), else a strong default
            for p in satisfied[:3]:
                because.append(_policy_label(p))
            if not because:
                because = ["No violations detected; evaluated obligations are satisfied or not applicable."]

        human_readable_outcome = (
            f"{verdict.decision_outcome} — Constitutional outcome at {verdict.severity} severity."
        )

        regulator_summary = (
            f"Outcome: {verdict.decision_outcome}. Severity: {verdict.severity}. "
            f"Blocking violations: {len(high_viol)}. Total violations: {len(violations)}. "
            f"Policies considered: {len(policies)}."
        )

        actions: List[str] = []
        # Prefer explicit remediation from violated/high policies if present
        for p in (high_viol or violations)[:5]:
            a = _recommended_action_from_policy(p)
            if a:
                actions.append(a)

        # If still empty, provide deterministic defaults by outcome
        if not actions and verdict.decision_outcome in {"DENY", "VETO"}:
            actions = [
                "Route to human review pool (Integrity/Trust & Safety).",
                "Collect additional evidence (context, user history, signals) and re-run GNCE after mitigation.",
                "If high-risk: keep action blocked until policy owner approval is recorded.",
            ]
        elif not actions and verdict.decision_outcome == "ALLOW":
            if violations:
                actions = [
                    "Proceed with execution.",
                    "Open a compliance remediation ticket for non-transaction obligations (audit/reporting/complaints/dispute).",
                    "Persist ADRA + evidence chain for audit readiness.",
                ]
            else:
                actions = [
                    "Proceed with execution.",
                    "Persist ADRA to SARS session ledger and export (if enabled).",
                    "Monitor drift signals (L6) over the next N runs; escalate if DRIFT_ALERT appears.",
                    "Sample this decision for periodic QA if the incident type is sensitive.",
                ]

        # Return a plain dict (UI + ADRA friendly)
        return {
            "decision_outcome": verdict.decision_outcome,
            "severity": verdict.severity,
            "human_oversight_required": verdict.human_oversight_required,
            "safe_state_triggered": verdict.safe_state_triggered,
            "timestamp_utc": verdict.timestamp_utc,
            "engine_version": verdict.engine_version,
            "rationale": verdict.rationale,
            "summary": verdict.summary,
            # v0.7.2 “meat”
            "human_readable_outcome": human_readable_outcome,
            "because": because,
            "regulator_summary": regulator_summary,
            "recommended_actions": actions,
        }


# Public singleton (matches your kernel usage)
GNCE_CONSTITUTION = ConstitutionalAuthority()
