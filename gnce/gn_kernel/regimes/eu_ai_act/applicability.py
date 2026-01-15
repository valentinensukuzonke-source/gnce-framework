# gnce/regimes/eu_ai_act/applicability.py
from __future__ import annotations

from typing import Any, Dict


def applies_eu_ai_act(ctx: Dict[str, Any]) -> bool:
    """
    Conservative EU AI Act applicability:
    - market is EU
    - ai_system flag is present OR ai_profile indicates an AI system
    """
    market = str(ctx.get("market") or "").upper()
    if market != "EU":
        return False

    ai = ctx.get("ai") or ctx.get("ai_profile") or {}
    if not isinstance(ai, dict):
        ai = {}

    return ai.get("is_ai_system") is True or ctx.get("is_ai_system") is True
