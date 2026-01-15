from __future__ import annotations
from typing import Any, Dict

def is_applicable(ctx: Dict[str, Any]) -> bool:
    # Keep it conservative. Example:
    return bool((ctx or {}).get("org") or (ctx or {}).get("system"))
