# gnce/gn_kernel/regimes/fintech_transaction_integrity/register.py

from __future__ import annotations

from gnce.gn_kernel.regimes.register import register_regime

# Some builds have RegimeType enum, some use plain strings.
try:
    from gnce.gn_kernel.regimes.register import RegimeType  # type: ignore
    _POLICY = RegimeType.POLICY
except Exception:
    _POLICY = "POLICY"


def register() -> None:
    # Import inside function so module import errors show up during init_registry()
    from .applicability import is_applicable
    from .resolver import resolve

    register_regime(
        "FINTECH_TRANSACTION_INTEGRITY",
        display_name="Fintech Transaction Integrity",
        domain="Transaction Integrity",
        framework="GNCE Constitutional Policy",
        regime_type=_POLICY,
        jurisdiction="GLOBAL",
        enforceable=True,
        l4_executable=True,
        authority="GNCE Constitutional Controls — Transaction Integrity",
        applicability=is_applicable,
        resolver=resolve,
    )
