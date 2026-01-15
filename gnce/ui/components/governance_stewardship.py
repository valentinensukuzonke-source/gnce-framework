# ui/components/governance_context.py
from __future__ import annotations

from typing import Dict, Any, List, Optional
import json
import streamlit as st
from datetime import datetime


# --------------------------------------------
# Severity → Color mapping (reuse GN palette)
# --------------------------------------------
SEVERITY_COLORS = {
    "LOW": "#00916E",        # green
    "MEDIUM": "#ffb300",     # amber
    "HIGH": "#C62828",       # red
    "CRITICAL": "#8b008b",   # purple
    "UNKNOWN": "#64748b",    # slate/neutral
}


def _severity_badge(severity: str | None) -> str:
    """Inline severity pill."""
    sev = (severity or "UNKNOWN").upper()
    color = SEVERITY_COLORS.get(sev, SEVERITY_COLORS["UNKNOWN"])

    return (
        f'<span style="display:inline-flex;align-items:center;gap:0.35rem;'
        f'background:{color}20;padding:6px 12px;border-radius:999px;'
        f'border:1px solid {color}60;color:{color};font-weight:600;'
        f'font-size:0.78rem;letter-spacing:0.04em;text-transform:uppercase;">'
        f'<span style="width:0.45rem;height:0.45rem;border-radius:999px;'
        f'background:{color};"></span>{sev}</span>'
    )


def _layer_badge(layer: str, color: str, emoji: str) -> str:
    """Badge for GNCE constitutional layers."""
    return (
        f'<span style="display:inline-flex;align-items:center;gap:0.35rem;'
        f'background:{color}15;padding:6px 12px;border-radius:999px;'
        f'border:1px solid {color}40;color:{color};font-weight:600;'
        f'font-size:0.78rem;letter-spacing:0.02em;">'
        f'{emoji}&nbsp;{layer}</span>'
    )


def _constitutional_pillar(label: str, value: str, emoji: str, layer: str = "") -> str:
    """Render a constitutional governance pillar."""
    value = value or "Unspecified"
    layer_badge = ""
    if layer:
        layer_badge = f'<span style="display:inline-block;margin-left:0.5rem;padding:2px 8px;background:rgba(79,70,229,0.15);border-radius:4px;font-size:0.7rem;opacity:0.8;color:#6366f1;">{layer}</span>'
    
    return f"""
    <div style="
        display:flex;
        align-items:flex-start;
        gap:0.55rem;
        margin-bottom:0.5rem;
        font-size:0.86rem;
        padding:0.75rem;
        background:rgba(15,23,42,0.3);
        border-radius:8px;
        border:1px solid rgba(148,163,184,0.2);
    ">
      <div style="font-size:1.2rem;margin-top:0.05rem;">{emoji}</div>
      <div style="flex:1;">
        <div style="font-weight:600;opacity:0.95;margin-bottom:0.1rem;color:#e2e8f0;">
          {label}{layer_badge}
        </div>
        <div style="opacity:0.9;font-size:0.9rem;font-weight:500;color:#cbd5e1;">{value}</div>
      </div>
    </div>
    """


def _extract_governance_context(adra: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract governance context with GNCE constitutional focus.
    """
    if not isinstance(adra, dict):
        return {}

    # Try multiple locations
    ctx = adra.get("governance_context") or {}
    if not ctx:
        ctx = adra.get("constitutional_oversight") or {}
    
    # Extract from L1 if present
    l1 = adra.get("L1_the_verdict_and_constitutional_outcome", {}) or {}
    if not ctx:
        ctx = l1.get("governance_context") or l1.get("constitutional_oversight") or {}

    if ctx and isinstance(ctx, dict):
        return ctx

    # ---------- GNCE CONSTITUTIONAL DEFAULTS ----------
    adra_id = adra.get("adra_id", "unknown")
    decision = str(l1.get("decision_outcome", "UNKNOWN")).upper()
    severity = str(l1.get("severity", "UNKNOWN")).upper()
    
    # GNCE-focused defaults (not GRC)
    return {
        "sovereign_engine": {
            "identity": "GNCE Constitutional Engine v0.4",
            "constitutional_layer": "L0-L7 Integrated",
            "governance_path": "Constitutional → Sovereign"
        },
        "policy_surface": {
            "layer": "L4 Policy Lineage",
            "deployment_context": "Policy Configuration Surface",
            "constitutional_binding": "Article-bound constraints"
        },
        "human_oversight": {
            "assigned": False,
            "constitutional_trigger": decision == "DENY" or severity in ["HIGH", "CRITICAL"],
            "oversight_path": "Sovereign Loop → Governance Dashboard"
        },
        "constitutional_tags": {
            "governance_tier": "CONSTITUTIONAL_ENGINE",
            "oversight_model": "AUTONOMOUS_WITH_SOVEREIGN_ESCALATION",
            "verdict_type": decision,
            "severity_class": severity,
            "notes": (
                f"GNCE constitutional verdict {adra_id}. "
                f"This is a machine-speed constitutional assessment, not a GRC assignment. "
                f"Human oversight may be invoked via sovereign governance paths."
            )
        },
        "sovereign_pathways": {
            "veto_feedback": "L7 → Agent",
            "drift_monitoring": "L6 → DDA Loop",
            "governance_updates": "Sovereign Dashboard → Policy Commit"
        }
    }


def _render_constitutional_metadata(ctx: Dict[str, Any], key_prefix: str) -> None:
    """
    Render constitutional metadata tab content.
    """
    constitutional_tags = ctx.get("constitutional_tags", {})
    
    st.markdown("##### 🏷️ Constitutional Metadata")
    
    if not constitutional_tags:
        st.info("No constitutional tags defined.")
        return
    
    # Engine configuration
    if any(k in constitutional_tags for k in ["governance_tier", "oversight_model", "constitutional_layer"]):
        st.markdown("###### ⚙️ Engine Configuration")
        cols = st.columns(3)
        config_items = [
            ("governance_tier", "Governance Tier"),
            ("oversight_model", "Oversight Model"),
            ("verdict_type", "Verdict Type"),
            ("severity_class", "Severity Class"),
            ("human_custodian_assigned", "Custodian Assigned"),
        ]
        
        for i, (key, label) in enumerate(config_items):
            if key in constitutional_tags:
                with cols[i % 3]:
                    value = constitutional_tags[key]
                    if isinstance(value, bool):
                        display_value = "✅ Yes" if value else "❌ No"
                    else:
                        display_value = str(value)
                    st.metric(label=label, value=display_value, delta=None)
    
    # Human role configuration
    if any(k in constitutional_tags for k in ["human_custodian_assigned", "custodian_role", "gnce_role_type"]):
        st.markdown("###### 👤 Human Constitutional Role")
        if "custodian_role" in constitutional_tags:
            st.markdown(f"**Assigned Role:** {constitutional_tags['custodian_role']}")
        if "gnce_role_type" in constitutional_tags:
            st.markdown(f"**GNCE Role Type:** `{constitutional_tags['gnce_role_type']}`")
        if "human_custodian_assigned" in constitutional_tags:
            status = "✅ Assigned" if constitutional_tags["human_custodian_assigned"] else "⏳ Unassigned"
            st.markdown(f"**Assignment Status:** {status}")
    
    # Notes
    if "notes" in constitutional_tags:
        st.markdown("###### 📝 Constitutional Notes")
        st.info(constitutional_tags["notes"])


def _render_governance_pathways(ctx: Dict[str, Any], key_prefix: str) -> None:
    """
    Render governance pathways tab content.
    """
    sovereign_pathways = ctx.get("sovereign_pathways", {})
    
    st.markdown("##### 🛣️ Constitutional Governance Pathways")
    
    if not sovereign_pathways:
        st.info("No constitutional pathways defined.")
        return
    
    # Veto Feedback Path
    if "veto_feedback" in sovereign_pathways:
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem;padding:0.75rem;background:rgba(239,68,68,0.1);border-radius:8px;border:1px solid rgba(239,68,68,0.3);">
                <div style="font-size:1.5rem;">⛔</div>
                <div style="flex:1;">
                    <div style="font-weight:600;color:#fca5a5;">Veto Feedback Path</div>
                    <div style="font-size:0.85rem;opacity:0.8;color:#fca5a5;">{sovereign_pathways['veto_feedback']}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Drift Monitoring Path
    if "drift_monitoring" in sovereign_pathways:
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem;padding:0.75rem;background:rgba(59,130,246,0.1);border-radius:8px;border:1px solid rgba(59,130,246,0.3);">
                <div style="font-size:1.5rem;">📈</div>
                <div style="flex:1;">
                    <div style="font-weight:600;color:#93c5fd;">Drift Detection Path</div>
                    <div style="font-size:0.85rem;opacity:0.8;color:#93c5fd;">{sovereign_pathways['drift_monitoring']}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Sovereign Governance Path
    if "governance_updates" in sovereign_pathways:
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem;padding:0.75rem;background:rgba(139,92,246,0.1);border-radius:8px;border:1px solid rgba(139,92,246,0.3);">
                <div style="font-size:1.5rem;">🏛️</div>
                <div style="flex:1;">
                    <div style="font-weight:600;color:#a78bfa;">Sovereign Governance Path</div>
                    <div style="font-size:0.85rem;opacity:0.8;color:#a78bfa;">{sovereign_pathways['governance_updates']}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown("###### 🧭 Constitutional Navigation")
    st.markdown("""
    **Primary Pathways:**
    1. **Machine-Speed Constitutional Loop (L0-L7)** - Autonomous assessment
    2. **Veto Feedback Path (L7 → Agent)** - Corrective signals
    3. **Drift Detection Loop (L6 → DDA)** - Behavioral monitoring
    4. **Sovereign Governance Path** - Human/regulatory oversight
    """)


def _render_configuration_interface(ctx: Dict[str, Any], key_prefix: str) -> Dict[str, Any]:
    """
    Render configuration interface tab content.
    """
    # Get current human oversight
    human_oversight = ctx.get("human_oversight", {})
    if isinstance(human_oversight, dict):
        current_assigned = human_oversight.get("assigned", False)
        current_custodian = human_oversight.get("custodian", "Unassigned (Constitutional Review Pool)")
        current_contact = human_oversight.get("contact", "team-escalation@domain.com")
        current_responsibility = human_oversight.get("responsibility", "RESPONSIBLE")
        current_path = human_oversight.get("oversight_path", "Autonomous Constitutional Engine")
    else:
        current_assigned = False
        current_custodian = "Unassigned (Constitutional Review Pool)"
        current_contact = "team-escalation@domain.com"
        current_responsibility = "RESPONSIBLE"
        current_path = "Autonomous Constitutional Engine"
    
    st.markdown("##### ⚙️ Constitutional Oversight Configuration")
    
    if st.button("🛠️ Configure Oversight & Human Engagement", key=f"{key_prefix}_config_all", use_container_width=True):
        st.session_state[f"{key_prefix}_show_config"] = True
    
    # Configuration interface
    if st.session_state.get(f"{key_prefix}_show_config", False):
        with st.expander("⚙️ Detailed Constitutional Configuration", expanded=True):
            # GNCE Constitutional Roles
            gnce_constitutional_roles = [
                {
                    "id": "unassigned",
                    "name": "Unassigned (Constitutional Review Pool)",
                    "emoji": "⏳",
                    "description": "No specific constitutional role assigned",
                    "activation": "On-demand via sovereign governance"
                },
                {
                    "id": "cah",
                    "name": "🧭 Constitutional Authority Holder (CAH)",
                    "emoji": "🧭",
                    "description": "Human root of constitutional legitimacy - authorizes/amends constitutional constraints",
                    "activation": "Constitutional definition & amendment"
                },
                {
                    "id": "eoo", 
                    "name": "🛑 Execution Oversight Officer (EOO)",
                    "emoji": "🛑",
                    "description": "Constitutional circuit breaker - summoned when autonomy is constitutionally insufficient",
                    "activation": "Veto triggers, threshold exceedances, legal human judgment required"
                },
                {
                    "id": "lbo",
                    "name": "⚖️ Liability Boundary Officer (LBO)", 
                    "emoji": "⚖️",
                    "description": "Owns legal attribution when autonomy crosses into regulated harm space",
                    "activation": "Audits, litigation, regulatory inquiry"
                },
                {
                    "id": "crs",
                    "name": "📜 Constitutional Regime Steward (CRS)",
                    "emoji": "📜", 
                    "description": "Custodian of regulatory regimes - encodes law into executable constitutional form",
                    "activation": "Regime mapping updates, law evolution"
                },
                {
                    "id": "abd",
                    "name": "🧠 Autonomy Boundary Designer (ABD)",
                    "emoji": "🧠",
                    "description": "Architect of autonomy limits - defines where autonomy stops",
                    "activation": "Autonomy tier definition, escalation threshold setting"
                },
                {
                    "id": "ecal",
                    "name": "📂 Evidence Custodian / Audit Liaison (ECAL)",
                    "emoji": "📂",
                    "description": "Human interface between GNCE and regulators - presents GNCE artifacts as evidence",
                    "activation": "Audits, regulatory evidence presentation"
                },
                {
                    "id": "hos",
                    "name": "✍️ Human Override Signatory (HOS)",
                    "emoji": "✍️",
                    "description": "Assumes responsibility for breaking autonomy - explicit liability transfer",
                    "activation": "GNCE blocks execution but business insists on proceeding"
                },
                {
                    "id": "ilc",
                    "name": "🧩 Institutional Learning Curator (ILC)",
                    "emoji": "🧩",
                    "description": "Curates institutional lessons - feeds learning back into the constitution",
                    "activation": "Veto pattern analysis, constitutional refinement"
                }
            ]
            
            # Find current role in list
            current_role_name = current_custodian
            current_role_index = 0
            for i, role in enumerate(gnce_constitutional_roles):
                if role["name"] == current_role_name:
                    current_role_index = i
                    break
            
            selected_role = st.selectbox(
                "Select Constitutional Role:",
                options=[role["name"] for role in gnce_constitutional_roles],
                index=current_role_index,
                key=f"{key_prefix}_custodian_select",
                help="Choose the GNCE constitutional role appropriate for this ADRA's oversight needs"
            )
            
            # Show role description
            selected_role_data = next(role for role in gnce_constitutional_roles if role["name"] == selected_role)
            st.markdown(f"**Role Description:** {selected_role_data['description']}")
            st.markdown(f"**Activation Trigger:** {selected_role_data['activation']}")
            
            # Responsibility level
            responsibility_options = ["RESPONSIBLE", "ACCOUNTABLE", "CONSULTED", "INFORMED"]
            selected_responsibility = st.selectbox(
                "Responsibility Level:",
                options=responsibility_options,
                index=responsibility_options.index(current_responsibility) if current_responsibility in responsibility_options else 0,
                key=f"{key_prefix}_responsibility"
            )
            
            # Contact information
            selected_contact = st.text_input(
                "Contact Email:",
                value=current_contact,
                key=f"{key_prefix}_contact"
            )
            
            # Assignment notes
            assignment_notes = st.text_area(
                "Constitutional Assignment Notes:",
                value=f"Assigned {selected_role} for {selected_responsibility.lower()} constitutional oversight via GNCE UI.",
                key=f"{key_prefix}_notes"
            )
            
            # -------------------------------
            # SECTION 2: CONSTITUTIONAL PATHWAYS
            # -------------------------------
            st.markdown("###### 🛣️ Constitutional Oversight Pathways")
            
            # Constitutional oversight options
            oversight_paths = [
                {"id": "autonomous", "name": "⚡ Autonomous Constitutional Engine", "path": "L0-L7 Machine Speed", "emoji": "⚡"},
                {"id": "sovereign_monitor", "name": "🏛️ Sovereign Governance Monitor", "path": "Block O Dashboard", "emoji": "🏛️"},
                {"id": "policy_feedback", "name": "🔄 Policy Feedback Loop", "path": "L7 → Block P", "emoji": "🔄"},
                {"id": "drift_oversight", "name": "📈 Drift Detection Oversight", "path": "L6 DDA Monitoring", "emoji": "📈"}
            ]
            
            selected_path = st.selectbox(
                "Primary Constitutional Oversight Pathway:",
                options=[p["name"] for p in oversight_paths],
                index=0,
                key=f"{key_prefix}_path_select"
            )
            
            # Constitutional triggers
            st.markdown("###### ⚡ Constitutional Triggers for Sovereign Engagement")
            col1, col2 = st.columns(2)
            with col1:
                trigger_deny = st.checkbox("Trigger on DENY verdicts", value=True, key=f"{key_prefix}_trigger_deny")
                trigger_high = st.checkbox("Trigger on HIGH/CRITICAL severity", value=True, key=f"{key_prefix}_trigger_high")
            with col2:
                trigger_veto = st.checkbox("Trigger on L7 veto", value=True, key=f"{key_prefix}_trigger_veto")
                trigger_drift = st.checkbox("Trigger on L6 drift alerts", value=False, key=f"{key_prefix}_trigger_drift")
            
            # -------------------------------
            # SECTION 3: SAVE CONFIGURATION
            # -------------------------------
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("✅ Save Constitutional Configuration", key=f"{key_prefix}_save_all", use_container_width=True):
                    # Update human oversight with custodian assignment
                    ctx["human_oversight"] = {
                        "assigned": True if selected_role != "Unassigned (Constitutional Review Pool)" else False,
                        "custodian": selected_role,
                        "contact": selected_contact,
                        "responsibility": selected_responsibility,
                        "assigned_at": datetime.now().isoformat(),
                        "assignment_notes": assignment_notes,
                        "constitutional_trigger": {
                            "on_deny": trigger_deny,
                            "on_high_severity": trigger_high,
                            "on_veto": trigger_veto,
                            "on_drift": trigger_drift
                        },
                        "oversight_path": selected_path,
                        "configuration_note": "Constitutional oversight with human engagement configured via GNCE UI",
                        "gnce_role_type": selected_role_data["id"],
                        "gnce_role_description": selected_role_data["description"]
                    }
                    
                    # Update constitutional tags
                    if "constitutional_tags" not in ctx:
                        ctx["constitutional_tags"] = {}
                    ctx["constitutional_tags"]["human_custodian_assigned"] = selected_role != "Unassigned (Constitutional Review Pool)"
                    ctx["constitutional_tags"]["custodian_role"] = selected_role
                    ctx["constitutional_tags"]["gnce_role_type"] = selected_role_data["id"]
                    ctx["constitutional_tags"]["assignment_timestamp"] = datetime.now().isoformat()
                    ctx["constitutional_tags"]["oversight_model"] = "CONSTITUTIONAL_WITH_HUMAN_ACTORS"
                    
                    st.success(f"Constitutional role configured: {selected_role}")
                    st.session_state[f"{key_prefix}_show_config"] = False
                    st.rerun()
            
            with col_cancel:
                if st.button("❌ Cancel", key=f"{key_prefix}_cancel_all", use_container_width=True):
                    st.session_state[f"{key_prefix}_show_config"] = False
                    st.rerun()
    
    # Display current configuration summary
    st.markdown("###### 📋 Current Configuration")
    st.markdown(f"**Active Path:** {current_path}")
    if current_assigned:
        st.markdown(f"**Constitutional Role:** {current_custodian}")
        st.markdown(f"**Responsibility:** {current_responsibility}")
        st.markdown(f"**Contact:** {current_contact}")
    else:
        st.markdown("**Constitutional Role:** ⏳ Unassigned (Constitutional Review Pool)")
    
    return ctx


def render_governance_stewardship(
    adra: Dict[str, Any],
    key_prefix: str = "govctx",
) -> None:
    """
    🏛️ GNCE Constitutional Governance Context
    
    Focuses on GNCE's constitutional architecture, NOT GRC:
    - Constitutional layers and pathways
    - Sovereign governance engagement points
    - Machine-speed vs human-speed oversight
    - Policy lineage and surface context
    """
    
    if not isinstance(adra, dict):
        return
    
    # Initialize session state
    if f"{key_prefix}_show_config" not in st.session_state:
        st.session_state[f"{key_prefix}_show_config"] = False
    
    # Extract constitutional context
    ctx = _extract_governance_context(adra)
    
    # Extract decision info
    l1 = adra.get("L1_the_verdict_and_constitutional_outcome", {}) or {}
    decision = str(l1.get("decision_outcome", l1.get("decision", "N/A"))).upper()
    severity = str(l1.get("severity", "UNKNOWN")).upper()
    
    # Parse GNCE constitutional elements
    sovereign_engine = ctx.get("sovereign_engine", {})
    if isinstance(sovereign_engine, dict):
        engine_identity = sovereign_engine.get("identity", "GNCE Constitutional Engine")
        engine_layer = sovereign_engine.get("constitutional_layer", "L0-L7")
    else:
        engine_identity = str(sovereign_engine)
        engine_layer = ""
    
    policy_surface = ctx.get("policy_surface", {})
    if isinstance(policy_surface, dict):
        policy_layer = policy_surface.get("layer", "L4 Policy Surface")
        policy_context = policy_surface.get("deployment_context", "Deployment Configuration")
    else:
        policy_layer = str(policy_surface)
        policy_context = ""
    
    human_oversight = ctx.get("human_oversight", {})
    if isinstance(human_oversight, dict):
        oversight_path = human_oversight.get("oversight_path", "Autonomous Constitutional Engine")
        oversight_trigger = human_oversight.get("constitutional_trigger", "On-demand via Sovereign Dashboard")
        human_custodian = human_oversight.get("custodian", "Unassigned (Constitutional Review Pool)")
        human_contact = human_oversight.get("contact", "team-escalation@domain.com")
        human_assigned = human_oversight.get("assigned", False)
        human_responsibility = human_oversight.get("responsibility", "RESPONSIBLE")
        gnce_role_type = human_oversight.get("gnce_role_type", "unassigned")
    else:
        oversight_path = str(human_oversight)
        oversight_trigger = ""
        human_custodian = "Unassigned (Constitutional Review Pool)"
        human_contact = "team-escalation@domain.com"
        human_assigned = False
        human_responsibility = "RESPONSIBLE"
        gnce_role_type = "unassigned"
    
    constitutional_tags = ctx.get("constitutional_tags", {})
    sovereign_pathways = ctx.get("sovereign_pathways", {})
    
    sev_badge = _severity_badge(severity)
    
    # -------------------------------
    # PANEL HEADER - CONSTITUTIONAL FOCUS
    # -------------------------------
    st.subheader("🏛️ Constitutional Governance Context")
    
    st.markdown(
        f"""
<div style="
    padding:18px 20px;
    border-radius:14px;
    margin-top:4px;
    background:radial-gradient(circle at top left,
                rgba(79,70,229,0.12),rgba(15,23,42,0.98));
    border:1px solid rgba(129,140,248,0.4);
    box-shadow:0 12px 28px rgba(15,23,42,0.9);
    font-size:0.88rem;
">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;">
    <div style="max-width:70%;">
      <div style="font-size:0.98rem;font-weight:600;margin-bottom:0.25rem;color:#e2e8f0;">
        GNCE Constitutional Governance Surface
      </div>
      <p style="margin:0;opacity:0.85;line-height:1.5;color:#cbd5e1;">
        This documents the <em>constitutional architecture</em> surrounding each ADRA,
        not GRC assignments. GNCE operates at machine speed (L0-L7) with sovereign
        governance engagement points for human oversight.
      </p>
    </div>
    <div style="text-align:right;display:flex;flex-direction:column;gap:0.4rem;align-items:flex-end;">
      <div style="font-size:0.8rem;opacity:0.9;color:#94a3b8;">
        Constitutional Verdict:&nbsp;<strong style="color:#e2e8f0;">{decision}</strong>
      </div>
      {sev_badge}
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
    
    # -------------------------------
    # SOVEREIGN ENGAGEMENT PROTOCOL (MOVED UP)
    # -------------------------------
    st.markdown("### 🏛️ Sovereign Engagement Protocol")
    
    # Determine engagement protocol
    is_sovereign_required = (
        decision == "DENY" or 
        severity in ["HIGH", "CRITICAL"] or
        "veto" in str(constitutional_tags.get("verdict_type", "")).lower()
    )
    
    if is_sovereign_required:
        st.warning("""
        **Sovereign Governance Engagement Recommended**
        
        This ADRA has triggered constitutional conditions that warrant review via:
        - **Block O: Sovereign Governance Dashboard** - For governance model review
        - **L7 Veto Artifact Analysis** - For corrective signal examination
        - **Policy Update Consideration** - For L4 policy surface adjustments
        
        *Note: This is constitutional governance review, not GRC compliance review.*
        """)
        
        # Show human constitutional role if assigned
        if human_assigned:
            # Map GNCE role types to engagement recommendations
            role_engagement = {
                "cah": "Constitutional authority ratification may be required.",
                "eoo": "Execution oversight officer should review veto artifacts.",
                "lbo": "Liability boundary assessment recommended.",
                "crs": "Regime steward review of policy alignment needed.",
                "abd": "Autonomy boundary review for threshold adjustments.",
                "ecal": "Evidence preparation for audit/regulatory review.",
                "hos": "Human override sign-off may be required.",
                "ilc": "Institutional learning curation opportunity."
            }
            
            engagement_note = role_engagement.get(gnce_role_type, "Constitutional role engagement recommended.")
            
            st.info(f"""
            **Assigned Constitutional Role:** {human_custodian}
            
            **Role-Specific Engagement:**
            {engagement_note}
            
            **Responsibility:** {human_responsibility}
            **Contact:** {human_contact}
            
            This constitutional actor should be engaged via sovereign governance pathways.
            """)
    else:
        st.success("""
        **Standard Constitutional Operation**
        
        This ADRA operates within normal constitutional parameters:
        - Machine-speed assessment complete (L0-L7)
        - No sovereign governance engagement required
        - Normal drift monitoring active (L6 DDA)
        
        Human constitutional actors remain available on-demand via Sovereign Dashboard.
        """)
    
    # -------------------------------
    # INTERACTIVE CONSTITUTIONAL PILLARS
    # -------------------------------
    st.markdown("### ⚖️ Constitutional Stewardship")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Sovereign Engine Pillar
        st.markdown(
            _constitutional_pillar(
                label="Constitutional Engine",
                value=engine_identity,
                emoji="⚙️",
                layer=engine_layer
            ),
            unsafe_allow_html=True
        )
        
        # Policy Surface Pillar
        st.markdown(
            _constitutional_pillar(
                label="Policy Configuration Surface",
                value=policy_context,
                emoji="📜",
                layer=policy_layer
            ),
            unsafe_allow_html=True
        )
    
    with col2:
        # Human Oversight Pathway Pillar
        st.markdown(
            _constitutional_pillar(
                label="Human Oversight Pathway",
                value=oversight_path,
                emoji="🧑‍⚖️",
                layer="Sovereign Loop"
            ),
            unsafe_allow_html=True
        )
        
        # Constitutional Role Pillar (if assigned)
        if human_assigned:
            st.markdown(
                _constitutional_pillar(
                    label="Constitutional Human Role",
                    value=human_custodian,
                    emoji="⚡",
                    layer=gnce_role_type.upper()
                ),
                unsafe_allow_html=True
            )
    
    # -------------------------------
    # HUMAN OVERSIGHT PATHWAY DETAILS
    # -------------------------------
    with st.expander("🧑‍⚖️ Human Oversight Pathway Details", expanded=True):
        st.markdown("#### 🧑‍⚖️ Constitutional Oversight Paths")
        st.markdown(f"**Active Path:** `{oversight_path}`")
        
        # Create tabs for detailed analysis inside the Human Oversight Pathway
        tab1, tab2, tab3 = st.tabs(["🏷️ Constitutional Metadata", "🛣️ Governance Pathways", "⚙️ Configuration"])
        
        with tab1:
            _render_constitutional_metadata(ctx, key_prefix)
        
        with tab2:
            _render_governance_pathways(ctx, key_prefix)
        
        with tab3:
            ctx = _render_configuration_interface(ctx, key_prefix)
    
    # -------------------------------
    # DISPLAY HUMAN ROLE INFORMATION
    # -------------------------------
    if human_assigned:
        st.markdown("### 👤 Constitutional Human Role")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Role", human_custodian)
        with col_b:
            st.metric("Responsibility", human_responsibility)
        with col_c:
            st.metric("Contact", human_contact if human_contact else "Not provided")
    
    # -------------------------------
    # EXPORT GOVERNANCE CONTEXT
    # -------------------------------
    st.markdown("---")
    with st.expander("📤 Export Constitutional Context", expanded=False):
        col1, col2 = st.columns([3, 1])
        with col1:
            include_adra = st.checkbox("Include full ADRA context", value=False, key=f"{key_prefix}_include_adra")
            export_format = st.selectbox("Format:", ["JSON", "Constitutional Summary"], key=f"{key_prefix}_export_format")
        
        if st.button("Generate Constitutional Export", key=f"{key_prefix}_generate_export", use_container_width=True):
            export_data = {
                "constitutional_context": ctx,
                "adra_metadata": {
                    "id": adra.get("adra_id"),
                    "verdict": decision,
                    "severity": severity,
                    "timestamp": datetime.now().isoformat(),
                    "constitutional_note": "GNCE constitutional governance context export"
                },
                "human_constitutional_engagement": {
                    "role": human_custodian,
                    "assigned": human_assigned,
                    "gnce_role_type": gnce_role_type,
                    "contact": human_contact if human_assigned else "Unassigned",
                    "responsibility": human_responsibility if human_assigned else "CONSTITUTIONAL_REVIEW_POOL",
                    "engagement_required": is_sovereign_required
                }
            }
            
            if include_adra:
                export_data["full_adra"] = adra
            
            if export_format == "Constitutional Summary":
                summary = f"""
                GNCE Constitutional Governance Summary
                ======================================
                
                ADRA: {adra.get('adra_id', 'Unknown')}
                Verdict: {decision}
                Severity: {severity}
                
                Constitutional Engine: {engine_identity}
                Policy Surface: {policy_layer}
                Oversight Pathway: {oversight_path}
                
                Human Constitutional Role: {human_custodian}
                GNCE Role Type: {gnce_role_type.upper() if gnce_role_type != 'unassigned' else 'UNASSIGNED'}
                Responsibility: {human_responsibility if human_assigned else 'CONSTITUTIONAL_REVIEW_POOL'}
                Contact: {human_contact if human_assigned else 'Unassigned'}
                
                Sovereign Engagement: {'Recommended' if is_sovereign_required else 'Not Required'}
                
                Generated: {datetime.now().isoformat()}
                """
                st.download_button(
                    label="📥 Download Constitutional Summary",
                    file_name=f"gnce_constitutional_{adra.get('adra_id', 'summary')}.txt",
                    mime="text/plain",
                    data=summary,
                    use_container_width=True,
                    key=f"{key_prefix}_download_summary"
                )
            else:
                st.download_button(
                    label="📥 Download JSON Context",
                    file_name=f"gnce_constitutional_{adra.get('adra_id', 'context')}.json",
                    mime="application/json",
                    data=json.dumps(export_data, indent=2),
                    use_container_width=True,
                    key=f"{key_prefix}_download_json"
                )


# -------------------------------------------------------------------
# Backwards-compat alias
# -------------------------------------------------------------------
render_governance_context = render_governance_stewardship