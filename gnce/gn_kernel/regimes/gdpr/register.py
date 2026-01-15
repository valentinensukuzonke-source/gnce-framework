"""
gnce/gn_kernel/regimes/gdpr/register.py

GDPR regime registration (live-wired, autodiscover-safe).

Why this patch exists
- Your new autodiscover registry loader imports each regime package and calls `register()`.
- GDPR was either not registering at all (so REGIME_REGISTRY had no "GDPR"),
  or it registered with a non-callable resolver (so it was effectively a stub).
- GNCE's `register_regime(...)` API has evolved; this file supports the current adapter
  by calling it in the most compatible way: (regime_id, spec_dict).

Key guarantees
- `register()` is present and safe to call multiple times.
- Works whether the caller passes a registry dict or not.
- Avoids importing non-existent symbols from gdpr/applicability.py.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def _upper(x: Any) -> str:
    return str(x or "").strip().upper().replace(" ", "_").replace("-", "_")


def _meta(payload: Dict[str, Any]) -> Dict[str, Any]:
    return (payload.get("meta") or {})


def applicability(payload: Dict[str, Any]) -> bool:
    """
    Minimal, safe GDPR applicability.

    GDPR generally applies when:
    - jurisdiction is EU (or UK in your system’s simplification), OR
    - the payload indicates GDPR-relevant risk categories (e.g., unlawful export / no lawful basis),
      even if jurisdiction is not explicitly set.

    This is intentionally conservative: it returns True when there is a reasonable GDPR surface,
    but does NOT attempt to determine real-world applicability for every country.
    """
    m = _meta(payload)
    j = _upper(m.get("jurisdiction"))

    if j in {"EU", "UK"}:
        return True

    risk = (payload.get("risk_indicators") or {})
    vc = _upper(risk.get("violation_category"))
    if vc in {"DATA_EXPORT_NONCOMPLIANT", "UNAPPROVED_EXPORT", "UNAUTHORIZED_ACCESS"}:
        return True

    # Export payloads frequently imply personal data movement.
    if payload.get("action") == "EXPORT_DATA" and payload.get("export"):
        return True

    return False


def register(registry: Optional[dict] = None) -> None:
    """
    Register GDPR in the global GNCE regime registry.

    `registry` is accepted for backward compatibility but not required
    (GNCE stores regimes in gnce.gn_kernel.regimes.register.REGIME_REGISTRY).
    """
    # Import here to avoid import-time side effects during discovery.
    from gnce.gn_kernel.regimes.register import register_regime
    from .resolver import resolve

    spec = {
        # NOTE: The core registry will normalize/merge these fields into its standard record.
        "regime_id": "GDPR",
        "display_name": "GDPR (General Data Protection Regulation)",
        "domain": "GDPR",
        "framework": "EU Privacy & Data Protection",
        "regime_type": "LAW",
        "jurisdiction": "EU",
        "enforceable": True,
        "l4_executable": True,  # live-wired (resolver is callable)
        "authority": "EU",
        "applicability": applicability,
        "resolver": resolve,
    }

    # Most compatible call style for your current register_regime adapter:
    #   register_regime(regime_id, spec_dict)
    # (Also works with older adapters that accept (regime_id, spec_dict) directly.)
    register_regime("GDPR", spec)


__all__ = ["register", "applicability"]
