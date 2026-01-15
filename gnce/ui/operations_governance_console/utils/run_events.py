from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, Optional
from datetime import datetime, timezone
import json
import uuid
import hashlib

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def _safe_get(d: Dict[str, Any], *path, default=None):
    cur: Any = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur

def _sha256_json(obj: Any) -> str:
    b = json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(b).hexdigest()

def emit_run_event(
    *,
    out_path: Path,
    adra: Dict[str, Any],
    session_id: str,
    engine_version: str,
    engine_mode: str,
    regulator_view: bool,
    federation_enabled: bool,
    payload_name: str,
    export_enabled: bool,
    exported: bool,
    export_path: Optional[str],
) -> Dict[str, Any]:
    adra_id = adra.get("adra_id") or adra.get("id") or adra.get("ADRA_ID") or "unknown"
    decision = (
        _safe_get(adra, "L1_the_verdict_and_constitutional_outcome", "decision_outcome")
        or adra.get("decision")
        or "UNKNOWN"
    )
    severity = (
        _safe_get(adra, "L1_the_verdict_and_constitutional_outcome", "severity")
        or adra.get("severity")
        or "N/A"
    )
    execution_eligible = bool(
        _safe_get(adra, "L1_the_verdict_and_constitutional_outcome", "execution_authorized", default=False)
        or adra.get("execution_eligible", False)
    )

    drift_outcome = adra.get("drift_outcome") or _safe_get(adra, "L6_behavioral_drift_monitoring", "drift_outcome") or "N/A"
    veto_category = adra.get("veto_category") or _safe_get(adra, "L7_veto_and_execution_feedback", "veto_category") or "N/A"

    violations = _safe_get(adra, "L4_policy_lineage_and_constitution", "policies_triggered", default=[])
    violations_count = 0
    if isinstance(violations, list):
        violations_count = sum(1 for p in violations if isinstance(p, dict) and p.get("status") == "VIOLATED")

    evt = {
        "event_type": "gnce_run",
        "event_version": "1.0",
        "event_id": f"evt-{uuid.uuid4().hex}",
        "ts_utc": _utc_now_iso(),

        "session_id": session_id,
        "engine_version": engine_version,
        "engine_mode": engine_mode,
        "regulator_view": regulator_view,
        "federation_enabled": federation_enabled,

        "payload_name": payload_name,

        "adra_id": adra_id,
        "decision": decision,
        "severity": severity,
        "execution_eligible": execution_eligible,
        "drift_outcome": drift_outcome,
        "violations_count": violations_count,
        "veto_category": veto_category,

        "export_enabled": export_enabled,
        "exported": exported,
        "export_path": export_path,

        # integrity of the event itself (not the ADRA)
        "checksum_sha256": _sha256_json({
            "adra_id": adra_id,
            "decision": decision,
            "severity": severity,
            "ts_utc": _utc_now_iso(),
        }),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(evt, ensure_ascii=False) + "\n")

    return evt


def iter_events(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out


def compute_kpis_from_events(events: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    total = 0
    allow = 0
    deny = 0
    drift_alerts = 0
    veto_events = 0
    sev_sum = 0.0
    sev_n = 0

    sev_map = {"LOW": 1.0, "MEDIUM": 2.0, "HIGH": 3.0, "CRITICAL": 4.0}

    for e in events:
        if e.get("event_type") != "gnce_run":
            continue
        total += 1
        d = (e.get("decision") or "UNKNOWN").upper()
        if d == "ALLOW":
            allow += 1
        elif d == "DENY":
            deny += 1

        if (e.get("drift_outcome") or "").upper() == "DRIFT_ALERT":
            drift_alerts += 1

        vc = (e.get("veto_category") or "N/A").upper()
        if vc not in ("N/A", "NONE", ""):
            veto_events += 1

        s = (e.get("severity") or "").upper()
        if s in sev_map:
            sev_sum += sev_map[s]
            sev_n += 1

    allow_pct = (allow / total * 100.0) if total else 0.0
    deny_pct = (deny / total * 100.0) if total else 0.0
    avg_sev = (sev_sum / sev_n) if sev_n else 0.0

    return {
        "total_runs": total,
        "allow": allow,
        "deny": deny,
        "allow_pct": allow_pct,
        "deny_pct": deny_pct,
        "drift_alerts": drift_alerts,
        "veto_events": veto_events,
        "avg_severity_score": avg_sev,
    }
