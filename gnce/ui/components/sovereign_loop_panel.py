# ui/components/sovereign_loop_panel.py
from __future__ import annotations

from typing import Dict, Any
import streamlit as st


def render_sovereign_loop_panel(adra: Dict[str, Any]) -> None:
    """
    🏛 Sovereign Constitutional Loop (S-Loop)

    This panel explains GNCE's constitutional substrate:
    - Defined by humans (once, out-of-band)
    - Enforced autonomously by GNCE at runtime
    - Audited transparently after the fact

    It is purely descriptive: it does NOT introduce any human-in-the-runtime-loop
    behaviour and has no effect on the verdict path.
    """
    if not isinstance(adra, dict):
        return

    l1 = adra.get("L1_the_verdict_and_constitutional_outcome", {}) or {}
    decision = str(l1.get("decision_outcome", "N/A")).upper()
    severity = str(l1.get("severity", "UNKNOWN")).upper()
  