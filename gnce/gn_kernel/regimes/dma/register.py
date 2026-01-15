# gnce/gn_kernel/regimes/dma/register.py
from __future__ import annotations

from gnce.gn_kernel.regimes.register import register_regime
from .applicability import applies_dma
from .resolver import evaluate_dma_obligations


def register() -> None:
    register_regime(
        regime_id="DMA",
        display_name="EU Digital Markets Act (Regulation)",
        domain="EU Digital Markets Act (DMA)",
        framework="Platform Competition & Gatekeeper Obligations",
        regime_type="REGULATION",
        jurisdiction="EU",
        authority="European Union",
        enforceable=True,
        l4_executable=False,  # set True only when you have real DMA rule execution
        applicability=applies_dma,
        resolver=evaluate_dma_obligations,
    )
