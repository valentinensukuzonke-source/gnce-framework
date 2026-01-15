# gnce/gn_kernel/regimes/sox/register.py
from gnce.gn_kernel.regimes.register import register_regime
from gnce.gn_kernel.regimes.sox.applicability import is_applicable
from gnce.gn_kernel.regimes.sox.resolver import resolve


def register() -> None:
    register_regime(
        regime_id="SOX",
        display_name="Sarbanes–Oxley Act (SOX)",
        domain="Financial Reporting Controls",
        framework="US Federal Law",
        regime_type="ACT",
        jurisdiction="US",
        authority="SEC/PCAOB",
        enforceable=True,
        l4_executable=True,
        applicability=is_applicable,
        resolver=resolve,
    )
