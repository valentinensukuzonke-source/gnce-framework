# ui/components/governance_catalog.py
from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple

import streamlit as st
import pandas as pd
import altair as alt

from gn_kernel.redaction import redact_adra_for_regulator


# --------------------------------------------
# Severity → Color mapping (aligned with GNCE v0.5 UI)
# --------------------------------------------
SEVERITY_COLORS = {
    "LOW": "#00916E",        # green
    "MEDIUM": "#ffb300",     # amber
    "HIGH": "#C62828",       # red
    "CRITICAL": "#8b008b",   # purple
    "UNKNOWN": "#64748b",    # slate/neutral
}

# Governance models mapping
GOVERNANCE_MODELS = {
    "POLICY_TEAM_PRIMARY": "🏢 Policy Team Led",
    "RISK_COMMITTEE": "⚖️ Risk Committee Oversight",
    "AUTOMATED_ONLY": "🤖 Fully Automated",
    "HUMAN_IN_LOOP": "👤 Human-in-the-Loop",
    "ESCALATION_REQUIRED": "⚠️ Escalation Required",
    "UNASSIGNED_REVIEW_POOL": "📋 Review Pool (Unassigned)",
}

# Regime icons for visual distinction
REGIME_ICONS = {
    "DSA": "📰",
    "DMA": "⚖️",
    "GDPR": "🔐",
    "EU AI ACT": "🤖",
    "ISO_42001": "📊",
    "NIST": "🇺🇸",
    "INTERNAL": "⚙️",
    "FINANCIAL": "💰",
    "SECURITY": "🛡️",
}


def _severity_pill(sev: str | None) -> str:
    """Create a styled severity pill with color coding."""
    label = (sev or "UNKNOWN").upper()
    color = SEVERITY_COLORS.get(label, SEVERITY_COLORS["UNKNOWN"])

    return (
        f'<span style="display:inline-flex;align-items:center;gap:0.35rem;'
        f'background:{color}20;padding:4px 10px;border-radius:999px;'
        f'border:1px solid {color}60;color:{color};font-weight:600;'
        f'font-size:0.70rem;letter-spacing:0.04em;text-transform:uppercase;">'
        f'<span style="width:0.40rem;height:0.40rem;border-radius:999px;'
        f'background:{color};"></span>{label}</span>'
    )


def _status_badge(status: str) -> str:
    """Create a styled status badge."""
    status_lower = (status or "").upper()
    
    if status_lower == "VIOLATED":
        color = "#ef4444"
        icon = "⛔"
    elif status_lower == "SATISFIED":
        color = "#22c55e"
        icon = "✅"
    elif status_lower == "NOT_APPLICABLE":
        color = "#94a3b8"
        icon = "📴"
    else:
        color = "#64748b"
        icon = "❓"
    
    return (
        f'<span style="display:inline-flex;align-items:center;gap:0.25rem;'
        f'background:{color}20;padding:2px 8px;border-radius:999px;'
        f'border:1px solid {color}60;color:{color};font-weight:500;'
        f'font-size:0.68rem;">{icon} {status_lower}</span>'
    )


def _get_active_adra() -> Dict[str, Any] | None:
    """
    Fetch the current ADRA from session and apply Regulator Mode redaction
    if enabled (using the same flag as gn_app.py).
    """
    adra = st.session_state.get("current_adra")
    if not isinstance(adra, dict):
        return None

    regulator_mode = bool(st.session_state.get("gnce_regulator_mode", False))
    if regulator_mode:
        try:
            return redact_adra_for_regulator(adra)
        except Exception:
            # In worst case, fall back to raw ADRA – better to show something
            return adra
    return adra


def _extract_governance_context(adra: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safely extract the governance_context, with soft fallbacks so the
    catalog always renders something intelligible.
    """
    if not isinstance(adra, dict):
        return {}

    ctx = adra.get("governance_context")
    if not ctx:
        # Prior naming or future variations
        ctx = adra.get("stewardship_context") or adra.get("accountability")

    if isinstance(ctx, dict):
        return ctx

    # Fallback default surface (if kernel wiring not present)
    return {
        "sovereign_engine_identity": "GNCE Sovereign Constitutional Engine",
        "organizational_owner": "Deployment-Level Policy Team (L4 policy surface)",
        "human_custodian": "Unassigned (Review Pool)",
        "stewardship_tags": {
            "stewardship_model": "POLICY_TEAM_PRIMARY",
            "human_review_anchor": "UNASSIGNED_REVIEW_POOL",
        },
        "verdict_snapshot": {},
        "chain_of_custody": {},
    }


def _build_policy_rows(adra: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Set[str]]:
    """
    Flatten L4 policy lineage into a list of rows for tabular display.
    Returns rows and a set of unique regimes.
    """
    l4 = adra.get("L4_policy_lineage_and_constitution") or {}
    policies = l4.get("policies_triggered") or []
    if not isinstance(policies, list):
        return [], set()

    rows: List[Dict[str, Any]] = []
    regimes: Set[str] = set()
    
    for p in policies:
        if not isinstance(p, dict):
            continue

        domain = p.get("domain") or ""
        regime = p.get("regime") or ""
        article = p.get("article") or ""
        category = p.get("category") or ""
        status = (p.get("status") or "").upper()
        severity = (p.get("severity") or "UNKNOWN").upper()
        detail = p.get("violation_detail") or p.get("finding") or p.get("notes") or ""
        
        if regime:
            regimes.add(regime.upper())
        
        rows.append(
            {
                "Domain": domain,
                "Regime": regime,
                "Article": article,
                "Category": category,
                "Status": status,
                "Severity": severity,
                "Detail": detail,
                "Severity_Rank": {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}.get(severity, 0),
                "_raw": p,  # Keep raw policy for expansion
            }
        )
    
    return rows, regimes


def _summarize_policies(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Simple counts and statistics used for the header summary.
    """
    summary = {
        "total": len(rows),
        "violated": 0,
        "satisfied": 0,
        "not_applicable": 0,
        "by_severity": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
        "by_regime": {},
        "highest_severity": "LOW",
    }
    
    highest_severity_rank = 0
    
    for r in rows:
        status = (r.get("Status") or "").upper()
        severity = (r.get("Severity") or "UNKNOWN").upper()
        regime = r.get("Regime") or "Unknown"
        
        if status == "VIOLATED":
            summary["violated"] += 1
        elif status == "SATISFIED":
            summary["satisfied"] += 1
        elif status in {"NOT_APPLICABLE", "N/A"}:
            summary["not_applicable"] += 1
        
        # Count by severity
        if severity in summary["by_severity"]:
            summary["by_severity"][severity] += 1
            
            # Track highest severity
            severity_rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}.get(severity, 0)
            if severity_rank > highest_severity_rank:
                highest_severity_rank = severity_rank
                summary["highest_severity"] = severity
        
        # Count by regime
        summary["by_regime"][regime] = summary["by_regime"].get(regime, 0) + 1
    
    return summary


def _render_regime_summary_chart(summary: Dict[str, Any]) -> None:
    """Render a simple bar chart showing policies by regime."""
    if not summary.get("by_regime"):
        return
    
    # Prepare data for chart
    regime_data = []
    for regime, count in summary["by_regime"].items():
        icon = REGIME_ICONS.get(regime.upper(), "📄")
        regime_data.append({
            "Regime": f"{icon} {regime}",
            "Policies": count,
            "icon": icon
        })
    
    # Sort by count descending
    regime_data.sort(key=lambda x: x["Policies"], reverse=True)
    
    # Create Altair chart
    df = pd.DataFrame(regime_data)
    
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('Policies:Q', title='Number of Policies'),
        y=alt.Y('Regime:N', sort='-x', title='Regime'),
        color=alt.Color('Policies:Q', scale=alt.Scale(scheme='blues'), legend=None),
        tooltip=['Regime', 'Policies']
    ).properties(
        height=200,
        title='Policies by Regulatory Regime'
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=12
    )
    
    st.altair_chart(chart, use_container_width=True)


def _render_governance_heatmap(rows: List[Dict[str, Any]]) -> None:
    """Render a heatmap showing regime × severity distribution."""
    if not rows:
        return
    
    # Prepare data for heatmap
    heatmap_data = []
    for row in rows:
        regime = row.get("Regime") or "Unknown"
        severity = row.get("Severity") or "UNKNOWN"
        heatmap_data.append({
            "Regime": regime,
            "Severity": severity,
            "Count": 1
        })
    
    df = pd.DataFrame(heatmap_data)
    
    # Aggregate counts
    heatmap_df = df.groupby(["Regime", "Severity"]).size().reset_index(name="Count")
    
    # Order severity
    severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]
    
    chart = alt.Chart(heatmap_df).mark_rect().encode(
        x=alt.X('Severity:N', sort=severity_order, title='Severity'),
        y=alt.Y('Regime:N', title='Regime'),
        color=alt.Color('Count:Q', scale=alt.Scale(scheme='redyellowblue'), legend=alt.Legend(title='Policy Count')),
        tooltip=['Regime', 'Severity', 'Count']
    ).properties(
        height=250,
        title='Regime × Severity Distribution'
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=12
    )
    
    st.altair_chart(chart, use_container_width=True)


def _get_regime_icon(regime: str) -> str:
    """Get appropriate icon for a regime."""
    regime_upper = regime.upper()
    for key, icon in REGIME_ICONS.items():
        if key in regime_upper:
            return icon
    return "📄"


def render_governance_catalog_v05() -> None:
    """
    🏛 Enhanced Unified Governance Catalog v0.5
    
    - Shows governance surface with visual indicators
    - Displays regime distribution with charts
    - Provides detailed policy breakdown with filtering
    - Shows interconnectivity with current ADRA
    """
    
    adra = _get_active_adra()
    if not isinstance(adra, dict):
        st.info("No active ADRA to render the governance catalog.")
        return
    
    ctx = _extract_governance_context(adra)
    rows, regimes = _build_policy_rows(adra)
    summary = _summarize_policies(rows)
    
    # Governance surface bits
    sovereign_engine = ctx.get("sovereign_engine_identity") or "GNCE Sovereign Constitutional Engine"
    organizational_owner = ctx.get("organizational_owner") or "Deployment-Level Policy Team (L4 policy surface)"
    human_custodian = ctx.get("human_custodian") or ctx.get("human_owner") or "Unassigned (Review Pool)"
    
    stewardship_tags = ctx.get("stewardship_tags") or {}
    stewardship_model = stewardship_tags.get("stewardship_model", "POLICY_TEAM_PRIMARY")
    human_anchor = stewardship_tags.get("human_review_anchor", "UNASSIGNED_REVIEW_POOL")
    
    # Get human-readable governance model
    governance_model_display = GOVERNANCE_MODELS.get(stewardship_model, stewardship_model)
    human_anchor_display = GOVERNANCE_MODELS.get(human_anchor, human_anchor)
    
    # Current verdict severity (for header pill)
    l1 = adra.get("L1_the_verdict_and_constitutional_outcome", {}) or {}
    verdict = l1.get("decision_outcome", "UNKNOWN").upper()
    severity = (l1.get("severity") or "UNKNOWN").upper()
    sev_pill_html = _severity_pill(severity)
    
    # Get ADRA metadata
    adra_id = adra.get("adra_id", "UNKNOWN")
    timestamp = adra.get("timestamp_utc", "UNKNOWN")
    
    # -------------------------------------
    # Header with interactive controls
    # -------------------------------------
    st.subheader("🏛 Unified Governance Catalog")
    
    # Create a multi-column header
    col1, col2, col3 = st.columns([3, 2, 1])
    
    with col1:
        st.markdown(f"""
        <div style="font-size:0.9rem; opacity:0.9; margin-bottom: 0.5rem;">
            <strong>Constitutional Governance Surface</strong><br>
            <span style="font-size:0.8rem;">
                Shows all governing regimes, articles, and policy bands applied to this ADRA
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Regime count badge
        regime_count = len(regimes)
        st.markdown(f"""
        <div style="text-align: center;">
            <div style="font-size: 1.2rem; font-weight: bold;">{regime_count}</div>
            <div style="font-size: 0.7rem; opacity: 0.8;">Active Regimes</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Verdict badge
        verdict_color = "#ef4444" if verdict == "DENY" else "#22c55e"
        st.markdown(f"""
        <div style="text-align: center;">
            <div style="font-size: 1.2rem; font-weight: bold; color: {verdict_color}">
                {verdict}
            </div>
            <div style="font-size: 0.7rem; opacity: 0.8;">Verdict</div>
        </div>
        """, unsafe_allow_html=True)
    
    # -------------------------------------
    # Governance Surface Card
    # -------------------------------------
    with st.expander("👑 Governance Surface Details", expanded=True):
        col_g1, col_g2, col_g3 = st.columns(3)
        
        with col_g1:
            st.markdown("**Sovereign Engine**")
            st.code(sovereign_engine, language=None)
        
        with col_g2:
            st.markdown("**Organizational Owner**")
            st.code(organizational_owner, language=None)
        
        with col_g3:
            st.markdown("**Human Custodian**")
            st.code(human_custodian, language=None)
        
        # Governance model tags
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown(f"**Stewardship Model:** {governance_model_display}")
        with col_t2:
            st.markdown(f"**Human Anchor:** {human_anchor_display}")
        
        # ADRA metadata
        st.caption(f"ADRA ID: `{adra_id}` | Timestamp: `{timestamp}`")
    
    # -------------------------------------
    # Quick Stats Dashboard
    # -------------------------------------
    st.markdown("### 📊 Policy Compliance Dashboard")
    
    # Create metrics cards
    cols = st.columns(5)
    
    with cols[0]:
        st.metric("Total Policies", summary["total"])
    
    with cols[1]:
        st.metric("Satisfied", summary["satisfied"], 
                 delta=f"{summary['satisfied']/max(summary['total'],1)*100:.0f}%" if summary["total"] > 0 else "0%")
    
    with cols[2]:
        st.metric("Violated", summary["violated"],
                 delta_color="inverse",
                 delta=f"{summary['violated']/max(summary['total'],1)*100:.0f}%" if summary["total"] > 0 else "0%")
    
    with cols[3]:
        highest_sev = summary["highest_severity"]
        st.metric("Highest Severity", highest_sev)
    
    with cols[4]:
        regime_count = len(summary["by_regime"])
        st.metric("Regimes", regime_count)
    
    # -------------------------------------
    # Visualizations Section
    # -------------------------------------
    if rows:
        tab1, tab2, tab3 = st.tabs(["📋 Policy Details", "📈 Regime Analysis", "🔥 Severity Heatmap"])
        
        with tab1:
            # Filter controls
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                filter_status = st.multiselect(
                    "Filter by Status",
                    options=["VIOLATED", "SATISFIED", "NOT_APPLICABLE"],
                    default=[]
                )
            with col_f2:
                filter_severity = st.multiselect(
                    "Filter by Severity",
                    options=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                    default=[]
                )
            with col_f3:
                filter_regime = st.multiselect(
                    "Filter by Regime",
                    options=sorted(regimes),
                    default=[]
                )
            
            # Apply filters
            filtered_rows = rows
            if filter_status:
                filtered_rows = [r for r in filtered_rows if r["Status"] in filter_status]
            if filter_severity:
                filtered_rows = [r for r in filtered_rows if r["Severity"] in filter_severity]
            if filter_regime:
                filtered_rows = [r for r in filtered_rows if r["Regime"] in filter_regime]
            
            # Display filtered results - FIXED: Added enumerate for unique keys
            if filtered_rows:
                for idx, row in enumerate(filtered_rows):
                    with st.expander(f"{_get_regime_icon(row['Regime'])} {row['Regime']} - Article {row['Article']} ({row['Category']})", expanded=False):
                        col_r1, col_r2, col_r3 = st.columns([2, 1, 1])
                        with col_r1:
                            st.markdown(f"**Domain:** {row['Domain']}")
                        with col_r2:
                            st.markdown(_status_badge(row['Status']), unsafe_allow_html=True)
                        with col_r3:
                            st.markdown(_severity_pill(row['Severity']), unsafe_allow_html=True)
                        
                        if row.get('Detail'):
                            st.markdown(f"**Details:** {row['Detail']}")
                        
                        # Show raw policy data on demand - FIXED: Unique key with idx
                        checkbox_key = f"raw_{row['Domain']}_{row['Regime']}_{row['Article']}_{idx}"
                        if st.checkbox("Show raw policy data", key=checkbox_key):
                            st.json(row.get('_raw', {}))
            else:
                st.info("No policies match the selected filters.")
        
        with tab2:
            _render_regime_summary_chart(summary)
            
            # Regime breakdown table
            if summary["by_regime"]:
                regime_df = pd.DataFrame([
                    {"Regime": regime, "Count": count, "Icon": _get_regime_icon(regime)}
                    for regime, count in summary["by_regime"].items()
                ])
                regime_df = regime_df.sort_values("Count", ascending=False)
                
                # Display as styled table
                for _, row in regime_df.iterrows():
                    col_reg1, col_reg2 = st.columns([1, 3])
                    with col_reg1:
                        st.markdown(f"<h3 style='margin:0;'>{row['Icon']} {row['Count']}</h3>", unsafe_allow_html=True)
                    with col_reg2:
                        st.markdown(f"**{row['Regime']}**")
                        st.progress(min(row['Count'] / summary['total'], 1.0) if summary['total'] > 0 else 0)
        
        with tab3:
            _render_governance_heatmap(rows)
            
            # Severity breakdown
            st.markdown("#### Severity Distribution")
            severity_df = pd.DataFrame([
                {"Severity": sev, "Count": count}
                for sev, count in summary["by_severity"].items() if count > 0
            ])
            
            if not severity_df.empty:
                severity_chart = alt.Chart(severity_df).mark_arc().encode(
                    theta=alt.Theta(field="Count", type="quantitative"),
                    color=alt.Color(field="Severity", type="nominal", 
                                   scale=alt.Scale(domain=list(SEVERITY_COLORS.keys()),
                                                  range=list(SEVERITY_COLORS.values()))),
                    tooltip=["Severity", "Count"]
                ).properties(
                    width=300,
                    height=300,
                    title="Policies by Severity Level"
                )
                st.altair_chart(severity_chart, use_container_width=True)
    
    else:
        st.info("No policy lineage (L4) available to render in the catalog.")
    
    # -------------------------------------
    # Footer with quick actions
    # -------------------------------------
    st.markdown("---")
    col_a1, col_a2, col_a3 = st.columns(3)
    
    with col_a1:
        if st.button("📋 Export to CSV", use_container_width=True):
            if rows:
                df_export = pd.DataFrame(rows)
                # Remove internal columns before export
                df_export = df_export.drop(columns=['Severity_Rank', '_raw'], errors='ignore')
                csv = df_export.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"governance_catalog_{adra_id}.csv",
                    mime="text/csv",
                )
    
    with col_a2:
        if st.button("🔄 Refresh View", use_container_width=True):
            st.rerun()
    
    with col_a3:
        if st.button("📚 View in ADRA Browser", use_container_width=True):
            st.session_state["adara_browser_target"] = adra_id
            st.toast("Navigating to ADRA Browser...")
            # Note: The actual navigation would be handled by the parent app
            st.info("Switch to the ADRA Browser tab to view this ADRA")