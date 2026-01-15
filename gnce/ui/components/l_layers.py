# gnce/ui/components/l_layers.py
from __future__ import annotations
from typing import Any, Dict, List, Tuple
import json
import streamlit as st

LAYER_SPECS: List[Tuple[str, str, str]] = [
    ("L0_pre_execution_validation", "L0", "Pre-Execution Constitutional Validation"),
    ("L1_the_verdict_and_constitutional_outcome", "L1", "the Verdict & Constitutional Outcome"),
    ("L2_input_snapshot_and_dra", "L2", "Deterministic Decision Lineage (DDL)"),
    ("L3_rule_level_trace", "L3", "Deterministic Rule Engine (DRE)"),
    ("L4_policy_lineage_and_constitution", "L4", "Policy Lineage & Constitutional Authority Layer"),
    ("L5_integrity_and_tokenization", "L5", "Integrity & Cryptographic Execution Token (CET)"),
    ("L6_behavioral_drift_and_monitoring", "L6", "Behavioral Drift & Constitutional Monitoring"),
    ("L7_veto_and_execution_feedback", "L7", "Veto Path & Sovereign Execution Feedback"),
]

# Layer color scheme matching GNCE theme
LAYER_COLORS = {
    "L0": "#10b981",  # Green
    "L1": "#3b82f6",  # Blue
    "L2": "#ef4444",  # Red
    "L3": "#8b5cf6",  # Purple
    "L4": "#64748b",  # Gray
    "L5": "#06b6d4",  # Cyan
    "L6": "#f59e0b",  # Amber
    "L7": "#dc2626",  # Red
}

# Layer descriptions
LAYER_DESCRIPTIONS = {
    "L0": "Constitutional bedrock & sovereignty",
    "L1": "Final decision outcome binding",
    "L2": "Ethical alignment & moral calculus",
    "L3": "Rule engine & policy constraints",
    "L4": "Policy lineage & legal grounding",
    "L5": "Cryptography & Tokenization",
    "L6": "Behavioral drift detection",
    "L7": "Constitutional veto & feedback",
}

def render_constitutional_layer_visualization() -> None:
    """
    Renders the 8 constitutional layers as a visual grid.
    This shows the architecture, not the data.
    """
    st.markdown("### 🏛️ Constitutional Layer Architecture")
    
    # Create two columns for the grid
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Core Governance Layers")
        
        # L0 - Foundational
        st.markdown(f"""
        <div style="
            background: rgba(15, 23, 42, 0.7); 
            padding: 12px; 
            border-radius: 8px; 
            border-left: 4px solid {LAYER_COLORS['L0']};
            margin-bottom: 8px;
            border: 1px solid rgba(148, 163, 184, 0.1);
        ">
            <div style="font-weight: bold; color: {LAYER_COLORS['L0']}; font-size: 16px;">
                L0 • Foundational
            </div>
            <div style="font-size: 12px; color: #94a3b8;">
                {LAYER_DESCRIPTIONS['L0']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # L1 - Verdict
        st.markdown(f"""
        <div style="
            background: rgba(15, 23, 42, 0.7); 
            padding: 12px; 
            border-radius: 8px; 
            border-left: 4px solid {LAYER_COLORS['L1']};
            margin-bottom: 8px;
            border: 1px solid rgba(148, 163, 184, 0.1);
        ">
            <div style="font-weight: bold; color: {LAYER_COLORS['L1']}; font-size: 16px;">
                L1 • Verdict
            </div>
            <div style="font-size: 12px; color: #94a3b8;">
                {LAYER_DESCRIPTIONS['L1']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # L2 - Ethical
        st.markdown(f"""
        <div style="
            background: rgba(15, 23, 42, 0.7); 
            padding: 12px; 
            border-radius: 8px; 
            border-left: 4px solid {LAYER_COLORS['L2']};
            margin-bottom: 8px;
            border: 1px solid rgba(148, 163, 184, 0.1);
        ">
            <div style="font-weight: bold; color: {LAYER_COLORS['L2']}; font-size: 16px;">
                L2 • Ethical
            </div>
            <div style="font-size: 12px; color: #94a3b8;">
                {LAYER_DESCRIPTIONS['L2']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # L3 - Constraints
        st.markdown(f"""
        <div style="
            background: rgba(15, 23, 42, 0.7); 
            padding: 12px; 
            border-radius: 8px; 
            border-left: 4px solid {LAYER_COLORS['L3']};
            margin-bottom: 8px;
            border: 1px solid rgba(148, 163, 184, 0.1);
        ">
            <div style="font-weight: bold; color: {LAYER_COLORS['L3']}; font-size: 16px;">
                L3 • Constraints
            </div>
            <div style="font-size: 12px; color: #94a3b8;">
                {LAYER_DESCRIPTIONS['L3']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### Enforcement & Audit Layers")
        
        # L4 - Policy
        st.markdown(f"""
        <div style="
            background: rgba(15, 23, 42, 0.7); 
            padding: 12px; 
            border-radius: 8px; 
            border-left: 4px solid {LAYER_COLORS['L4']};
            margin-bottom: 8px;
            border: 1px solid rgba(148, 163, 184, 0.1);
        ">
            <div style="font-weight: bold; color: {LAYER_COLORS['L4']}; font-size: 16px;">
                L4 • Policy
            </div>
            <div style="font-size: 12px; color: #94a3b8;">
                {LAYER_DESCRIPTIONS['L4']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # L5 - C&T
        st.markdown(f"""
        <div style="
            background: rgba(15, 23, 42, 0.7); 
            padding: 12px; 
            border-radius: 8px; 
            border-left: 4px solid {LAYER_COLORS['L5']};
            margin-bottom: 8px;
            border: 1px solid rgba(148, 163, 184, 0.1);
        ">
            <div style="font-weight: bold; color: {LAYER_COLORS['L5']}; font-size: 16px;">
                L5 • C&T
            </div>
            <div style="font-size: 12px; color: #94a3b8;">
                {LAYER_DESCRIPTIONS['L5']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # L6 - Drift
        st.markdown(f"""
        <div style="
            background: rgba(15, 23, 42, 0.7); 
            padding: 12px; 
            border-radius: 8px; 
            border-left: 4px solid {LAYER_COLORS['L6']};
            margin-bottom: 8px;
            border: 1px solid rgba(148, 163, 184, 0.1);
        ">
            <div style="font-weight: bold; color: {LAYER_COLORS['L6']}; font-size: 16px;">
                L6 • Drift
            </div>
            <div style="font-size: 12px; color: #94a3b8;">
                {LAYER_DESCRIPTIONS['L6']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # L7 - Veto
        st.markdown(f"""
        <div style="
            background: rgba(15, 23, 42, 0.7); 
            padding: 12px; 
            border-radius: 8px; 
            border-left: 4px solid {LAYER_COLORS['L7']};
            margin-bottom: 8px;
            border: 1px solid rgba(148, 163, 184, 0.1);
        ">
            <div style="font-weight: bold; color: {LAYER_COLORS['L7']}; font-size: 16px;">
                L7 • Veto
            </div>
            <div style="font-size: 12px; color: #94a3b8;">
                {LAYER_DESCRIPTIONS['L7']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.info("🏛️ Constitutional Governance Flow: All 8 layers work in concert to ensure deterministic, auditable, and sovereign decision-making")

def _safe_get(d: Any, *path: str) -> Any:
    cur = d
    for p in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
    return cur

def _render_layer_card(layer_code: str, title: str, obj: Dict[str, Any]) -> None:
    constitutional = obj.get("constitutional") if isinstance(obj, dict) else None
    clause = _safe_get(constitutional, "clause") or "—"
    severity = obj.get("severity")
    validated = obj.get("validated")
    gate = obj.get("decision_gate")

    st.markdown(f"**{layer_code} — {title}**")

    cols = st.columns(3)
    with cols[0]:
        if severity is not None:
            st.caption(f"Severity: **{severity}**")
    with cols[1]:
        if validated is not None:
            st.caption(f"Validated: **{validated}**")
    with cols[2]:
        if isinstance(gate, dict) and "allow_downstream" in gate:
            st.caption(f"Gate: **{'ALLOW' if gate['allow_downstream'] else 'BLOCK'}**")

    if constitutional:
        st.caption(f"Clause: {clause}")

    with st.expander("🧩 Raw Layer Object", expanded=False):
        st.code(json.dumps(obj, indent=2), language="json")

def render_layers_stack(
    adra: Dict[str, Any],
    regulator_mode: bool = False,
    focus_layer: str = "L1",
    key_prefix: str = "main",
) -> None:
    st.subheader("🧠 GNCE Constitutional Layers")

    # Summary chips
    l1 = adra.get("L1_the_verdict_and_constitutional_outcome", {}) or {}
    l6 = adra.get("L6_behavioral_drift_and_monitoring", {}) or {}
    l7 = adra.get("L7_veto_and_execution_feedback", {}) or {}
    l5 = adra.get("L5_integrity_and_tokenization", {}) or {}

    decision = (l1.get("decision_outcome") or l1.get("decision") or "N/A")
    severity = (l1.get("severity") or "N/A")
    gate = "ALLOW" if (l7.get("decision_gate", {}).get("allow_downstream") is True) else "BLOCK"
    drift = (l6.get("drift_outcome") or "NO_DRIFT")
    veto = (l7.get("veto_category") or "NONE")
    cet = "SIGNED" if (l5.get("decision_gate", {}).get("allow_downstream") is True) else "NOT_SIGNED"

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Verdict", str(decision))
    c2.metric("Severity", str(severity))
    c3.metric("Gate", gate)
    c4.metric("Drift", str(drift))
    c5.metric("Veto", str(veto))
    c6.metric("CET", cet)

    st.markdown("---")

    # IMPORTANT: no radio here (radio lives in gn_app.py)
    for adra_key, layer_code, title in LAYER_SPECS:
        obj = adra.get(adra_key)
        if not isinstance(obj, dict):
            continue

        expanded = (layer_code == (focus_layer or "L1"))
        with st.expander(f"{layer_code} — {title}", expanded=expanded):
            _render_layer_card(layer_code, title, obj)

def render_constitutional_layers(
    adra: Dict[str, Any],
    regulator_mode: bool = False,
    focus_layer: str = "L1",
) -> None:
    """
    Main function that renders both the layer visualization and detailed data.
    Handles both old and new parameter signatures.
    """
    try:
        # First, show the constitutional layer visualization
        render_constitutional_layer_visualization()
        
        st.markdown("---")
        
        # Then show the detailed layer inspection from the ADRA
        if adra:
            # Try to render with the new parameters
            render_layers_stack(adra, regulator_mode=regulator_mode, focus_layer=focus_layer, key_prefix="compat")
        else:
            st.info("Run GNCE to generate an ADRA for detailed layer inspection.")
    except Exception as e:
        # If anything goes wrong, show a simplified view
        st.warning(f"Layer rendering encountered an issue: {e}")
        if adra:
            # Fallback to basic rendering
            render_layers_stack(adra, key_prefix="fallback")