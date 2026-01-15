# ui/components/telemetry_dashboard.py (Simplified Working Version)

from __future__ import annotations

from typing import Dict, Any, List, Tuple, Optional
from collections import Counter
from datetime import datetime

import streamlit as st
import pandas as pd
import altair as alt

from .executive_summary import render_executive_summary

# -------------------------------------------------------------------
# TELEMETRY UTILS (merged from telemetry_utils.py)
# -------------------------------------------------------------------

def _safe_upper(v: Any) -> str:
    return str(v or "").strip().upper()

def _as_bool(v: Any) -> Optional[bool]:
    if isinstance(v, bool):
        return v
    if v is None:
        return None
    s = str(v).strip().lower()
    if s in {"true", "yes", "y", "1"}:
        return True
    if s in {"false", "no", "n", "0"}:
        return False
    return None

def severity_to_score(raw: Any) -> int:
    num_map = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}
    if isinstance(raw, (int, float)):
        label = num_map.get(int(raw), "UNKNOWN")
    else:
        label = _safe_upper(raw)
    mapping = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    return mapping.get(label, 0)

def _parse_iso(ts: Any) -> Optional[datetime]:
    if not ts:
        return None
    if isinstance(ts, datetime):
        return ts
    s = str(ts).strip()
    try:
        s = s.replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except Exception:
        return None

def _adra_for_id(adra_store: Dict[str, Any], adra_id: Optional[str]) -> Dict[str, Any]:
    if not adra_id:
        return {}
    adra = (adra_store or {}).get(adra_id, {}) or {}
    return adra if isinstance(adra, dict) else {}

def _l(adra: Dict[str, Any], key: str) -> Dict[str, Any]:
    blk = (adra or {}).get(key, {}) or {}
    return blk if isinstance(blk, dict) else {}

def _extract_decision_severity(adra: Dict[str, Any], row: Dict[str, Any]) -> Tuple[str, str]:
    l1 = _l(adra, "L1_the_verdict_and_constitutional_outcome")
    decision = (
        l1.get("decision_outcome")
        or l1.get("verdict")
        or l1.get("decision")
        or row.get("Decision")
        or row.get("GNCE Decision")
        or "N/A"
    )
    severity = (
        l1.get("severity")
        or row.get("Severity")
        or row.get("GNCE Severity")
        or "—"
    )
    return _safe_upper(decision) or "N/A", _safe_upper(severity) or "—"

def _extract_drift(adra: Dict[str, Any], row: Dict[str, Any]) -> str:
    l6 = _l(adra, "L6_behavioral_drift_and_monitoring")
    drift = (
        l6.get("drift_outcome")
        or l6.get("status")
        or adra.get("drift_outcome")
        or row.get("Drift")
        or "NO_DRIFT"
    )
    return _safe_upper(drift) or "NO_DRIFT"

def _extract_veto(adra: Dict[str, Any], row: Dict[str, Any]) -> Tuple[Optional[bool], str]:
    l7 = _l(adra, "L7_veto_and_execution_feedback")
    veto_triggered = (
        _as_bool(l7.get("veto_triggered"))
        if "veto_triggered" in l7
        else _as_bool(row.get("Veto Triggered"))
    )
    veto_cat = (
        l7.get("veto_category")
        or l7.get("veto_path_triggered")
        or row.get("Veto category")
        or row.get("Veto Category")
        or ""
    )
    return veto_triggered, _safe_upper(veto_cat)

def _extract_timestamp(adra: Dict[str, Any], row: Dict[str, Any]) -> str:
    ts = (
        row.get("Timestamp (UTC)")
        or adra.get("timestamp_utc")
        or adra.get("created_at_utc")
        or ""
    )
    return str(ts or "—")

# -------------------------------------------------------------------
# CONSTANTS
# -------------------------------------------------------------------

SEVERITY_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
SEVERITY_COLORS = {
    "LOW": "#10B981",        # green
    "MEDIUM": "#F59E0B",     # amber
    "HIGH": "#EF4444",       # red
    "CRITICAL": "#8B5CF6",   # purple
}

# -------------------------------------------------------------------
# TIME WINDOW SELECTOR
# -------------------------------------------------------------------

def render_time_window_selector(
    ledger: List[Dict[str, Any]],
    key_prefix: str = "telemetry",
) -> Tuple[List[Dict[str, Any]], List[str], str]:
    """Time window selector for the Ops Console."""
    if not ledger:
        return [], [], "No ADRAs"

    choice = st.radio(
        "Time window",
        ["Entire session"],
        index=0,
        horizontal=True,
        key=f"{key_prefix}_gn_time_window",
    )

    window_label = "Entire session"
    window_ledger = ledger

    window_ids = [
        row.get("ADRA ID")
        for row in window_ledger
        if row.get("ADRA ID")
    ]

    return window_ledger, window_ids, window_label

# -------------------------------------------------------------------
# EVENT LEDGER TABLE
# -------------------------------------------------------------------

def _build_event_ledger_df(window_ledger: List[Dict[str, Any]], adra_store: Dict[str, Any]) -> pd.DataFrame:
    rows = []
    for r in window_ledger:
        adra_id = r.get("ADRA ID") or r.get("adra_id") or r.get("adraId")
        adra = _adra_for_id(adra_store, adra_id)

        decision, severity = _extract_decision_severity(adra, r)
        drift = _extract_drift(adra, r)
        veto_triggered, veto_category = _extract_veto(adra, r)
        
        if veto_triggered is None:
            veto_triggered = (decision == "DENY") and bool(veto_category) and (veto_category != "NONE")
        
        exec_auth = _as_bool(r.get("Execution authorized"))
        ts = _extract_timestamp(adra, r)

        decision_display = "✅ ALLOW" if decision == "ALLOW" else ("⛔ DENY" if decision == "DENY" else decision)
        severity_display = {
            "LOW": "🟢 LOW",
            "MEDIUM": "🟠 MEDIUM",
            "HIGH": "🔴 HIGH",
            "CRITICAL": "🟣 CRITICAL",
        }.get(severity, severity)

        veto_display = "🚫 YES" if veto_triggered else "✅ NO"
        cet_display = "🔐" if _as_bool(r.get("CET Present")) else "—"

        rows.append({
            "Timestamp (UTC)": ts,
            "ADRA ID": adra_id or "—",
            "Decision": decision_display,
            "Severity": severity_display,
            "Drift": drift,
            "Execution authorized": ("✅ True" if exec_auth else "🚫 False") if exec_auth is not None else "—",
            "Veto triggered": veto_display,
            "Veto category": veto_category or "—",
            "CET": cet_display,
            "CET strategy": r.get("CET Strategy") or "—",
        })

    df = pd.DataFrame(rows)
    if "Timestamp (UTC)" in df.columns:
        parsed = df["Timestamp (UTC)"].apply(_parse_iso)
        df["_ts_sort"] = parsed
        df = df.sort_values(by="_ts_sort", ascending=True).drop(columns=["_ts_sort"])
    return df

# -------------------------------------------------------------------
# OPS CONSOLE
# -------------------------------------------------------------------

def render_operations_console(
    window_ledger: List[Dict[str, Any]],
    window_label: str,
) -> None:
    """Render the operations console."""
    if not window_ledger:
        st.info("No ADRAs in the selected time window.")
        return

    adra_store = st.session_state.get("gn_adra_store", {}) or {}
    window_adra_ids = [
        (row.get("ADRA ID") or row.get("adra_id") or row.get("adraId"))
        for row in window_ledger
        if (row.get("ADRA ID") or row.get("adra_id") or row.get("adraId"))
    ]

    st.markdown(f"### 📊 GNCE Telemetry — {window_label}")

    # Event ledger
    st.markdown("#### 📋 Event Ledger")
    df_events = _build_event_ledger_df(window_ledger, adra_store)
    st.dataframe(df_events, use_container_width=True, hide_index=True)

    with st.expander("Export event ledger (CSV)"):
        csv = df_events.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV",
            data=csv,
            file_name=f"gnce_telemetry_{window_label.replace(' ', '_')}.csv",
            mime="text/csv",
        )

    # Severity distribution
    st.markdown("#### 📈 Severity Distribution")
    sev_counts = Counter(_safe_upper(r.get("Severity", "")) for r in window_ledger)
    df_sev = pd.DataFrame(
        [{"Severity": s, "Count": sev_counts.get(s, 0)} for s in SEVERITY_ORDER]
    )

    chart_sev = (
        alt.Chart(df_sev)
        .mark_bar()
        .encode(
            y=alt.Y("Severity:N", sort=SEVERITY_ORDER),
            x=alt.X("Count:Q", title="ADRAs"),
            color=alt.Color(
                "Severity:N",
                scale=alt.Scale(
                    domain=SEVERITY_ORDER,
                    range=[
                        SEVERITY_COLORS["LOW"],
                        SEVERITY_COLORS["MEDIUM"],
                        SEVERITY_COLORS["HIGH"],
                        SEVERITY_COLORS["CRITICAL"],
                    ],
                ),
            ),
        )
        .properties(height=200)
    )
    st.altair_chart(chart_sev, use_container_width=True)

    # Decision distribution
    st.markdown("#### 🎯 Decision Distribution")
    dec_counts = Counter(_safe_upper(r.get("Decision", "")) for r in window_ledger)
    df_dec = pd.DataFrame([
        {"Decision": "ALLOW", "Count": dec_counts.get("ALLOW", 0)},
        {"Decision": "DENY", "Count": dec_counts.get("DENY", 0)},
        {"Decision": "OTHER", "Count": sum(v for k, v in dec_counts.items() if k not in ["ALLOW", "DENY"])}
    ])

    chart_dec = (
        alt.Chart(df_dec)
        .mark_bar()
        .encode(
            y=alt.Y("Decision:N", sort=["ALLOW", "DENY", "OTHER"]),
            x=alt.X("Count:Q", title="Count"),
            color=alt.Color(
                "Decision:N",
                scale=alt.Scale(
                    domain=["ALLOW", "DENY", "OTHER"],
                    range=["#10B981", "#EF4444", "#6B7280"]
                ),
            ),
        )
        .properties(height=150)
    )
    st.altair_chart(chart_dec, use_container_width=True)

    # Summary statistics
    st.markdown("#### 📊 Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    total_adras = len(window_ledger)
    allow_count = dec_counts.get("ALLOW", 0)
    deny_count = dec_counts.get("DENY", 0)
    allow_rate = (allow_count / total_adras * 100) if total_adras > 0 else 0
    
    with col1:
        st.metric("Total ADRAs", total_adras)
    with col2:
        st.metric("ALLOW", allow_count)
    with col3:
        st.metric("DENY", deny_count)
    with col4:
        st.metric("Allow Rate", f"{allow_rate:.1f}%")

# -------------------------------------------------------------------
# MAIN TELEMETRY FUNCTION
# -------------------------------------------------------------------

def render_gnce_telemetry_v07(ledger: List[Dict[str, Any]]) -> None:
    """
    Main telemetry dashboard function.
    """
    if not ledger:
        st.info("No ledger entries. Run GNCE first.")
        return
    
    adra_store = st.session_state.get("gn_adra_store", {}) or {}
    
    # Simple tab interface
    tab1, tab2 = st.tabs(["📊 Dashboard", "📈 Executive Summary"])
    
    with tab1:
        window_ledger, window_ids, window_label = render_time_window_selector(
            ledger=ledger,
            key_prefix="telemetry_v07",
        )
        render_operations_console(window_ledger=window_ledger, window_label=window_label)
    
    with tab2:
        if ledger:
            window_ledger, window_ids, window_label = render_time_window_selector(
                ledger=ledger,
                key_prefix="executive_summary",
            )
            render_executive_summary(
                ledger=ledger,  # This is correct - ledger is the parameter
                adra_store=adra_store,
                window_adra_ids=window_ids,
                window_label=window_label,
                key_prefix="telemetry_exec_summary"
            )
        else:
            st.info("No ledger data available for executive summary.")