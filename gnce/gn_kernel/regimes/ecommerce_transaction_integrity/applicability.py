"""Applicability for ECOMMERCE_TRANSACTION_INTEGRITY.

This file provides a stable `applicable(payload) -> bool` symbol because
the auto-discovery loader expects *some* standard name.

If you already have a function like `is_applicable(payload)` in this file,
keep it — `applicable()` will delegate to it automatically.
"""

from __future__ import annotations

from typing import Any, Dict


def is_applicable(payload: dict) -> bool:
    """Default applicability heuristic (safe + conservative)."""
    payload = payload or {}
    industry = str(payload.get("industry_id") or "").strip().upper()
    # Apply to common e-commerce-like industries.
    return industry in {"ECOMMERCE", "MARKETPLACE", "RETAIL"} or "ECOMMERCE" in industry


def applicable(payload: dict) -> bool:
    """Stable wrapper expected by some register() implementations."""
    # If a project-specific function exists, prefer it.
    fn = globals().get("is_applicable")
    if callable(fn):
        return bool(fn(payload))
    return False
