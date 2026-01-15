# gnce/gn_kernel/regimes/sec_17A4/register.py
from __future__ import annotations

from gnce.gn_kernel.regimes.register import register_regime
from gnce.gn_kernel.regimes.sec_17A4.applicability import is_applicable
from gnce.gn_kernel.regimes.sec_17A4.resolver import resolve


def register() -> None:
    register_regime(
        regime_id="SEC_17A4",
        display_name="SEC Rule 17a-4 (Books and Records)",
        domain="Broker-Dealer Recordkeeping",
        framework="Financial / Markets Compliance",
        regime_type="RULE",
        jurisdiction="US",
        authority="SEC",
        enforceable=True,
        l4_executable=True,          # ✅ MUST be True
        applicability=is_applicable, # ✅ real applicability
        resolver=resolve,            # ✅ real resolver
    )
