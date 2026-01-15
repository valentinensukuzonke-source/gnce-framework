"""NIST AI RMF regime registration (live-wired, GNCE v0.7.2-RC).

This file registers the NIST AI RMF regime in the global REGIME_REGISTRY using the
current `register_regime()` API. It is designed to be compatible with the
autodiscovery loader in `gnce.gn_kernel.regimes.register`.

Key points:
- Uses `regime_id` (not `id`) to match the GNCE registry schema.
- Provides a robust `applicability` import fallback (different regimes may name it
  `applicable`, `is_applicable`, or `applies`).
- Exposes a callable `resolver` via `resolver.resolve`, which wraps the existing
  kernel-native evaluator.
"""

from __future__ import annotations

from typing import Any, Dict, Callable

from gnce.gn_kernel.regimes.register import register_regime


def _load_applicability() -> Callable[[Dict[str, Any]], bool]:
    """Best-effort import for the regime applicability predicate."""
    try:
        # Most regimes use this name
        from .applicability import applicable as fn  # type: ignore
        return fn
    except Exception:
        pass
    try:
        from .applicability import is_applicable as fn  # type: ignore
        return fn
    except Exception:
        pass
    try:
        from .applicability import applies as fn  # type: ignore
        return fn
    except Exception:
        pass

    # Fallback: allow evaluation; underlying rule evaluators can still return NOT_APPLICABLE
    def _default(_: Dict[str, Any]) -> bool:
        return True

    return _default


def register() -> None:
    """Register NIST AI RMF into the GNCE regime registry."""
    from .resolver import resolve  # local import to avoid import-order issues

    applicability = _load_applicability()

    register_regime(
        regime_id="NIST_AI_RMF",
        display_name="NIST AI Risk Management Framework",
        domain="NIST AI RMF",
        framework="Risk Management Framework",
        regime_type="FRAMEWORK",
        jurisdiction="GLOBAL",
        enforceable=False,
        l4_executable=True,
        authority="NIST",
        applicability=applicability,
        resolver=resolve,
    )
