"""
Auto-generated GNCE regime register for ISO_42001.

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
    Register ISO_42001 into the global REGIME_REGISTRY.

    This function is discovered automatically by gnce.gn_kernel.regimes.register.init_registry().
    """
    register_regime(
        regime_id="ISO_42001",
        display_name="ISO/IEC 42001",
        domain="AI Governance",
        framework="AI Governance & Risk Management",
        regime_type="STANDARD",
        jurisdiction="GLOBAL",
        enforceable=True,
        l4_executable=True,
        authority="ISO",
        applicability=applicable,
        resolver=resolve,
    )
