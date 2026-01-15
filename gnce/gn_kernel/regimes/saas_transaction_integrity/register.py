"""
Register SAAS_TRANSACTION_INTEGRITY with the GNCE regime registry.

This file follows the same pattern as other regimes in this repo:
- expose `register()` with no args
- call `register_regime(...)` using the correct GNCE v0.7.2-RC signature
"""
from __future__ import annotations

from gnce.gn_kernel.regimes.register import register_regime
from .applicability import is_applicable
from .resolver import resolve


def register() -> None:
    register_regime(
        regime_id="SAAS_TRANSACTION_INTEGRITY",  # ✅ FIXED
        display_name="SaaS Transaction Integrity",
        domain="SaaS Transaction Integrity",
        framework="SaaS Integrity Controls",
        regime_type="INTEGRITY",
        jurisdiction="GLOBAL",
        enforceable=True,
        l4_executable=True,
        authority="GNCE",
        applicability=is_applicable,
        resolver=resolve,
    )
