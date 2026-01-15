# gnce/gn_kernel/execution/executor.py
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional, List

from .protocol import RunEvent, now_utc_iso, best_effort_regime

# Optional: L7 veto helpers. If dedicated modules exist, use them; otherwise fall back to local logic.
try:
    from gnce.gn_kernel.execution.veto_engine import build_veto_basis  # type: ignore
except Exception:  # pragma: no cover
    def build_veto_basis(l4_results: dict) -> list[dict]:
        """Extract a minimal veto_basis from L4 policies (violated HIGH/CRITICAL items)."""
        policies = (l4_results or {}).get("policies_triggered") or []
        basis: list[dict] = []
        for p in policies:
            if not isinstance(p, dict):
                continue
            status = str(p.get("status") or "").upper()
            sev = str(p.get("severity") or "").upper()
            if status != "VIOLATED":
                continue
            if sev not in ("HIGH", "CRITICAL"):
                continue
            basis.append(
                {
                    "article": p.get("article") or p.get("title") or "UNKNOWN",
                    "status": status,
                    "severity": sev,
                    "constitutional_clause": "GNCE Sec. 1.1 — No HIGH/CRITICAL violation may yield ALLOW.",
                    "explanation": f"Article {p.get('article') or 'UNKNOWN'} violated with severity {sev}.",
                }
            )
        return basis

try:
    from gnce.gn_kernel.layers.l7_veto import apply_l7_veto  # type: ignore
except Exception:  # pragma: no cover
    def apply_l7_veto(veto_basis: list[dict], constitution: dict | None = None) -> dict:
        """Create the L7 veto payload from a veto_basis list."""
        triggered = len(veto_basis or []) > 0
        escalation = "HUMAN_REVIEWER" if triggered else None
        veto_category = "CONSTITUTIONAL_BLOCK" if triggered else None

        payload = {
            "execution_authorized": not triggered,
            "veto_path_triggered": triggered,
            "veto_category": veto_category,
            "veto_basis": veto_basis or [],
            "escalation_required": escalation,
            "constitutional_citation": (
                "A system cannot execute an ALLOW verdict when HIGH/CRITICAL obligations are violated "
                "or when DRIFT_ALERT remains unresolved."
            ),
            "layer": "L7",
            "title": "Veto Path & Sovereign Execution Feedback",
            "validated": True,
            "issues": ([f"Execution blocked (veto_category={veto_category})."] if triggered else []),
            "severity": ("HIGH" if triggered else "LOW"),
            "constitutional": {
                "clause": "GNCE Sec. 7.1 — No execution may proceed when veto conditions are present.",
                "explainability": {
                    "headline": (
                        f"EXECUTION BLOCKED — veto_category={veto_category}, escalation={escalation}."
                        if triggered
                        else "EXECUTION AUTHORIZED — no veto conditions present."
                    )
                },
            },
            "checks": [
                {
                    "check_id": "L7.EXECUTION_AUTHORIZED",
                    "description": "Execution authorized only when no veto conditions exist.",
                    "pass": (not triggered),
                    "observed": str(not triggered),
                },
                {
                    "check_id": "L7.VETO_PATH_STATUS",
                    "description": "Veto path not triggered (or escalation required).",
                    "pass": (not triggered),
                    "observed": str(triggered),
                },
            ],
            "evidence": {
                "veto_category": veto_category,
                "escalation_required": escalation,
                "veto_basis_count": len(veto_basis or []),
            },
            "decision_gate": {
                "allow_downstream": (not triggered),
                "block_reason": (f"L7 veto: {veto_category} (escalation={escalation})." if triggered else None),
                "gate_reason": (
                    f"DENY: execution blocked (veto_category={veto_category}, escalation={escalation})."
                    if triggered
                    else "ALLOW: execution authorized (no veto conditions)."
                ),
            },
        }
        return payload



def _sha256_json(obj: Dict[str, Any]) -> str:
    b = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(b).hexdigest()


def _first_str(*vals: Any, default: str = "UNKNOWN") -> str:
    for v in vals:
        if isinstance(v, str) and v.strip():
            return v.strip()
    return default


def _count_violations(adra: Dict[str, Any]) -> int:
    l4 = adra.get("L4_policy_lineage_and_constitution") or {}
    policies = l4.get("policies_triggered")
    if isinstance(policies, list):
        return sum(
            1 for p in policies
            if isinstance(p, dict) and str(p.get("status") or "").upper() == "VIOLATED"
        )
    return 0


def build_run_event(
    *,
    adra: Dict[str, Any],
    session_id: str,
    engine_mode: str,
    regulator_view: bool,
    federation_enabled: bool,
    payload_name: Optional[str],
    export_enabled: bool,
    exported: bool,
    export_path: Optional[str],
) -> RunEvent:
    l1 = adra.get("L1_the_verdict_and_constitutional_outcome") or {}
    l7 = adra.get("L7_veto_and_execution_feedback") or {}

    # If L7 is missing, derive it deterministically from L4 (and constitution if present).
    if not l7:
        l4 = adra.get("L4_policy_lineage_and_constitution") or {}
        constitution = adra.get("constitution") or adra.get("L0_constitution") or None
        veto_basis = build_veto_basis(l4)
        l7 = apply_l7_veto(veto_basis, constitution)
        # Persist into the ADRA so downstream UI/ledger tooling can see it.
        adra["L7_veto_and_execution_feedback"] = l7

    decision = _first_str(adra.get("decision"), adra.get("Decision"), l1.get("decision_outcome"), default="UNKNOWN")
    severity = _first_str(adra.get("severity"), adra.get("Severity"), l1.get("severity"), default="N/A")

    # Risk band: you can map from severity score later; for now keep best-effort
    risk_band = _first_str(adra.get("risk_band"), adra.get("session_risk_band"), default="N/A")

    exec_val = l7.get("execution_authorized")
    if exec_val is None:
        exec_val = adra.get("execution_authorized")

    execution_authorized = bool(exec_val) if exec_val is not None else False

    adra_id = _first_str(adra.get("adra_id"), adra.get("ADRA ID"), default="—")
    violations_count = _count_violations(adra)
    regime = best_effort_regime(adra)

    return RunEvent(
        event_type="GNCE_RUN",
        ts_utc=now_utc_iso(),
        session_id=session_id,
        adra_id=adra_id,
        decision=decision,
        severity=severity,
        risk_band=risk_band,
        regime=regime,
        violations_count=int(violations_count),
        execution_authorized=execution_authorized,
        engine_mode=engine_mode,
        regulator_view=bool(regulator_view),
        federation_enabled=bool(federation_enabled),
        payload_name=payload_name,
        export_enabled=bool(export_enabled),
        exported=bool(exported),
        export_path=export_path,
        adra_hash_sha256=_sha256_json(adra),
    )


def append_jsonl(path: Path, evt: RunEvent) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(evt.to_dict(), ensure_ascii=False) + "\n")
