# gnce/ui/operations_governance_console/utils/viz.py
from __future__ import annotations

from typing import Any, Dict, List
import pandas as pd
import altair as alt

# Governance semantic palette (stable)
GNCE_VERDICT_DOMAIN = ["ALLOW", "DENY", "UNKNOWN"]
GNCE_VERDICT_RANGE = [
    "#10B981",  # ALLOW (green)
    "#EF4444",  # DENY (red)
    "#64748B",  # UNKNOWN (muted slate)
]


PII_KEYS = {
    "name", "full_name", "email", "phone", "mobile", "address",
    "id_number", "ssn", "passport", "dob", "date_of_birth",
    "ip", "ip_address", "device_id",
}

def redact_obj(obj: Any) -> Any:
    """Best-effort recursive redaction for UI display."""
    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            if str(k).lower() in PII_KEYS:
                out[k] = "REDACTED"
            else:
                out[k] = redact_obj(v)
        return out
    if isinstance(obj, list):
        return [redact_obj(x) for x in obj]
    return obj

def verdict_color_scale() -> alt.Scale:
    return alt.Scale(domain=GNCE_VERDICT_DOMAIN, range=GNCE_VERDICT_RANGE)

def verdict_color(field: str = "verdict:N", title: str = "Verdict") -> alt.Color:
    return alt.Color(
        field,
        scale=verdict_color_scale(),
        sort=GNCE_VERDICT_DOMAIN,
        legend=alt.Legend(title=title),
    )

def entries_to_df(entries: List[Dict[str, Any]]) -> pd.DataFrame:
    """Convert normalized/coerced entries to a small dataframe used by charts."""
    rows = []
    for e in entries or []:
        if not isinstance(e, dict):
            continue
        ts = e.get("time") or e.get("timestamp_utc") or e.get("_dt")
        verdict = (e.get("verdict") or e.get("decision") or e.get("_verdict") or "UNKNOWN")
        verdict = str(verdict).upper().strip()
        if verdict not in ("ALLOW", "DENY"):
            verdict = "UNKNOWN"
        rows.append({"time": ts, "verdict": verdict})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["time"] = pd.to_datetime(df["time"], errors="coerce", utc=True)
    df = df.dropna(subset=["time"])
    return df
