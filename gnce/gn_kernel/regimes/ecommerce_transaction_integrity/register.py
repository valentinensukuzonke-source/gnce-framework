"""ECOMMERCE Transaction Integrity regime registration.

Fixes:
- Makes applicability import robust (supports `applicable`, `is_applicable`, `applies`).
- Uses GNCE's current `register_regime` signature (regime_id=..., not id=...).
- Keeps backward compatibility if older helper names exist.
"""

from __future__ import annotations

from typing import Any, Callable, Dict

from gnce.gn_kernel.regimes.register import register_regime


def _load_applicability() -> Callable[[dict], bool]:
    """Return an applicability callable from this package, with safe fallbacks."""
    try:
        from .applicability import applicable  # preferred
        return applicable
    except Exception:
        pass

    # Common alternates in older / inconsistent regime folders
    for name in ("is_applicable", "applies", "isApplicable", "is_applicability"):
        try:
            mod = __import__(__name__.rsplit(".", 1)[0] + ".applicability", fromlist=[name])
            fn = getattr(mod, name)
            if callable(fn):
                return fn
        except Exception:
            continue

    # Last resort: apply when industry looks like ecommerce/marketplace/retail
    def _fallback(payload: dict) -> bool:
        industry = str((payload or {}).get("industry_id") or "").upper()
        return industry in {"ECOMMERCE", "MARKETPLACE", "RETAIL"} or "ECOMMERCE" in industry

    return _fallback


def register() -> None:
    from .resolver import resolve  # must exist

    applicability = _load_applicability()

    register_regime(
        regime_id="ECOMMERCE_TRANSACTION_INTEGRITY",
        display_name="E-Commerce Transaction Integrity",
        domain="ECOMMERCE_TRANSACTION_INTEGRITY",
        framework="Transaction Integrity Controls",
        regime_type="INTEGRITY",
        jurisdiction="GLOBAL",
        enforceable=True,
        l4_executable=True,
        authority="GNCE Transaction Integrity Registry",
        applicability=applicability,
        resolver=resolve,
    )
