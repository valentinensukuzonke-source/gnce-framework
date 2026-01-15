# ui/components/executive_dashboard.py

import streamlit as st
import pandas as pd
import altair as alt
from typing import List, Dict, Any

SEVERITY_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
SEVERITY_SCORES = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
SEVERITY_COLORS = {
    "LOW": "#00916E",
    "MEDIUM": "#ffb300",
    "HIGH": "#C62828",
    "CRITICAL": "#8b008b",
}


def _score(sev: str) -> int:
    return SEVERITY_SCORES.get(str(sev).upper(), 0)


# --------------------------------------------------------------------
# EXECUTIVE DASHBOARD — GNCE Fleet View
# --------------------------------------------------------------------
def render_executive_dashboard(ledger: List[Dict[str, Any]]):
    """
    LAYER A — FLEET EXECUTIVE OVERVIEW
    High-level risk posture view across last N ADRAs.
    """

    st.header("🛰️ GNCE Fleet Executive Overview")

    if not ledger:
        st.info("No ADRAs recorded yet. Run GNCE to populate telemetry.")
        return

    df = pd.DataFrame(ledger)
    df["Score"] = df["Severity"].apply(_score)

    # ----------------------------------------------------------------
    # A1 — Global Risk Meter
    # ----------------------------------------------------------------
    rolling_window = min(200, len(df))
    df_last = df.tail(rolling_window)

    avg_score = df_last["Score"].mean()

    if avg_score < 1.5:
        band, emoji = "LOW", "🟢"
    elif avg_score < 2.5:
        band, emoji = "MEDIUM", "🟠"
    elif avg_score < 3.5:
        band, emoji = "HIGH", "🔴"
    else:
        band, emoji = "CRITICAL", "🟣"

    st.markdown(
        f"""
        <div style="font-size:1.2rem; margin-top:0.1rem;">
            <strong>Global GNCE Risk Band:</strong>
            <span style="padding:0.25rem 0.7rem;
                         border-radius:12px;
                         border:1px solid rgba(255,255,255,0.25);
                         margin-left:0.4rem;
                         background:rgba(0,0,0,0.3);">
                {emoji} {band}
            </span>
            <span style="opacity:0.6; margin-left:1rem;">
                (based on last {rolling_window} ADRAs)
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ----------------------------------------------------------------
    # A2 — Risk Sparkline (last 200 ADRAs)
    # ----------------------------------------------------------------
    st.markdown("### 📈 Fleet Risk Trend (last 200 ADRAs)")

    spark = (
        alt.Chart(df_last.reset_index())
        .mark_line(color="#3b82f6")
        .encode(
            x=alt.X("index:Q", title="Recent ADRAs"),
            y=alt.Y("Score:Q", title="Severity score"),
        )
        .properties(height=120)
    )
    st.altair_chart(spark, use_container_width=True)

    # ----------------------------------------------------------------
    # A3 — Regime Risk Signatures
    # ----------------------------------------------------------------
    st.markdown("### 🧭 Regime Risk Signatures")

    regimes = ["DSA", "DMA", "AI_ACT", "GDPR"]
    reg_cols = st.columns(len(regimes))

    for idx, r in enumerate(regimes):
        df_reg = df_last[df_last["Articles (all)"].str.contains(r[:3], na=False)]
        score = df_reg["Score"].mean() if not df_reg.empty else 0

        if score < 1.5:
            emoji = "🟢"
        elif score < 2.5:
            emoji = "🟠"
        elif score < 3.5:
            emoji = "🔴"
        else:
            emoji = "🟣"

        reg_cols[idx].markdown(
            f"""
            <div style="padding:0.7rem;
                        border-radius:10px;
                        border:1px solid rgba(255,255,255,0.25);
                        background:#0f172a;">
                <strong>{r}</strong><br>
                {emoji} Risk {score:.1f}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ----------------------------------------------------------------
    # A4 — Domain × Time Heatmap
    # ----------------------------------------------------------------
    st.markdown("### 🔥 Domain × Time Heatmap (risk-weighted)")

    # Expand ledger rows to map each article domain
    rows = []
    for _, row in df_last.iterrows():
        arts = row.get("Articles (all)") or ""
        for a in arts.split(","):
            domain = a.strip().split(" ")[0]
            if domain:
                rows.append(
                    {
                        "Domain": domain,
                        "Risk": _score(row["Severity"]),
                        "Index": row["index"] if "index" in df_last else 0,
                    }
                )

    if rows:
        df_heat = pd.DataFrame(rows)
        heatmap = (
            alt.Chart(df_heat)
            .mark_rect()
            .encode(
                x=alt.X("Index:Q", title="ADRA timeline"),
                y=alt.Y("Domain:N", title="Regulatory Domain"),
                color=alt.Color(
                    "Risk:Q",
                    scale=alt.Scale(
                        domain=[1, 2, 3, 4],
                        range=[
                            SEVERITY_COLORS["LOW"],
                            SEVERITY_COLORS["MEDIUM"],
                            SEVERITY_COLORS["HIGH"],
                            SEVERITY_COLORS["CRITICAL"],
                        ],
                    ),
                ),
            )
            .properties(height=240)
        )
        st.altair_chart(heatmap, use_container_width=True)
    else:
        st.info("No domain activity detected in recent ADRAs.")
