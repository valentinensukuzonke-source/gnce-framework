"""Registry entry for GNCE Cyber Controls Regime.

Your kernel expects an executable registry like:
    from gnce.gn_kernel.regimes.register import init_registry, REGIME_REGISTRY

This module provides a spec dict compatible with kernel.py usage:
- kernel.py checks `spec.get("applicability")` (callable) and `spec.get("resolver")` (callable)
- kernel.py reads `spec.get("domain_id")` and `spec.get("display_name")` for stubs

Integration (in your central registry file):
    from .cyber_controls.register import get_regime_spec, REGIME_ID

    REGIME_REGISTRY[REGIME_ID] = get_regime_spec()

If your central registry is building via init_registry(), add the same line there.
"""

from __future__ import annotations

from typing import Any, Callable, Dict

from .applicability import is_applicable
from .resolver import resolve

REGIME_ID = "GNCE_CYBER_CONTROLS"

def get_regime_spec() -> Dict[str, Any]:
    """Return the regime spec used by GNCE's executable registry."""
    return {
        "regime_id": REGIME_ID,
        "domain_id": "CYBER_CONTROLS",
        "display_name": "GNCE Cyber Controls Regime",
        "framework": "GNCE",
        "version": "0.1.0",
        "description": (
            "Execution-time evaluation of cyber control constraints for security-relevant actions. "
            "Governance of whether the action may execute, with audit-grade artifacts."
        ),
        "applicability": is_applicable,  # (payload) -> (bool, reason)
        "resolver": resolve,              # (payload) -> dict|list of policy results
    }
