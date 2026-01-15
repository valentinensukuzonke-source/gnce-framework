# gnce/kernel/events.py
from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime, timezone
import uuid


GNCE_VERSION = "0.4.0"

SEVERITY_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
SEVERITY_SCORE = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


def _utc_now_iso() -> str:
    """Return current UTC time in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def _norm_severity(raw: Any) -> str:
    """Normalise severity into LOW/MEDIUM/HIGH/CRITICAL/UNKNOWN."""
    if raw is None:
        return "UNKNOWN"

    if isinstance(raw, (int, float)):
        val = int(raw)
        if val <= 1:
            return "LOW"
        elif val == 2:
            return "MEDIUM"
        elif val == 3:
            return "HIGH"
        else:
            return "CRITICAL"

    s = str(raw).strip().upper()
    if not s:
        return "UNKNOWN"
    if s in SEVERITY_ORDER:
        return s
    return s  # some other label, keep as-is


def _severity_score(raw: Any) -> int:
    """Numeric severity score for risk-weighting."""
    label = _norm_severity(raw)
    return SEVERITY_SCORE.get(label, 0)


def _base_event(
    *,
    event_type: str,
    adra_id: str,
    ts_utc: str,
    payload: Dict[str, Any] | None = None,
    extra: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Common envelope for all GNCE events."""
    ev: Dict[str, Any] = {
        "event_id": "ev-" + uuid.uuid4().hex[:12],
        "event_type": event_type,
        "ts_utc": ts_utc,
        "adra_id": adra_id,
        "gnce_version": GNCE_VERSION,
    }
    if payload is not None:
        ev["payload"] = payload
    if extra:
        ev.update(extra)
    return ev


def build_event_stream(
    adra_id: str,
    raw_payload: Dict[str, Any],
    policies: List[Dict[str, Any]],
    l1: Dict[str, Any],
    l6: Dict[str, Any],
    l7: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Build a GNCE event stream for this ADRA execution.

    Event types (v0.4 demo):
      - ADRA_CREATED
      - L1_VERDICT
      - POLICY_EVAL (one per L4 policy)
      - DRIFT_STATUS
      - VETO_STATUS
    """
    events: List[Dict[str, Any]] = []

    ts = l1.get("timestamp_utc") or _utc_now_iso()

    # 1) ADRA_CREATED
    events.append(
        _base_event(
            event_type="ADRA_CREATED",
            adra_id=adra_id,
            ts_utc=ts,
            payload={"input": raw_payload},
            extra={},
        )
    )

    # 2) L1_VERDICT
    verdict_decision = l1.get("decision_outcome") or l1.get("decision") or "N/A"
    verdict_severity = _norm_severity(l1.get("severity", "UNKNOWN"))

    events.append(
        _base_event(
            event_type="L1_VERDICT",
            adra_id=adra_id,
            ts_utc=ts,
            extra={
                "decision_outcome": verdict_decision,
                "severity": verdict_severity,
                "severity_score": _severity_score(verdict_severity),
                "human_oversight_required": bool(
                    l1.get("human_oversight_required", False)
                ),
                "safe_state_triggered": bool(l1.get("safe_state_triggered", False)),
            },
        )
    )

    # 3) POLICY_EVAL – one per L4 policy
    for p in policies:
        if not isinstance(p, dict):
            continue

        regime = (
            p.get("regime")
            or p.get("domain")
            or p.get("regulatory_domain")
            or "UNKNOWN_REGIME"
        )
        domain = p.get("domain") or regime
        article = p.get("article", "N/A")

        status = str(p.get("status", "UNKNOWN")).upper()
        sev = _norm_severity(
            p.get("severity")
            or p.get("severity_level")
            or p.get("severity_score")
            or p.get("criticality")
        )

        events.append(
            _base_event(
                event_type="POLICY_EVAL",
                adra_id=adra_id,
                ts_utc=ts,
                extra={
                    "regime": regime,
                    "domain": domain,
                    "article": article,
                    "status": status,
                    "severity": sev,
                    "severity_score": _severity_score(sev),
                    "rule_ids": p.get("rule_ids", []),
                    "impact_on_verdict": p.get("impact_on_verdict"),
                },
            )
        )

    # 4) DRIFT_STATUS
    drift_outcome = (
        l6.get("drift_outcome")
        or l6.get("drift_status")
        or l6.get("drift_state")
        or "NO_DRIFT"
    )
    events.append(
        _base_event(
            event_type="DRIFT_STATUS",
            adra_id=adra_id,
            ts_utc=ts,
            extra={
                "drift_outcome": str(drift_outcome),
                "notes": l6.get("notes"),
            },
        )
    )

    # 5) VETO_STATUS
    execution_authorized = bool(l7.get("execution_authorized", True))
    veto_path_triggered = bool(l7.get("veto_path_triggered", not execution_authorized))

    events.append(
        _base_event(
            event_type="VETO_STATUS",
            adra_id=adra_id,
            ts_utc=ts,
            extra={
                "execution_authorized": execution_authorized,
                "veto_path_triggered": veto_path_triggered,
                "notes": l7.get("notes"),
            },
        )
    )

    return events
