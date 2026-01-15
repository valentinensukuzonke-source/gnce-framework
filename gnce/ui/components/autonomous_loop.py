# ui/components/autonomous_loop.py
from __future__ import annotations

from typing import Dict, Any, Optional, List
import json

import streamlit as st


# -------------------------------------------------------
#  Enhanced Helpers
# -------------------------------------------------------

def _chip(label: str, value: str, color: str = "default"):
    """Styled chip with color coding"""
    colors = {
        "default": "rgba(100, 116, 139, 0.15)",
        "success": "rgba(34, 197, 94, 0.15)",
        "warning": "rgba(245, 158, 11, 0.15)",
        "danger": "rgba(239, 68, 68, 0.15)",
        "info": "rgba(59, 130, 246, 0.15)"
    }
    bg_color = colors.get(color, colors["default"])
    
    st.markdown(
        f"""
        <div style="display:inline-block;
                    padding:0.3rem 0.65rem;
                    margin:0.15rem 0.25rem 0.15rem 0;
                    border-radius:999px;
                    border:1px solid rgba(0,0,0,0.15);
                    background-color:{bg_color};
                    font-size:0.85rem;">
            <b>{label}:</b>&nbsp;{value}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _get_in(d: Any, path: Iterable[str], default=None):
    """Safe nested dictionary access"""
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def _get_original_input_from_session() -> Dict[str, Any]:
    """
    Get the original input that was sent to GNCE from session state.
    This is what was actually edited in the sidebar and fired.
    """
    try:
        # First try to get the actual input that was used for the latest run
        # This should be stored by gn_app.py after running GNCE
        current_input = st.session_state.get("current_input_used", {})
        if current_input:
            return current_input
        
        # Fallback: try to get from input editor session state
        input_text = st.session_state.get("gn_input_json_text", "")
        if input_text:
            try:
                return json.loads(input_text)
            except:
                pass
        
        # Fallback: get from latest ADRA's L2 snapshot
        latest_adra = st.session_state.get("current_adra", {})
        return latest_adra.get("_original_input", {})
    except Exception as e:
        st.error(f"Error getting original input: {e}")
        return {}


def _get_request_payload_for_display(adra: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get the request payload for display, prioritizing the actual input that was fired.
    """
    # First try to get the original input from session state (what was actually sent)
    original_input = _get_original_input_from_session()
    if original_input:
        return original_input
    
    # Fallback: extract from ADRA using multiple strategies
    if not isinstance(adra, dict):
        return {}
    
    # Try multiple locations for the payload in ADRA
    payload_sources = [
        # L2 input snapshot
        adra.get("L2_input_snapshot_and_dra", {}).get("input_snapshot"),
        adra.get("L2_input_snapshot_and_provenance", {}).get("input_snapshot"),
        adra.get("L2_input_and_tasking", {}).get("input_snapshot"),
        # L2 evidence
        adra.get("L2_input_snapshot_and_dra", {}).get("evidence"),
        # Direct in L2
        adra.get("L2", {}).get("input_snapshot"),
        # Top-level fields (direct mapping from input)
        {k: v for k, v in adra.items() if k in [
            "action", "content", "user_id", "timestamp_utc", "risk_indicators",
            "meta", "industry_id", "profile_id", "kyc", "account", "order",
            "request_type", "payload", "data", "input", "listing"
        ] and v is not None}
    ]
    
    for source in payload_sources:
        if isinstance(source, dict) and source:
            return source
    
    return {}


def _render_request_payload(payload: Dict[str, Any], adra: Dict[str, Any] = None):
    """Render request payload showing what was actually fired"""
    
    if not payload or (isinstance(payload, dict) and len(payload) == 0):
        _render_no_payload_message()
        return
    
    # Main payload display
    with st.expander("📋 Request Details", expanded=True):
        # Show the actual JSON that was fired
        st.markdown("##### 🎯 **Input Sent to GNCE**")
        st.caption("This is what was actually fired from the input editor")
        
        # Check if payload is minimal (just metadata)
        is_minimal_payload = len(payload) <= 3 and all(k in ["adra_id", "timestamp_utc", "input_hash"] for k in payload.keys())
        
        if is_minimal_payload:
            # Show metadata only
            st.markdown("##### 📊 Metadata")
            
            # Use container for consistent spacing
            with st.container():
                # Show available metadata in a clean format
                if "adra_id" in payload:
                    st.markdown(f"**ADRA ID:**  \n`{payload['adra_id']}`")
                
                if "timestamp_utc" in payload:
                    st.markdown(f"**Timestamp:**  \n`{payload['timestamp_utc']}`")
                
                if "input_hash" in payload:
                    st.markdown(f"**Input Hash:**  \n`{payload['input_hash'][:20]}...`")
                
                st.info("ℹ️ Request contains minimal metadata. Full payload may be stored in L2 evidence layers.")
        else:
            # Show full payload like in screenshot
            # Display key fields prominently
            if "action" in payload:
                _chip("Action", str(payload["action"]), "info")
            
            if "user_id" in payload:
                _chip("User ID", str(payload["user_id"]), "default")
            
            if "industry_id" in payload:
                _chip("Industry", str(payload["industry_id"]), "info")
            
            if "profile_id" in payload:
                _chip("Profile", str(payload["profile_id"]), "info")
            
            # Content preview (like in screenshot)
            if "content" in payload and payload["content"]:
                content = payload["content"]
                if isinstance(content, str) and len(content) > 0:
                    st.markdown("**Content:**")
                    # Show in a styled box like the screenshot
                    st.markdown(f"""
                    <div style="padding: 8px; background-color: #f8f9fa; border-radius: 4px; border: 1px solid #e9ecef; margin: 4px 0;">
                        {content[:200]}{'...' if len(content) > 200 else ''}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Show risk indicators like in screenshot
            risk_indicators = payload.get("risk_indicators", {})
            if risk_indicators:
                st.markdown("**Risk Indicators:**")
                for key, value in risk_indicators.items():
                    if value is not None:
                        display_key = key.replace("_", " ").title()
                        st.text(f"• {display_key}: {value}")
            
            # Show metadata like in screenshot
            meta = payload.get("meta", {})
            if meta:
                st.markdown("**Meta:**")
                for key, value in meta.items():
                    if isinstance(value, (str, int, float, bool)):
                        st.text(f"• {key}: {value}")
                    elif isinstance(value, list):
                        st.text(f"• {key}: [{len(value)} items]")
            
            # Show order information if present (from screenshot)
            order = payload.get("order", {})
            if order:
                st.markdown("**Order:**")
                order_id = order.get("order_id", "N/A")
                st.text(f"• Order ID: {order_id}")
                
                items = order.get("items", [])
                if items and len(items) > 0:
                    st.text(f"• Items: {len(items)}")
                    for item in items[:2]:  # Show first 2 items
                        product_id = item.get("product_id", "N/A")
                        qty = item.get("quantity", item.get("qty", 1))
                        st.text(f"  - {product_id} x {qty}")
            
            # Show listing if present
            listing = payload.get("listing", {})
            if listing:
                st.markdown("**Listing:**")
                for key, value in listing.items():
                    if isinstance(value, (str, int, float, bool)):
                        st.text(f"• {key}: {value}")
            
            # Show payment and shipping info
            if "payment_method" in payload:
                st.text(f"• Payment: {payload['payment_method']}")
            if "ship_to_country" in payload:
                st.text(f"• Ship to: {payload['ship_to_country']}")
        
        # Show metadata section (always show this)
        st.markdown("---")
        st.markdown("##### 📊 Metadata")
        
        # Get ADRA info for display
        adra_id = adra.get("adra_id", "UNKNOWN") if adra else "UNKNOWN"
        timestamp = adra.get("timestamp_utc", "UNKNOWN") if adra else "UNKNOWN"
        
        # Try to get L2 provenance
        if adra:
            l2 = adra.get("L2_input_snapshot_and_dra") or adra.get("L2_input_snapshot_and_provenance") or adra.get("L2")
            if l2:
                provenance = l2.get("provenance", {})
                fields_present = provenance.get("fields_present", [])
                input_hash = l2.get("input_hash_sha256", "UNKNOWN")
                
                # Show in a clean format
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**ADRA ID:**  \n`{adra_id}`")
                    st.markdown(f"**Timestamp:**  \n`{timestamp}`")
                    st.markdown(f"**Fields:** {len(payload)}")
                
                with col2:
                    st.markdown(f"**Input Hash:**  \n`{input_hash[:20]}...`")
                    if fields_present:
                        st.markdown(f"**Fields Present:** {len(fields_present)}")
        
        # Raw JSON view toggle
        with st.expander("📄 View Full Request JSON", expanded=False):
            st.json(payload)


def _render_no_payload_message():
    """Render message when no payload is available"""
    with st.expander("📋 Request Details", expanded=True):
        st.markdown("##### 🎯 **Input Sent to GNCE**")
        
        # Check if we're in a fresh state
        if not st.session_state.get("has_run_gnce", False):
            st.info("""
            **No GNCE run yet.**
            
            Configure your input in the sidebar and run GNCE to see the request details here.
            
            The input you configure will appear exactly as you enter it.
            """)
        else:
            st.warning("""
            **Request payload not available.**
            
            This could be because:
            1. The ADRA doesn't contain the original input
            2. The input editor wasn't used
            3. Session state was cleared
            
            Try running GNCE again with input editing enabled in the sidebar.
            """)
            
            # Show what we do have
            current_adra = st.session_state.get("current_adra", {})
            if current_adra:
                st.markdown("**Available ADRA Info:**")
                adra_id = current_adra.get("adra_id", "UNKNOWN")
                timestamp = current_adra.get("timestamp_utc", "UNKNOWN")
                st.text(f"ADRA ID: {adra_id}")
                st.text(f"Timestamp: {timestamp}")


def _simulate_actuator_response(
    payload: Dict[str, Any],
    adra: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Enhanced actuator response simulation with better visuals.
    """
    l1 = (adra or {}).get("L1_the_verdict_and_constitutional_outcome") or {}
    l7 = (adra or {}).get("L7_veto_and_execution_feedback") or {}

    decision = str(l1.get("decision_outcome", "UNKNOWN")).upper()
    severity = str(l1.get("severity", "UNKNOWN")).upper()
    human_oversight = bool(l1.get("human_oversight_required", False))

    execution_authorized = bool(
        l7.get("execution_authorized", decision == "ALLOW")
    )
    veto_category = str(l7.get("veto_category", "NONE")).upper()

    # -----------------------------
    # 1) Core actuator decision with visual indicators
    # -----------------------------
    if not execution_authorized or decision == "DENY":
        actuator_decision = "REFUSE_ACTION"
        final_outcome = "ACTION_REFUSED"
        decision_emoji = "❌"
        decision_color = "danger"
    elif human_oversight:
        actuator_decision = "ESCALATE_TO_HUMAN"
        final_outcome = "ACTION_ESCALATED"
        decision_emoji = "👁️"
        decision_color = "warning"
    else:
        actuator_decision = "EXECUTE_ACTION"
        final_outcome = "ACTION_EXECUTED"
        decision_emoji = "✅"
        decision_color = "success"

    # -----------------------------
    # 2) Human-readable reason with better formatting
    # -----------------------------
    reason_lines: list[str] = []

    if actuator_decision == "REFUSE_ACTION":
        if veto_category == "CONSTITUTIONAL_BLOCK":
            reason_lines.append(
                "🚫 **Constitutional Block** - GNCE detected HIGH/CRITICAL legal violations"
            )
            reason_lines.append("_Impact: Action permanently blocked, violation logged_")
        elif veto_category == "DRIFT_BLOCK":
            reason_lines.append(
                "📈 **Behavioral Drift Block** - GNCE detected abnormal pattern"
            )
            reason_lines.append("_Impact: Action blocked, system flagged for review_")
        else:
            reason_lines.append(
                "⛔ **GNCE Veto** - Verdict is not safe to execute"
            )
            reason_lines.append("_Impact: Action blocked pending review_")
    elif actuator_decision == "ESCALATE_TO_HUMAN":
        reason_lines.append("👥 **Human Oversight Required**")
        reason_lines.append("_GNCE allowed in principle but flagged for human review_")
        reason_lines.append("_Status: Queued for manual decision_")
    else:
        reason_lines.append("✅ **Approved for Execution**")
        reason_lines.append("_GNCE verdict is ALLOW with no veto conditions_")
        reason_lines.append("_Status: Ready for downstream processing_")

    # -----------------------------
    # 3) Enhanced downstream effects simulation
    # -----------------------------
    req_type = str(payload.get("request_type", "")).upper()
    action = str(payload.get("action", "")).upper()
    user_id = payload.get("user_id") or payload.get("actor_id") or "user"

    effects: list[str] = []

    # Check for e-commerce content from screenshot
    action_lower = action.lower()
    if "indimage" in action_lower or "ecommerce" in str(payload.get("industry_id", "")).lower():
        content_label = payload.get("content") or payload.get("content_id") or "product listing"
        
        if final_outcome == "ACTION_EXECUTED":
            effects.append(f"📢 **Published**: `{content_label}` is now live on marketplace")
            if severity in {"HIGH", "CRITICAL"}:
                effects.append("⚠️ **Note**: High severity context recorded in audit log")
            # Add e-commerce specific effects
            order_info = payload.get("order", {})
            if order_info:
                order_id = order_info.get("order_id", "UNKNOWN")
                effects.append(f"📦 **Order**: `{order_id}` processed successfully")
        elif final_outcome == "ACTION_REFUSED":
            effects.append(f"🚫 **Blocked**: `{content_label}` rejected by marketplace policy")
            effects.append(f"📋 **User Action**: `{user_id}` received policy violation notice")
            effects.append("📊 **System**: Incident logged in moderation dashboard")
        else:  # ACTION_ESCALATED
            effects.append(f"👥 **Escalated**: `{content_label}` sent to marketplace review")
            effects.append(f"⏳ **Status**: Awaiting decision from marketplace moderation")
            effects.append("📋 **Queue**: Added to priority review queue")
    
    elif req_type == "FINANCIAL_TRANSACTION" or action in {"TRANSFER", "WITHDRAW", "PAYMENT"}:
        if final_outcome == "ACTION_EXECUTED":
            effects.append("💰 **Executed**: Transaction processed successfully")
            effects.append("📋 **Status**: Funds transferred, receipt generated")
        elif final_outcome == "ACTION_REFUSED":
            effects.append("🚫 **Blocked**: Transaction flagged for compliance")
            effects.append("📊 **System**: SAR report triggered automatically")
        else:
            effects.append("👥 **Review**: Transaction sent for compliance review")
            effects.append("⏳ **Status**: Manual approval required")
    
    else:
        # Generic template
        if final_outcome == "ACTION_EXECUTED":
            effects.append("✅ **Approved**: Request processed by downstream system")
            effects.append("📋 **Status**: Action completed successfully")
        elif final_outcome == "ACTION_REFUSED":
            effects.append("🚫 **Denied**: Request blocked by policy enforcement")
            effects.append("📊 **System**: Incident logged for audit trail")
        else:
            effects.append("👥 **Escalated**: Requires human oversight")
            effects.append("⏳ **Status**: Pending manual review")

    return {
        "actuator_decision": actuator_decision,
        "final_outcome": final_outcome,
        "decision_emoji": decision_emoji,
        "decision_color": decision_color,
        "reason_lines": reason_lines,
        "simulated_effects": effects,
        "veto_category": veto_category,
        "execution_authorized": execution_authorized,
        "gnce_decision": decision,
        "gnce_severity": severity,
        "human_oversight_required": human_oversight,
        "timestamp_utc": adra.get("timestamp_utc", ""),
        "adra_id": adra.get("adra_id", ""),
        "_source": "simulated_from_gnce_output",
    }


# -------------------------------------------------------
#  Enhanced Public Renderer
# -------------------------------------------------------

def render_autonomous_execution_loop(adra: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced renderer for the Requester → GNCE → Actuator loop.
    
    Returns:
        actuator_response dict for SARS ledger persistence.
    """

    if not isinstance(adra, dict):
        st.info("📭 No ADRA available yet. Run GNCE at least once.")
        st.session_state["has_run_gnce"] = False
        return {}

    # Mark that we've run GNCE
    st.session_state["has_run_gnce"] = True
    
    # Store the ADRA in session for reference
    st.session_state["current_adra"] = adra

    st.markdown("### 🔄 Autonomous Execution Loop")
    st.caption("Requester → GNCE → Actuator workflow visualization")

    # Get the ACTUAL input that was fired (not reconstructed from ADRA)
    payload = _get_request_payload_for_display(adra)
    
    # Generate actuator response
    actuator_response = _simulate_actuator_response(payload, adra)

    l1 = adra.get("L1_the_verdict_and_constitutional_outcome") or {}
    l7 = adra.get("L7_veto_and_execution_feedback") or {}

    decision = l1.get("decision_outcome", "UNKNOWN")
    severity = l1.get("severity", "UNKNOWN")
    
    # Get drift outcome from multiple possible locations
    drift_outcome = (
        adra.get("drift_outcome") or
        (adra.get("L6_behavioral_drift_and_monitoring") or {}).get("drift_outcome") or
        (adra.get("L6") or {}).get("drift_outcome") or
        "NO_DRIFT"
    )

    # ---------------------------------------------------
    # Layout: 3 columns with visual arrows
    # ---------------------------------------------------
    col_req, arrow1, col_gnce, arrow2, col_act = st.columns([1.0, 0.2, 1.0, 0.2, 1.0])

    # Arrow 1
    with arrow1:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; font-size: 24px;'>➡️</div>", unsafe_allow_html=True)
        st.caption("Request")

    # Arrow 2
    with arrow2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; font-size: 24px;'>➡️</div>", unsafe_allow_html=True)
        st.caption("Verdict")

    # 1) Requester - Show ACTUAL input that was fired
    with col_req:
        st.markdown("##### 👤 **Requester**")
        st.caption("AI Agent or User")
        
        # Show the actual request payload that was sent
        _render_request_payload(payload, adra)
        
        # Show provenance/context if available
        with st.expander("🔍 Input Provenance", expanded=False):
            # Show where the input came from
            original_input = _get_original_input_from_session()
            input_source = "Unknown"
            if original_input and payload == original_input:
                input_source = "Input Editor (sidebar)"
            elif payload and adra.get("L2_input_snapshot_and_dra"):
                input_source = "L2 Snapshot in ADRA"
            elif payload:
                input_source = "Reconstructed from ADRA"
            
            st.text(f"Source: {input_source}")
            st.text(f"Payload keys: {list(payload.keys()) if payload else 'None'}")
            
            # Show L2 info if available
            l2 = adra.get("L2_input_snapshot_and_dra") or adra.get("L2_input_snapshot_and_provenance") or adra.get("L2")
            if l2:
                st.markdown("**L2 Context:**")
                st.json(l2, expanded=False)

    # 2) GNCE Verdict
    with col_gnce:
        st.markdown("##### ⚖️ **GNCE**")
        st.caption("Constitutional Engine")
        
        # Decision chips
        decision_color = "success" if decision == "ALLOW" else "danger"
        severity_color = {
            "LOW": "success",
            "MEDIUM": "warning", 
            "HIGH": "danger",
            "CRITICAL": "danger"
        }.get(severity.upper(), "default")
        
        _chip("Decision", str(decision).upper(), decision_color)
        _chip("Severity", str(severity).upper(), severity_color)
        _chip("Drift", str(drift_outcome).upper(), "info" if drift_outcome == "NO_DRIFT" else "warning")
        
        exec_auth = l7.get('execution_authorized', False)
        exec_color = "success" if exec_auth else "danger"
        _chip("Exec Authorized", str(exec_auth), exec_color)
        
        veto_cat = l7.get('veto_category', 'NONE')
        veto_color = "danger" if veto_cat != "NONE" else "default"
        _chip("Veto", str(veto_cat).upper(), veto_color)
        
        # Summary info
        st.markdown("---")
        if l1.get("rationale"):
            st.markdown("**Rationale:**")
            rationale = l1["rationale"]
            if isinstance(rationale, str):
                st.text(rationale[:150] + "..." if len(rationale) > 150 else rationale)
            elif isinstance(rationale, list):
                for line in rationale[:2]:  # Show first 2 lines
                    st.text(f"• {line}")
        
        # Veto details in expander
        with st.expander("🛑 Full GNCE Verdict (L1)", expanded=False):
            st.json(l1, expanded=False)
        
        # Veto artifact
        with st.expander("⚡ Veto Artifact (L7)", expanded=False):
            st.json(l7, expanded=False)
        
        # Supporting layers
        with st.expander("🔬 Supporting Layers (L3-L6)", expanded=False):
            layers = ["L3", "L4", "L5", "L6"]
            for layer in layers:
                layer_data = adra.get(f"{layer}_") or adra.get(layer)
                if layer_data:
                    st.markdown(f"**{layer}:**")
                    st.json(layer_data, expanded=False)

    # 3) Actuator
    with col_act:
        st.markdown("##### ⚡ **Actuator**")
        st.caption("Execution Component")
        
        # Visual decision display
        decision_emoji = actuator_response.get("decision_emoji", "⚡")
        decision_color = actuator_response.get("decision_color", "default")
        
        st.markdown(f"### {decision_emoji} **{actuator_response['actuator_decision']}**")
        st.markdown(f"**Final Outcome:** `{actuator_response['final_outcome']}`")
        
        # Reason
        st.markdown("---")
        st.markdown("##### 📋 Decision Rationale")
        for line in actuator_response["reason_lines"]:
            st.markdown(f"• {line}")
        
        # Platform effects
        st.markdown("---")
        st.markdown("##### 🎯 Platform Impact")
        for effect in actuator_response["simulated_effects"]:
            st.markdown(f"• {effect}")
        
        # Technical details
        with st.expander("🔧 Technical Details", expanded=False):
            st.markdown("**GNCE Basis:**")
            st.text(f"Decision: {actuator_response['gnce_decision']}")
            st.text(f"Severity: {actuator_response['gnce_severity']}")
            st.text(f"Veto Category: {actuator_response['veto_category']}")
            st.text(f"Human Oversight: {actuator_response['human_oversight_required']}")
            
            st.markdown("**Metadata:**")
            if actuator_response.get("adra_id"):
                st.text(f"ADRA ID: {actuator_response['adra_id']}")
            if actuator_response.get("timestamp_utc"):
                st.text(f"Timestamp: {actuator_response['timestamp_utc']}")
            st.text(f"Source: {actuator_response.get('_source', 'unknown')}")
        
        # Full response
        with st.expander("📄 Full Actuator Response", expanded=False):
            st.json(actuator_response, expanded=False)

    # ---------------------------------------------------
    # Final Status & Debug Info
    # ---------------------------------------------------
    st.markdown("---")
    
    # Final status
    final_status = actuator_response["final_outcome"]
    if final_status == "ACTION_EXECUTED":
        st.success(f"### ✅ **ACTION EXECUTED** - Request completed successfully")
    elif final_status == "ACTION_REFUSED":
        st.error(f"### ❌ **ACTION BLOCKED** - Request denied by policy")
    else:
        st.warning(f"### ⏳ **ACTION ESCALATED** - Awaiting human review")
    
    # Debug information
    with st.expander("🔧 Debug Information", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Input Analysis:**")
            
            # Show what we actually displayed
            original_input = _get_original_input_from_session()
            if original_input:
                st.success("✅ Found original input in session state")
                st.text(f"Keys: {list(original_input.keys())}")
            else:
                st.warning("⚠️ No original input in session")
            
            st.text(f"Payload displayed: {list(payload.keys()) if payload else 'None'}")
            st.text(f"Payload size: {len(str(payload))} chars")
            
            # Check for session state keys
            st.markdown("**Session State:**")
            for key in ["gn_input_json_text", "current_input_used", "current_adra"]:
                has_key = key in st.session_state
                status = "✅" if has_key else "❌"
                st.text(f"{status} {key}: {has_key}")
        
        with col2:
            st.markdown("**ADRA Structure:**")
            adra_id = adra.get("adra_id", "UNKNOWN")
            st.text(f"ADRA ID: {adra_id}")
            st.text(f"Timestamp: {adra.get('timestamp_utc', 'UNKNOWN')}")
            
            # Layers present
            layers = []
            for layer in ["L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7"]:
                if adra.get(layer) or adra.get(f"{layer}_"):
                    layers.append(layer)
            st.text(f"Layers: {', '.join(layers) or 'None'}")
            
            # Check for input snapshot
            l2 = adra.get("L2_input_snapshot_and_dra") or adra.get("L2")
            if l2 and l2.get("input_snapshot"):
                st.success("✅ L2 contains input_snapshot")
                snapshot = l2.get("input_snapshot")
                if isinstance(snapshot, dict):
                    st.text(f"Snapshot keys: {list(snapshot.keys())}")
            else:
                st.warning("⚠️ No input_snapshot in L2")

    return actuator_response