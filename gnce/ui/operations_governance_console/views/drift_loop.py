# gnce/ui/operations_governance_console/views/drift_loop.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import html

import streamlit as st
import pandas as pd
import altair as alt

from ..models.drift import drift_summary
from ..utils.viz import entries_to_df

# --- Canonical palette (GREEN / RED / muted slate) ---
VERDICT_DOMAIN = ["ALLOW", "DENY", "UNKNOWN"]
VERDICT_RANGE = ["#10B981", "#EF4444", "#94A3B8"]  # allow, deny, unknown

def _info_icon(tooltip: str, *, bg: str = "rgba(148,163,184,0.35)") -> None:
    """
    Small filled circle 'i' with a native hover tooltip (title=...).
    """
    tip = html.escape(str(tooltip or "")).replace("\n", "&#10;")
    st.markdown(
        f"""
        <span title="{tip}"
              style="
                cursor:help;
                display:inline-flex;align-items:center;justify-content:center;
                width:16px;height:16px;
                border-radius:999px;
                background:{bg};
                color:rgba(255,255,255,0.95);
                font-size:11px;font-weight:900;
                line-height:1;
                user-select:none;
              ">i</span>
        """,
        unsafe_allow_html=True,
    )

def _pick_bucket(df: pd.DataFrame) -> str:
    """
    Choose a bucket size that avoids collapsing the whole run into a single point.
    We prefer smoother buckets, but we must preserve >=2 buckets when timestamps vary.
    """
    if df.empty or "time" not in df.columns:
        return "5min"

    tmin = df["time"].min()
    tmax = df["time"].max()
    if pd.isna(tmin) or pd.isna(tmax):
        return "5min"

    span = (tmax - tmin).total_seconds()

    # Heuristic buckets by span
    if span <= 60:
        return "1s"
    if span <= 10 * 60:
        return "30s"
    if span <= 2 * 60 * 60:
        return "1min"
    if span <= 8 * 60 * 60:
        return "5min"
    return "15min"

def _build_trend(df2: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
    """
    Return (trend_df, bucket_str). Ensures we always have a visible time-series.
    """
    bucket = _pick_bucket(df2)
    for candidate in [bucket, "30s", "10s", "1s"]:
        try:
            tmp = df2.copy()
            tmp["bucket"] = tmp["time"].dt.floor(candidate)
            trend = tmp.groupby(["bucket", "verdict"]).size().reset_index(name="count")
            if trend["bucket"].nunique() >= 2 or df2["time"].nunique() <= 1:
                return trend, candidate
        except Exception:
            continue

    # Fallback: no floor (raw timestamps)
    trend = df2.groupby(["time", "verdict"]).size().reset_index(name="count").rename(columns={"time": "bucket"})
    return trend, "raw"

def _nice_line_chart(trend: pd.DataFrame, *, height: int = 220) -> alt.Chart:
    scale = alt.Scale(domain=VERDICT_DOMAIN, range=VERDICT_RANGE)

    # Ensure the legend / colors are stable even when a class is missing
    trend = trend.copy()
    trend["verdict"] = pd.Categorical(trend["verdict"], categories=VERDICT_DOMAIN, ordered=True)

    base = (
        alt.Chart(trend)
        .mark_line(point=alt.OverlayMarkDef(size=70), strokeWidth=2)
        .encode(
            x=alt.X("bucket:T", title="Time", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("count:Q", title="Count"),
            color=alt.Color("verdict:N", scale=scale, legend=alt.Legend(title="Verdict")),
            tooltip=[
                alt.Tooltip("bucket:T", title="Bucket"),
                alt.Tooltip("verdict:N", title="Verdict"),
                alt.Tooltip("count:Q", title="Count"),
            ],
        )
        .properties(height=height)
    )
    # Subtle grid for dark UI
    return base.configure_axis(gridColor="rgba(148,163,184,0.18)", tickColor="rgba(148,163,184,0.35)")

def render_drift_loop(entries: List[Dict[str, Any]], depth: str = "Standard") -> None:
    """
    Loop 1 — GSDS
    """
    st.markdown("## 🔁 Loop 1 — Governance Stability & Drift Surveillance (GSDS)")
    st.caption("Monitors instability signals (DENY excursions, veto dispersion, constitution churn). Read-only.")

    depth = (depth or "Standard").strip().title()
    if depth not in ("Summary", "Standard", "Deep"):
        depth = "Standard"

    # Model summary (notes + churn signals, etc.)
    s = drift_summary(entries) if entries else {
        "risk": "GREEN",
        "deny_rate": "0.0",
        "constitution_hash_churn": 0,
        "notes": ["No evidence loaded."],
    }

    df = entries_to_df(entries or [])
    total = int(len(df))

    # Compute counts (and keep them consistent across all Loop 1 widgets)
    verdict_counts = df["verdict"].fillna("UNKNOWN").astype(str).str.upper().value_counts().to_dict() if not df.empty else {}
    allow_n = int(verdict_counts.get("ALLOW", 0))
    deny_n = int(verdict_counts.get("DENY", 0))
    unk_n = int(verdict_counts.get("UNKNOWN", 0))

    denom = max(allow_n + deny_n, 0)
    deny_rate = (deny_n / denom * 100.0) if denom > 0 else 0.0

    # Risk band: regulator-simple thresholds
    if denom == 0:
        risk = "AMBER" if total > 0 else "GREEN"
    elif deny_rate >= 25.0:
        risk = "RED"
    elif deny_rate >= 10.0:
        risk = "AMBER"
    else:
        risk = "GREEN"

    st.caption(f"Scope: {total} ADRAs in loaded evidence. DENY rate uses DENY/(ALLOW+DENY) (UNKNOWN excluded).")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Drift Risk", risk)
    c2.metric("DENY Rate", f"{deny_rate:.1f}%")
    c3.metric("ALLOW / DENY / UNKNOWN", f"{allow_n} / {deny_n} / {unk_n}")
    c4.metric("Runs Observed", str(total))

    st.markdown("**Notes / Findings:**")
    for note in (s.get("notes") or []):
        st.write(f"- {note}")

    if depth == "Summary":
        st.divider()
        return

    # Guard: need timestamps to chart
    if df.empty or "time" not in df.columns:
        st.info("No timestamp evidence available for trend charts.", icon="ℹ️")
        st.divider()
        return

    df2 = df.dropna(subset=["time"]).copy()
    df2["time"] = pd.to_datetime(df2["time"], errors="coerce")
    df2 = df2.dropna(subset=["time"])
    df2["verdict"] = df2["verdict"].fillna("UNKNOWN").astype(str).str.upper()
    df2.loc[~df2["verdict"].isin(VERDICT_DOMAIN), "verdict"] = "UNKNOWN"

    st.markdown("### Verdict trend (ALLOW/DENY/UNKNOWN)")
    cols = st.columns([0.95, 0.05])
    with cols[1]:
        _info_icon(
            "Shows decision counts over time.\n"
            "Buckets are chosen automatically to avoid collapsing the run into a single point.\n"
            "UNKNOWN means the verdict field was missing or unparsable in the evidence."
        )

    if df2.empty:
        st.info("No valid timestamps found after parsing.", icon="ℹ️")
    else:
        trend, bucket_used = _build_trend(df2)

        # Stable ordering (and fill missing verdicts with 0 for smooth lines)
        buckets = sorted(trend["bucket"].unique())
        idx = pd.MultiIndex.from_product([buckets, VERDICT_DOMAIN], names=["bucket", "verdict"])
        tmp = trend.set_index(["bucket", "verdict"]).reindex(idx, fill_value=0).reset_index()

        chart = _nice_line_chart(tmp, height=220)
        st.altair_chart(chart, use_container_width=True)
        st.caption(f"Bucket size: {bucket_used}.")

    # Top veto-origin layers from DENY decisions (if present in normalized entries)
    if "veto_layer" in df.columns:
        den_df = df[df["verdict"].astype(str).str.upper() == "DENY"].copy()
        if not den_df.empty:
            den_df["veto_layer"] = den_df["veto_layer"].fillna("UNKNOWN").astype(str)
            top = den_df["veto_layer"].value_counts().head(12).reset_index()
            top.columns = ["veto_layer", "count"]

            st.markdown("### Top veto-origin layers (from DENY decisions)")
            cols2 = st.columns([0.95, 0.05])
            with cols2[1]:
                _info_icon(
                    "Counts where verdict == DENY grouped by veto attribution.\n"
                    "If this is UNKNOWN, the upstream evidence is missing veto_layer / clause attribution."
                )

            bar = (
                alt.Chart(top)
                .mark_bar(opacity=0.9)
                .encode(
                    x=alt.X("count:Q", title="DENY count"),
                    y=alt.Y("veto_layer:N", sort="-x", title="Veto layer"),
                    tooltip=[alt.Tooltip("veto_layer:N", title="Veto layer"), alt.Tooltip("count:Q", title="DENY count")],
                    color=alt.value("#EF4444"),
                )
                .properties(height=min(320, 26 * len(top) + 40))
                .configure_axis(gridColor="rgba(148,163,184,0.18)", tickColor="rgba(148,163,184,0.35)")
            )
            st.altair_chart(bar, use_container_width=True)
        else:
            st.caption("No DENY decisions in loaded scope — veto layer ranking unavailable.")
    else:
        st.caption("No veto attribution fields in evidence — veto layer ranking unavailable.")

    if depth == "Deep":
        with st.expander("🔎 Deep evidence (raw last entry)", expanded=False):
            st.json(entries[-1] if entries else {})

    st.divider()
