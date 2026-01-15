# ui/components/forensic_inspector.py
from __future__ import annotations

from typing import Dict, Any, List

import streamlit as st
import pandas as pd


def _safe_get_timeline(adra: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Try to retrieve the kernel execution timeline from:
      1. adra["kernel_execution_timeline"]
      2. adra["governance_context"]["chain_of_custody"]["timeline_events"]
    """
    if not isinstance(adra, dict):
        return []

    # 1) Direct kernel_execution_timeline (preferred)
    tl = adra.get("kernel_execution_timeline")
    if isinstance(tl, list):
        return tl

    # 2) Fallback via governance_context.chain_of_custody.timeline_events
    gc = adra.get("governance_context") or {}
    coc = gc.get("chain_of_custody") or {}
    tl2 = coc.get("timeline_events")
    if isinstance(tl2, list):
        return tl2

    return []

def _render_constitution_trail(adra: Dict[str, Any]) -> None:
    """
    Renders the kernel_execution_timeline as a compact vertical “constitution trail”
    PLUS an optional full-detail table view for long runs.
    """

    st.markdown("### ⏱️ Constitutional Execution Trail (Kernel Timeline)")

    timeline = _safe_get_timeline(adra)
    if not timeline:
        st.info(
            "No `kernel_execution_timeline` found on this ADRA. "
            "Run GNCE with the v0.5 kernel wiring to populate the temporal chain of custody."
        )
        return

    # Normalise into a DataFrame
    df = pd.DataFrame(timeline)

    # Ensure columns exist
    if "ts_utc" not in df.columns:
        df["ts_utc"] = ""
    if "stage" not in df.columns:
        df["stage"] = ""
    if "detail" not in df.columns:
        df["detail"] = ""

    # Sort by timestamp (just in case) and prettify timestamps
    try:
        df = df.sort_values("ts_utc", ascending=True)
    except Exception:
        pass

    def _pretty_ts(raw: Any) -> str:
        s = str(raw or "")
        if not s:
            return ""
        # strip microseconds if present
        if "." in s:
            s = s.split(".")[0]
        return s

    df["ts_pretty"] = df["ts_utc"].apply(_pretty_ts)

    # Band classification for quick reading
    def _band_for_stage(stage: str) -> str:
        su = (stage or "").upper()
        if su.startswith("REQUEST"):
            return "Request"
        if su.startswith("L0"):
            return "L0 — Input Integrity"
        if su.startswith("L1"):
            return "L1 — Constitutional Verdict"
        if su.startswith("L2"):
            return "L2 — Snapshot & Hash"
        if su.startswith("L3") or su.startswith("L4"):
            return "L3/L4 — Policy & Lineage"
        if su.startswith("L5"):
            return "L5 — CET / Integrity"
        if su.startswith("L6"):
            return "L6 — Drift"
        if su.startswith("L7"):
            return "L7 — Veto"
        if "ADRA_ASSEMBLED" in su:
            return "ADRA Assembly"
        return "Other"

    df["band"] = df["stage"].apply(_band_for_stage)

    # Summary chips
    first_ts = df["ts_pretty"].iloc[0] if len(df) else "N/A"
    last_ts = df["ts_pretty"].iloc[-1] if len(df) else "N/A"
    total_steps = len(df)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("First event (UTC)", first_ts)
    with c2:
        st.metric("Last event (UTC)", last_ts)
    with c3:
        st.metric("Total kernel stages", total_steps)

    st.markdown("---")

    # View toggle: compact timeline vs full table
    view_mode = st.radio(
        "View mode",
        ["Timeline (compact)", "Table (full detail)"],
        horizontal=True,
        key="kernel_timeline_view_mode",
    )

    # -----------------------------
    # 1) COMPACT TIMELINE VIEW
    # -----------------------------
    if view_mode.startswith("Timeline"):
        st.markdown("#### Compact timeline")

        for _, row in df.iterrows():
            ts = row.get("ts_pretty", "")
            stage = row.get("stage", "")
            band = row.get("band", "")
            detail = row.get("detail", "")

            # Short detail snippet (truncate long ones)
            snippet = str(detail or "")
            if len(snippet) > 140:
                snippet = snippet[:140] + "…"

            st.markdown(
                f"""
<div style="display:flex; align-items:flex-start; margin-bottom:0.5rem;">
  <div style="width:12px; display:flex; flex-direction:column; align-items:center; margin-right:0.4rem;">
    <div style="width:7px; height:7px; border-radius:999px; background-color:#bbb;"></div>
    <div style="flex:1; width:1px; background:linear-gradient(to bottom, #666, transparent); min-height:14px;"></div>
  </div>
  <div style="flex:1; font-size:0.82rem;">
    <div style="color:#999; font-size:0.75rem;">{ts}</div>
    <div style="font-weight:600; margin-top:0.05rem;">{stage}</div>
    <div style="color:#aaa; font-size:0.75rem; margin-top:0.05rem;">{band}</div>
    <div style="margin-top:0.1rem; font-size:0.8rem; color:#ccc;">{snippet}</div>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )

        st.caption(
            "Timeline view shows a **compact, scrollable rail** of stages. "
            "Use the table view for full details or filtering."
        )

    # -----------------------------
    # 2) FULL TABLE VIEW (+ filter)
    # -----------------------------
    else:
        st.markdown("#### Full kernel timeline (table)")

        # Small filter for ultra-long runs
        filter_mode = st.selectbox(
            "Filter stages",
            ["All stages", "L6/L7 only – Drift & Veto"],
            index=0,
            key="kernel_timeline_filter_mode",
        )

        filtered_df = df.copy()
        if filter_mode.startswith("L6/L7"):
            su = filtered_df["stage"].astype(str).str.upper()
            mask = su.str.startswith("L6") | su.str.startswith("L7")
            filtered_df = filtered_df[mask]

        if filtered_df.empty:
            st.info("No stages match the current filter.")
            return

        table_df = filtered_df[["ts_pretty", "stage", "band", "detail"]].rename(
            columns={
                "ts_pretty": "Timestamp (UTC)",
                "stage": "Stage",
                "band": "Band",
                "detail": "Detail",
            }
        )

        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "Use the filter above to quickly zoom into L6/L7 (drift + veto) events "
            "when the kernel trail becomes very long."
        )

def _render_header_summary(adra: Dict[str, Any]) -> None:
    """
    Small header summary so the forensic inspector feels anchored to a specific ADRA.
    """
    adra_id = adra.get("adra_id", "unknown")
    ver = adra.get("GNCE_version", "unknown")

    l1 = adra.get("L1_the_verdict_and_constitutional_outcome") or {}
    l6 = adra.get("L6_behavioral_drift_and_monitoring") or {}
    l7 = adra.get("L7_veto_and_execution_feedback") or {}

    decision = l1.get("decision_outcome", "N/A")
    severity = str(l1.get("severity", "UNKNOWN")).upper()
    drift_outcome = str(
        adra.get("drift_outcome") or l6.get("drift_outcome") or "NO_DRIFT"
    ).upper()
    veto_triggered = bool(
        l7.get("veto_path_triggered")
        or l7.get("veto_triggered")
        or not l7.get("execution_authorized", True)
    )

    chain = (adra.get("governance_context") or {}).get("chain_of_custody") or {}
    received_ts = chain.get("request_received_utc", "N/A")

    st.subheader("🔍 Forensic Inspector (Single ADRA)")
    st.caption(f"ADRA ID: `{adra_id}` · GNCE v{ver}")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Decision", decision)
    with c2:
        st.metric("Severity", severity)
    with c3:
        st.metric("Drift outcome", drift_outcome)
    with c4:
        st.metric("Veto path", "YES" if veto_triggered else "NO")

    st.caption(f"Request received (L2 provenance): `{received_ts}`")


def _render_raw_layer_peek(adra: Dict[str, Any]) -> None:
    """
    Very small helper to let you peek into L0, L1, L4 quickly.
    """
    with st.expander("🧬 Layer snapshot (L0, L1, L4)", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**L0 — Pre-execution validation**")
            st.json(adra.get("L0_pre_execution_validation") or {}, expanded=False)
        with col2:
            st.markdown("**L1 — verdict**")
            st.json(adra.get("L1_the_verdict_and_constitutional_outcome") or {}, expanded=False)
        with col3:
            st.markdown("**L4 — Policy lineage & constitution**")
            st.json(adra.get("L4_policy_lineage_and_constitution") or {}, expanded=False)


def _render_compare_selector(
    active_adra_id: str | None,
    adra_store: Dict[str, Any],
) -> None:
    """
    Optional: allow the user to select another ADRA to compare high-level fields with.
    Keeps it light and non-intrusive.
    """
    if not adra_store:
        return

    with st.expander("🧪 Compare with another ADRA (quick diff)", expanded=False):
        ids = list(adra_store.keys())
        if not ids:
            st.info("No other ADRAs stored in this session.")
            return

        default_index = 0
        if active_adra_id and active_adra_id in ids:
            # if current ADRA is in the list, pick a different default if possible
            default_index = 0 if ids[0] != active_adra_id else (1 if len(ids) > 1 else 0)

        compare_id = st.selectbox(
            "Select another ADRA ID to compare against:",
            options=ids,
            index=default_index,
            key="forensic_compare_adra_id",
        )

        if not compare_id:
            return

        base = adra_store.get(active_adra_id) if active_adra_id else None
        other = adra_store.get(compare_id)

        if not isinstance(base, dict) or not isinstance(other, dict):
            st.info("One of the selected ADRAs is not available.")
            return

        base_l1 = base.get("L1_the_verdict_and_constitutional_outcome") or {}
        other_l1 = other.get("L1_the_verdict_and_constitutional_outcome") or {}

        base_dec = base_l1.get("decision_outcome", "N/A")
        base_sev = str(base_l1.get("severity", "UNKNOWN")).upper()

        other_l1_sev = str(other_l1.get("severity", "UNKNOWN")).upper()
        other_dec = other_l1.get("decision_outcome", "N/A")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Current ADRA** (`{active_adra_id}`)")
            st.metric("Decision", base_dec)
            st.metric("Severity", base_sev)
        with c2:
            st.markdown(f"**Compared ADRA** (`{compare_id}`)")
            st.metric("Decision", other_dec)
            st.metric("Severity", other_l1_sev)


# -------------------------------------------------------------------
#  Public entrypoint used by gn_app.py
# -------------------------------------------------------------------

def render_forensic_inspector(
    active_adra: Dict[str, Any],
    adra_store: Dict[str, Any],
) -> None:
    """
    Forensic Inspector v0.5

    - Anchors on a single ADRA (the one currently in view).
    - Shows header summary (decision, severity, drift, veto).
    - Renders the ⏱️ Constitutional Execution Trail (kernel timeline).
    - Offers quick layer snapshots (L0, L1, L4).
    - Optional ADRA-to-ADRA quick diff for operators.
    """
    if not isinstance(active_adra, dict):
        st.info("Forensic Inspector: no active ADRA available.")
        return

    active_adra_id = active_adra.get("adra_id")

    _render_header_summary(active_adra)
    st.markdown("---")

    # ⏱️ Temporal chain of custody / constitution trail
    _render_constitution_trail(active_adra)

    st.markdown("---")
    _render_raw_layer_peek(active_adra)

    st.markdown("---")
    _render_compare_selector(active_adra_id, adra_store)
