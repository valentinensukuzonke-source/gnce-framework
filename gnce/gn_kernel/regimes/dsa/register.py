# gnce/gn_kernel/regimes/dsa/register.py
from __future__ import annotations

from typing import Any, Dict

from gnce.gn_kernel.regimes.register import register_regime
from gnce.gn_kernel.regimes.dsa.applicability import applies_dsa
from gnce.gn_kernel.regimes.dsa.resolver import evaluate_dsa_articles


def register() -> None:
    """
    Register the DSA regime into the global registry.
    """
    register_regime(
        regime_id="DSA",
        display_name="EU Digital Services Act (Regulation)",
        domain="EU Digital Services Act (DSA)",
        framework="Platform Safety & Online Intermediary Compliance",
        regime_type="REGULATION",
        jurisdiction="EU",
        authority="European Union",
        enforceable=True,
        l4_executable=True,
        applicability=applies_dsa,
        resolver=evaluate_dsa_articles,
    )



