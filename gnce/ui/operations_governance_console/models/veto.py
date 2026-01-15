# gnce/ui/operations_governance_console/models/veto.py
from __future__ import annotations

from typing import Any, Dict, List
from collections import Counter


def veto_insights(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    denied = [e for e in entries if e.get("_verdict") == "DENY"]
    if not denied:
        return {
            "deny_count": 0,
            "top_layers": [],
            "top_clauses": [],
            "notes": ["No DENY entries found in loaded scope."],
        }

    layers = [e.get("_veto_layer") or "UNKNOWN" for e in denied]
    clauses = [e.get("_clause") or "UNKNOWN" for e in denied]

    layer_counts = Counter(layers)
    clause_counts = Counter(clauses)

    return {
        "deny_count": len(denied),
        "top_layers": layer_counts.most_common(7),
        "top_clauses": clause_counts.most_common(7),
        "sample_denies": denied[:10],
        "notes": ["Veto path is active; review top clauses for policy/regulatory pressure."],
    }
