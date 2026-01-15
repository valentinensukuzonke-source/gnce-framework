"""
Auto-generated GNCE regime register for FINRA.

- Uses gnce.gn_kernel.regimes.register.register_regime (new universal API).
- Backward compatible with older GNCE builds that may still accept legacy shapes.
"""
from __future__ import annotations

from gnce.gn_kernel.regimes.register import register_regime

# Local hooks
from .applicability import applicable
from .resolver import resolve


def register() -> None:
    """
    Register FINRA into the global REGIME_REGISTRY.

    This function is discovered automatically by gnce.gn_kernel.regimes.register.init_registry().
    """
    register_regime(
        regime_id="FINRA",
        display_name="FINRA Rules",
        domain="US Financial Markets",
        framework="FINRA Regulatory Compliance",
        regime_type="REGULATION",
        jurisdiction="US",
        enforceable=True,
        l4_executable=True,
        authority="FINRA",
        applicability=applicable,
        resolver=resolve,
    )
