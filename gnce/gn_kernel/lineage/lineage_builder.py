#gnce/gn_kernel/lineage/lineage_builder.py
from __future__ import annotations
from typing import Any, Dict, List

def build_lineage(adra: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build lineage as a deterministic derived artifact.

    IMPORTANT:
    - Must NOT mutate ADRA.
    - Kernel is the only authority allowed to attach lineage into ADRA
      (pre-finalization).
    """
    l0 = adra.get("L0_pre_execution_validation") or {}
    l1 = adra.get("L1_the_verdict_and_constitutional_outcome") or {}
    l4 = adra.get("L4_policy_lineage_and_constitution") or {}
    l6 = adra.get("L6_behavioral_drift_and_monitoring") or {}
    l7 = adra.get("L7_veto_and_execution_feedback") or {}

    # Lightweight deterministic summary (extend as you like)
    policies = (l4.get("policies_triggered") or []) if isinstance(l4, dict) else []
    articles = [p.get("article") for p in policies if isinstance(p, dict) and p.get("article")]

    return {
        "version": "1.0",
        "adra_id": adra.get("adra_id"),
        "created_at_utc": adra.get("created_at_utc"),
        "anchors": {
            "l0_validated": bool(l0.get("validated", False)) if isinstance(l0, dict) else None,
            "decision_outcome": l1.get("decision_outcome") if isinstance(l1, dict) else None,
            "severity": l1.get("severity") if isinstance(l1, dict) else None,
            "drift_outcome": l6.get("drift_outcome") if isinstance(l6, dict) else None,
            "veto": bool(l7.get("veto_path_triggered") or l7.get("veto_triggered"))
            if isinstance(l7, dict)
            else None,
            "articles": articles,
        },
        "edges": [],   # reserved for richer graph later
        "notes": "Embedded lineage (kernel-attached pre-finalization).",
    }
