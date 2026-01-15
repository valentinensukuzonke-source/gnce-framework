# gnce/kernel/regimes/dsa/applicability.py
from __future__ import annotations

from typing import Any, Dict


def applies_dsa(ctx: Dict[str, Any]) -> bool:
    """
    DSA applies when the service operates in the EU and is an online platform
    / intermediary service context.

    Conservative rule:
    - market must be explicitly EU
    - service_type/platform_type must match a known online platform / intermediary indicator
    """
    if not isinstance(ctx, dict):
        return False

    market = str(ctx.get("market") or "").strip().upper()
    if market != "EU":
        return False

    service = str(ctx.get("service_type") or ctx.get("platform_type") or "").strip().upper()

    return service in {
        "ONLINE_PLATFORM",
        "SOCIAL_PLATFORM",
        "MARKETPLACE",
        "INTERMEDIARY_SERVICE",
        "HOSTING_SERVICE",
        "VLOP",
    }
