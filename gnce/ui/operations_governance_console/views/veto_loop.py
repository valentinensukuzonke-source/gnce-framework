# gnce/ui/operations_governance_console/views/veto_loop.py
from __future__ import annotations

from typing import Any, Dict, List
import html as _html

import streamlit as st
import pandas as pd
import altair as alt

def _info_icon(text: str, *, bg: str = "rgba(239,68,68,0.85)") -> str:
    tip = _html.escape(text).replace("\n", "&#10;")
    return (
        f'<span title="{tip}" '
        f'style="cursor:help;display:inline-flex;align-items:center;justify-content:center;'
        f'width:16px;height:16px;border-radius:999px;background:{bg};'
        f'color:rgba(255,255,255,0.95);font-size:11px;font-weight:900;line-height:1;'
        f'user-select:none;">i</span>'
    )

def _as_upper(x: Any) -> str:
    return "" if x is None else str(x).upper().strip()

def _extract_veto_layer(e: Dict[str, Any]) -> str:
    for k in ("veto_layer", "_veto_layer", "veto_origin_layer", "origin_layer"):
        v = e.get(k)
        if v:
            return str(v)
    env = e.get("_envelope") or {}
    if isinstance(env, dict):
        l7 = env.get("L7_veto_and_execution_feedback") or {}
        if isinstance(l7, dict):
            v = l7.get("veto_origin_layer") or l7.get("origin_layer")
            if v:
                return str(v)
    return "UNKNOWN"

def _extract_clause(e: Dict[str, Any]) -> str:
    for k in ("veto_clause", "clause", "_clause", "article"):
        v = e.get(k)
        if v:
            return str(v)
    env = e.get("_envelope") or {}
    if isinstance(env, dict):
        l4 = env.get("L4_policy_lineage_and_constitution") or {}
        if isinstance(l4, dict):
            policies = l4.get("policies_triggered") or []
            if isinstance(policies, list) and policies:
                violated = [
                    p for p in policies
                    if isinstance(p, dict)
                    and _as_upper(p.get("status")) == "VIOLATED"
                    and p.get("article")
                ]
                if violated:
                    return str(violated[0].get("article"))
                first = next((p for p in policies if isinstance(p, dict) and p.get("article")), None)
                if first:
                    return str(first.get("article"))
    return "—"

def _extract_const_hash(e: Dict[str, Any]) -> str:
    v = e.get("constitution_hash") or e.get("_constitution_hash")
    if v:
        return str(v)
    env = e.get("_envelope") or {}
    if isinstance(env, dict):
        l4 = env.get("L4_policy_lineage_and_constitution") or {}
        if isinstance(l4, dict) and l4.get("constitution_hash"):
            return str(l4.get("constitution_hash"))
    return "—"

def _build_accountability_df(entries: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for e in entries or []:
        verdict = _as_upper(e.get("verdict") or e.get("decision") or e.get("_verdict"))
        if verdict != "DENY":
            continue
        rows.append({
            "veto_layer": _extract_veto_layer(e),
            "clause": _extract_clause(e),
            "constitution_hash": _extract_const_hash(e),
        })

    if not rows:
        return pd.DataFrame(columns=["veto_layer", "clause", "constitution_hash", "deny_count", "attribution"])

    df = pd.DataFrame(rows)
    agg = (
        df.groupby(["veto_layer", "clause", "constitution_hash"], as_index=False)
        .size()
        .rename(columns={"size": "deny_count"})
        .sort_values("deny_count", ascending=False)
    )

    def _attrib(row) -> str:
        if row["veto_layer"] == "UNKNOWN" or row["clause"] == "—" or row["constitution_hash"] == "—":
            return "⚠ Missing"
        return "✅ Attributed"

    agg["attribution"] = agg.apply(_attrib, axis=1)
    return agg

def render_veto_loop(entries: List[Dict[str, Any]], *, depth: str = "Standard") -> None:
    st.markdown("## 🟥 Loop 3 — Veto Accountability & Escalation Oversight (VAEO)")
    st.caption("Tracks veto activations, origin layers/clauses, and escalation quality. Regulator-grade evidence. Read-only.")

    total = len(entries or [])
    denies = [
        e for e in (entries or [])
        if _as_upper(e.get("verdict") or e.get("decision") or e.get("_verdict")) == "DENY"
    ]
    deny_count = len(denies)

    st.caption(f"Scope: {deny_count} DENY ADRAs (of {total} total). Accountability is derived from recorded veto attribution fields.")

    acc = _build_accountability_df(entries)
    top_layer = str(acc.iloc[0]["veto_layer"]) if not acc.empty else "—"
    top_clause = str(acc.iloc[0]["clause"]) if not acc.empty else "—"

    c1, c2, c3 = st.columns(3)
    c1.metric("DENY Count", str(deny_count))
    c2.metric("Top Veto Layer", top_layer)
    c3.metric("Top Clause", top_clause)

    st.markdown(
        "**Accountability Ledger (DENY evidence)** "
        + _info_icon(
            "Groups DENY ADRAs by veto_layer + clause + constitution_hash.\n"
            "UNKNOWN indicates missing attribution metadata (not a separate verdict).\n"
            "Recommendation: emit constitution_hash + veto_origin_layer + violated article in ADRA.",
            bg="rgba(239,68,68,0.85)",
        ),
        unsafe_allow_html=True,
    )

    if deny_count == 0:
        st.info("No DENY evidence in the selected scope — veto accountability ledger is empty.", icon="ℹ️")
        st.divider()
        return

    st.dataframe(acc.head(50), use_container_width=True, hide_index=True)

    st.markdown("**Top accountability findings (ranked)**")
    topn = acc.head(5).to_dict("records")
    cols = st.columns(len(topn))
    for col, row in zip(cols, topn):
        veto_layer = str(row["veto_layer"])
        clause = str(row["clause"])
        ch = str(row["constitution_hash"])
        cnt = int(row["deny_count"])
        attribution = str(row["attribution"])

        is_unknown = (veto_layer == "UNKNOWN" or clause == "—" or ch == "—")
        bg = "rgba(100,116,139,0.22)" if is_unknown else "rgba(239,68,68,0.16)"
        border = "rgba(100,116,139,0.35)" if is_unknown else "rgba(239,68,68,0.35)"

        col.markdown(
            f"""<div style="padding:12px;border-radius:14px;border:1px solid {border};background:{bg};">
                <div style="font-weight:800;font-size:14px;">{_html.escape(veto_layer)}</div>
                <div style="opacity:0.85;font-size:12px;">Clause: {_html.escape(clause)}</div>
                <div style="opacity:0.85;font-size:12px;">Const: {_html.escape(ch)}</div>
                <div style="margin-top:8px;font-weight:900;font-size:18px;">{cnt}</div>
                <div style="opacity:0.85;font-size:12px;">{_html.escape(attribution)}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    with st.expander("📊 Chart view (optional)", expanded=False):
        df_layer = (
            acc.groupby("veto_layer", as_index=False)["deny_count"]
            .sum()
            .sort_values("deny_count", ascending=False)
            .head(10)
        )
        if df_layer.empty:
            st.info("No attributable veto layers to chart.", icon="ℹ️")
        else:
            hover = alt.selection_point(fields=["veto_layer"], on="mouseover", empty=False)
            bars = alt.Chart(df_layer).mark_bar(cornerRadius=6).encode(
                y=alt.Y("veto_layer:N", sort="-x", title=None),
                x=alt.X("deny_count:Q", title="DENY count"),
                color=alt.condition(
                    alt.datum.veto_layer == "UNKNOWN",
                    alt.value("#64748B"),
                    alt.value("#EF4444"),
                ),
                opacity=alt.condition(
                    alt.datum.veto_layer == "UNKNOWN",
                    alt.value(0.35),
                    alt.value(0.9),
                ),
                tooltip=[
                    alt.Tooltip("veto_layer:N", title="Veto layer"),
                    alt.Tooltip("deny_count:Q", title="DENY count"),
                ],
            ).add_params(hover).encode(
                opacity=alt.condition(hover, alt.value(1.0), alt.value(0.75))
            )

            labels = alt.Chart(df_layer).mark_text(align="left", baseline="middle", dx=6, fontSize=12).encode(
                y=alt.Y("veto_layer:N", sort="-x"),
                x="deny_count:Q",
                text="deny_count:Q",
            )

            chart = (bars + labels).properties(height=260).configure_view(strokeOpacity=0).configure_axis(gridOpacity=0.12)
            st.altair_chart(chart, use_container_width=True)

    st.divider()
