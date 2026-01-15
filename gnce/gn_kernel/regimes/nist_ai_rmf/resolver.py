"""NIST AI RMF regime resolver (live-wired).

This wraps the kernel-native evaluator `evaluate_nist_ai_rmf_rules` so the regime
registry can expose a callable resolver (and optionally be made executable later)
without duplicating policy logic.
"""

from __future__ import annotations

from typing import Any, Dict, List

from gnce.gn_kernel.rules.nist_ai_rmf_rules import evaluate_nist_ai_rmf_rules


def resolve(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Return NIST AI RMF policies in the standard resolver shape.

    NOTE: In GNCE v0.7.2-RC, NIST AI RMF is evaluated as a kernel-native regime.
    This resolver is provided for registry coherency and for future optional
    executable-mode wiring.
    """
    policies, summary = evaluate_nist_ai_rmf_rules(payload or {})
    # Ensure list type
    if not isinstance(policies, list):
        policies = []
    return {
        "policies_triggered": policies,
        "summary": summary or {},
    }
