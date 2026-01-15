# gnce/gn_kernel/execution/metrics.py
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Any, Iterable


def compute_kpis(events: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    total = 0
    allow = 0
    deny = 0

    # Per-regime buckets
    by_regime = defaultdict(lambda: {"total": 0, "allow": 0, "deny": 0})

    for e in events:
        if not isinstance(e, dict):
            continue
        if e.get("event_type") != "GNCE_RUN":
            continue

        total += 1
        decision = str(e.get("decision") or "").upper()
        regime = str(e.get("regime") or "UNKNOWN")

        by_regime[regime]["total"] += 1

        if decision == "ALLOW":
            allow += 1
            by_regime[regime]["allow"] += 1
        elif decision == "DENY":
            deny += 1
            by_regime[regime]["deny"] += 1

    return {
        "total_runs": total,
        "allow_count": allow,
        "deny_count": deny,
        "by_regime": dict(by_regime),  # { "DSA": {...}, "DMA": {...}, ... }
    }
