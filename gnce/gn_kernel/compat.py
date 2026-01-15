# gnce/kernel/compat.py
from __future__ import annotations

import copy
from typing import Any, Dict


def apply_compat(adra: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compatibility bridge for legacy ADRA shapes.

    IMPORTANT:
    - Never mutates the input ADRA (safe for finalized ADRAs)
    - Returns a deepcopy with alias keys added if needed
    """
    out: Dict[str, Any] = copy.deepcopy(adra)

    # Legacy → canonical aliasing (L4/L7)
    if "L4_policy_lineage_and_constitution" not in out and "L4" in out:
        out["L4_policy_lineage_and_constitution"] = out["L4"]

    if "L7_veto_and_execution_feedback" not in out and "L7" in out:
        out["L7_veto_and_execution_feedback"] = out["L7"]

    return out
