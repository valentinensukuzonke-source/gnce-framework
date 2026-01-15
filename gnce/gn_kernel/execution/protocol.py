# gnce/gn_kernel/execution/protocol.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class RunEvent:
    """
    Immutable run-event contract (what we publish to Kafka / write JSONL).
    This is the OLTP record. KPI rollups are derived (OLAP).
    """
    event_type: str                 # "GNCE_RUN"
    ts_utc: str                     # ISO timestamp
    session_id: str
    adra_id: str

    decision: str                   # "ALLOW"/"DENY"/"UNKNOWN"
    severity: str                   # "LOW"/"MEDIUM"/"HIGH"/"CRITICAL"/"N/A"
    risk_band: str                  # "LOW"/"MEDIUM"/"HIGH"/"CRITICAL"/"N/A"

    regime: str                     # e.g. "DSA" / "DMA" / "GDPR" / "MIXED" / "UNKNOWN"
    violations_count: int
    execution_authorized: bool

    engine_mode: str                # "Lab Mode"/"Production Mode"
    regulator_view: bool
    federation_enabled: bool

    payload_name: Optional[str] = None
    export_enabled: bool = False
    exported: bool = False
    export_path: Optional[str] = None

    # Optional: keep a tiny signature field for later integrity chaining
    adra_hash_sha256: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def best_effort_regime(adra: Dict[str, Any]) -> str:
    """
    Pick a primary regime for slicing (per-regime KPIs).
    Strategy:
      - Prefer L4.policies_triggered domains/regime fields if present
      - Else L1 verdict block may include regime
      - Else "UNKNOWN"
    """
    l4 = adra.get("L4_policy_lineage_and_constitution") or {}
    policies = l4.get("policies_triggered")
    if isinstance(policies, list) and policies:
        regimes = []
        for p in policies:
            if isinstance(p, dict):
                r = p.get("regime") or p.get("Regime")
                if isinstance(r, str) and r.strip():
                    regimes.append(r.strip())
        regimes = list(dict.fromkeys(regimes))
        if len(regimes) == 1:
            return regimes[0]
        if len(regimes) > 1:
            return "MIXED"

    l1 = adra.get("L1_the_verdict_and_constitutional_outcome") or {}
    r = l1.get("regime") or l1.get("Regime")
    if isinstance(r, str) and r.strip():
        return r.strip()

    return "UNKNOWN"
