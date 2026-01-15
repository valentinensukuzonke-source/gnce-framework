"""
Auto-generated GNCE regime register for PCI_DSS.

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
    Register PCI_DSS into the global REGIME_REGISTRY.

    This function is discovered automatically by gnce.gn_kernel.regimes.register.init_registry().
    """
    register_regime(
        regime_id="PCI_DSS",
        display_name="PCI DSS",
        domain="Payments Security",
        framework="Payment Card Industry Data Security Standard",
        regime_type="STANDARD",
        jurisdiction="GLOBAL",
        enforceable=True,
        l4_executable=True,
        authority="PCI SSC",
        applicability=applicable,
        resolver=resolve,
    )
