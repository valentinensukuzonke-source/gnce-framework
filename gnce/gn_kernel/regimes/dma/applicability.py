# gnce/kernel/regimes/dma/applicability.py
from __future__ import annotations

from typing import Any, Dict


def applies_dma(ctx: Dict[str, Any]) -> bool:
    """
    DMA applies when:
    - market is EU
    - operator is explicitly marked as a gatekeeper (conservative)
    """
    market = str(ctx.get("market") or "").upper()
    if market != "EU":
        return False

    dma = ctx.get("dma") or ctx.get("dma_profile") or {}
    if not isinstance(dma, dict):
        dma = {}

    return dma.get("is_gatekeeper") is True
