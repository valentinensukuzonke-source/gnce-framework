# gnce/ui/operations_governance_console/models/drift.py
from __future__ import annotations

from typing import Any, Dict, List
from collections import Counter
from datetime import datetime


def drift_summary(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Drift here is computed as *signals of instability* we can prove from ledger:
    - sudden DENY spikes
    - high churn in veto layers
    - constitution hash changes in a session
    """
    if not entries:
        return {
            "risk": "UNKNOWN",
            "deny_rate": 0.0,
            "top_veto_layers": [],
            "constitution_hash_churn": 0,
            "notes": ["No ledger entries loaded."],
        }

    verdicts = [e.get("_verdict") for e in entries]
    c = Counter(verdicts)
    total = sum(c.values()) or 1
    deny_rate = (c.get("DENY", 0) / total) * 100.0

    veto_layers = [e.get("_veto_layer") for e in entries if e.get("_verdict") == "DENY" and e.get("_veto_layer")]
    veto_counts = Counter(veto_layers)

    const_hashes = [e.get("_constitution_hash") for e in entries if e.get("_constitution_hash")]
    const_churn = len(set(const_hashes)) - 1 if const_hashes else 0

    # Risk heuristic (read-only, explainable)
    notes: List[str] = []
    risk = "GREEN"
    if const_churn > 0:
        risk = "AMBER"
        notes.append("Constitution hash varied within the loaded session scope (possible recompile / drift event).")
    if deny_rate >= 35.0:
        risk = "AMBER"
        notes.append("DENY rate is elevated; investigate policy-regime or external-law shifts.")
    if deny_rate >= 60.0:
        risk = "RED"
        notes.append("DENY rate is severe; system is likely operating under constraint pressure.")
    if len(veto_counts) >= 4 and deny_rate >= 35.0:
        risk = "RED"
        notes.append("Veto origin is highly distributed across layers (instability signal).")

    return {
        "risk": risk,
        "deny_rate": round(deny_rate, 2),
        "top_veto_layers": veto_counts.most_common(5),
        "constitution_hash_churn": max(const_churn, 0),
        "notes": notes or ["No drift anomalies detected from available ledger signals."],
    }
