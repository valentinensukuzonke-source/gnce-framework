# gnce/gn_kernel/regimes/eu_ai_act/register.py
from __future__ import annotations

from gnce.gn_kernel.regimes.register import register_regime

from .applicability import applies_eu_ai_act
from .resolver import evaluate_eu_ai_act_controls


def register() -> None:
    register_regime(
        "EU_AI_ACT",
        display_name="EU AI Act (Regulation)",
        domain="EU AI Act",
        framework="AI System Risk & Compliance Controls",
        regime_type="REGULATION",
        jurisdiction="EU",
        authority="European Union",
        enforceable=True,
        l4_executable=True,
        applicability=applies_eu_ai_act,
        resolver=evaluate_eu_ai_act_controls,
    )
