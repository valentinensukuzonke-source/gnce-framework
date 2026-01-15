"""
Auto-generated GNCE regime register for BSA_AML.

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
    Register BSA_AML into the global REGIME_REGISTRY.

    This function is discovered automatically by gnce.gn_kernel.regimes.register.init_registry().
    """
    register_regime(
        regime_id="BSA_AML",
        display_name="BSA/AML",
        domain="US Financial Crime",
        framework="Bank Secrecy Act / Anti-Money Laundering",
        regime_type="REGULATION",
        jurisdiction="US",
        enforceable=True,
        l4_executable=True,
        authority="FinCEN",
        applicability=applicable,
        resolver=resolve,
    )
