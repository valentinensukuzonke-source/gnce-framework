import streamlit as st
from typing import Dict, Any, List

# ============================
#  COLOR SCHEME
# ============================
LAYER_COLORS = {
    "PASS": "#1f8f4e",      # green
    "WARN": "#c9a227",      # amber
    "FAIL": "#b81d2d",      # red
    "VETO": "#b81d2d",      # red
    "DEFAULT": "#3b3b3b",   # grey
}

# ============================
#  HUMAN-READABLE LAYER NAMES
# ============================
LAYER_NAMES = {
    "L0": "Pre-Execution Validation",
    "L1": "The Verdict Engine",
    "L2": "Input Snapshot & Hashing",
    "L3": "Rule-Level Trace",
    "L4": "Policy Lineage & Constitution",
    "L5": "Integrity & Tokenization (CET)",
    "L6": "Behavioral Drift Monitoring",
    "L7": "Veto & Execution Feedback",
}

# ============================
#  STATUS RESOLUTION
# ============================
def _layer_status(layer: str, adra: Dict[str, Any]) -> str:
    """Compute PASS/WARN/FAIL/VETO/DEFAULT per layer from the ADRA."""
    try:
        if layer == "L0":
            l0 = adra.get("L0_pre_execution_validation", {}) or {}
            return "PASS" if l0.get("validated") else "FAIL"

        if layer == "L1":
            l1 = adra.get("L1_meta_verdict", {}) or {}
            return "FAIL" if l1.get("decision_outcome") == "DENY" else "PASS"

        if layer == "L2":
            l2 = adra.get("L2_input_snapshot_and_dra", {}) or {}
            return "PASS" if l2 else "DEFAULT"

        if layer == "L3":
            l3 = adra.get("L3_rule_level_trace", {}) or {}
            summary = l3.get("summary", {}) or {}
            failed = int(summary.get("failed", 0))
            return "PASS" if failed == 0 else "WARN"

        if layer == "L4":
            l4 = adra.get("L4_policy_lineage_and_constitution", {}) or {}
            policies = l4.get("policies_triggered", []) or []
            violated = any(p.get("status") == "VIOLATED" for p in policies)
            return "FAIL" if violated else "PASS"

        if layer == "L5":
            l5 = adra.get("L5_integrity_and_tokenization", {}) or {}
            return "PASS" if l5 else "DEFAULT"

        if layer == "L6":
            drift_outcome = str(adra.get("drift_outcome", "")).upper()
            return "FAIL" if drift_outcome == "DRIFT_ALERT" else "PASS"

        if layer == "L7":
            l7 = adra.get("L7_veto_and_execution_feedback", {}) or {}
            return "VETO" if l7.get("veto_path_triggered") else "PASS"

    except Exception:
        return "DEFAULT"

    return "DEFAULT"


# ============================
#  LAYER DETAIL RENDERING
# ============================
def _render_layer_details(layer: str, adra: Dict[str, Any]):
    st.markdown(f"### 🔍 Details for **{layer} — {LAYER_NAMES.get(layer, layer)}**")
    st.markdown("---")

    if layer == "L0":
        st.json(adra.get("L0_pre_execution_validation", {}))
    elif layer == "L1":
        st.json(adra.get("L1_meta_verdict", {}))
    elif layer == "L2":
        st.json(adra.get("L2_input_snapshot_and_dra", {}))
    elif layer == "L3":
        st.json(adra.get("L3_rule_level_trace", {}))
    elif layer == "L4":
        st.json(adra.get("L4_policy_lineage_and_constitution", {}))
    elif layer == "L5":
        st.json(adra.get("L5_integrity_and_tokenization", {}))
    elif layer == "L6":
        st.json(adra.get("L6_behavioral_drift_and_monitoring", {}))
    elif layer == "L7":
        st.json(adra.get("L7_veto_and_execution_feedback", {}))

    st.markdown("---")


# ============================
#  ROOT-CAUSE TRACEBACK
# ============================
def calculate_root_cause(adra: Dict[str, Any]) -> Dict[str, Any]:
    """
    Infer which layer actually triggered the veto / hard failure.

    Priority:
      - L7 veto artifact
      - L6 drift alert
      - L4 violated policies
      - L3 blocking rule failures
      - Fallback: L1 deny
    """
    result = {
        "layer": "NONE",
        "layer_name": "",
        "reason": "",
        "article": None,
        "severity": None,
        "veto_category": None,
    }

    if not isinstance(adra, dict):
        return result

    l7 = adra.get("L7_veto_and_execution_feedback", {}) or {}
    l6 = adra.get("L6_behavioral_drift_and_monitoring", {}) or {}
    l4 = adra.get("L4_policy_lineage_and_constitution", {}) or {}
    l3 = adra.get("L3_rule_level_trace", {}) or {}
    l1 = adra.get("L1_meta_verdict", {}) or {}

    # 1) Hard veto from L7
    if l7.get("veto_path_triggered"):
        veto_cat = l7.get("veto_category") or "UNKNOWN"
        basis = l7.get("veto_basis", []) or []
        art = None
        severity = None

        for b in basis:
            if b.get("article"):
                art = b.get("article")
                severity = b.get("severity")
                break

        result.update(
            {
                "layer": "L7",
                "layer_name": LAYER_NAMES["L7"],
                "reason": l7.get(
                    "constitutional_citation",
                    "Constitutional veto triggered for this ADRA.",
                ),
                "article": art,
                "severity": severity,
                "veto_category": veto_cat,
            }
        )
        return result

    # 2) Drift alert from L6
    drift_outcome = str(adra.get("drift_outcome", "")).upper()
    if drift_outcome == "DRIFT_ALERT":
        result.update(
            {
                "layer": "L6",
                "layer_name": LAYER_NAMES["L6"],
                "reason": l6.get(
                    "notes",
                    "L6 drift engine reported DRIFT_ALERT for this ADRA, requiring safety escalation.",
                ),
                "article": None,
                "severity": None,
                "veto_category": "DRIFT_BLOCK",
            }
        )
        return result

    # 3) Violated policies at L4
    policies: List[Dict[str, Any]] = l4.get("policies_triggered", []) or []
    violated = [
        p
        for p in policies
        if str(p.get("status", "")).upper() == "VIOLATED"
        and str(p.get("severity", "")).upper() in {"HIGH", "CRITICAL"}
    ]
    if violated:
        v0 = violated[0]
        art = v0.get("article")
        sev = v0.get("severity", "UNKNOWN")
        result.update(
            {
                "layer": "L4",
                "layer_name": LAYER_NAMES["L4"],
                "reason": v0.get(
                    "impact_on_verdict",
                    "High-severity policy violation triggered this decision.",
                ),
                "article": art,
                "severity": sev,
                "veto_category": None,
            }
        )
        return result

    # 4) Blocking failures at L3
    summary = l3.get("summary", {}) or {}
    blocking = int(summary.get("blocking_failures", 0))
    if blocking > 0:
        result.update(
            {
                "layer": "L3",
                "layer_name": LAYER_NAMES["L3"],
                "reason": f"{blocking} blocking rule failure(s) in L3 rule trace.",
                "article": None,
                "severity": None,
                "veto_category": None,
            }
        )
        return result

    # 5) Fallback – L1 deny
    if l1.get("decision_outcome") == "DENY":
        result.update(
            {
                "layer": "L1",
                "layer_name": LAYER_NAMES["L1"],
                "reason": l1.get(
                    "basis", "Meta verdict engine DENY without a more specific root cause."
                ),
                "article": None,
                "severity": l1.get("severity"),
                "veto_category": None,
            }
        )
        return result

    return result


# ============================
#  EXECUTION PATH VISUALIZER
# ============================
def render_execution_path_visualizer(adra: Dict[str, Any]):
    if not isinstance(adra, dict):
        return

    st.subheader("🔍 Execution Path Visualizer (L0 → L7)")

    # --- Root-cause summary banner ---
    root = calculate_root_cause(adra)
    if root["layer"] != "NONE":
        lines = []
        header = f"🔥 **Root-cause:** `{root['layer']}` — {root['layer_name']}"
        lines.append(header)

        meta_bits = []
        if root.get("article"):
            meta_bits.append(f"Article: `{root['article']}`")
        if root.get("severity"):
            meta_bits.append(f"Severity: `{root['severity']}`")
        if root.get("veto_category"):
            meta_bits.append(f"Veto category: `{root['veto_category']}`")

        if meta_bits:
            lines.append(" · ".join(meta_bits))

        if root.get("reason"):
            lines.append("")
            lines.append(root["reason"])

        st.info("\n".join(lines))

    # selection state
    if "epv_selected_layer" not in st.session_state:
        st.session_state.epv_selected_layer = "L0"

    st.markdown("")  # small spacing

    cols = st.columns(8)
    layer_order = ["L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7"]

    for idx, layer in enumerate(layer_order):
        status = _layer_status(layer, adra)
        color = LAYER_COLORS.get(status, LAYER_COLORS["DEFAULT"])
        btn_key = f"EPV_{layer}"
        label = f"{layer} · {status}"

        with cols[idx]:
            clicked = st.button(
                label,
                key=btn_key,
                help=LAYER_NAMES.get(layer, layer),
            )

            # Per-button glassy styling using the HTML id = key
            st.markdown(
                f"""
                <style>
                    div[data-testid="stButton"] button#{btn_key} {{
                        background: linear-gradient(
                            145deg,
                            {color}ee,
                            {color}bb
                        );
                        color: #f9fafb;
                        padding: 18px 8px;
                        border-radius: 18px;
                        border: none;
                        font-weight: 600;
                        width: 100%;
                        height: 86px;
                        box-shadow: 0 10px 26px rgba(15, 23, 42, 0.9);
                        backdrop-filter: blur(14px);
                        -webkit-backdrop-filter: blur(14px);
                        letter-spacing: 0.03em;
                        text-transform: uppercase;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        text-align: center;
                        font-size: 0.80rem;
                        transition: transform 120ms ease-out,
                                    box-shadow 120ms ease-out,
                                    background 120ms ease-out;
                    }}
                    div[data-testid="stButton"] button#{btn_key}:hover {{
                        transform: translateY(-1px) scale(1.01);
                        box-shadow: 0 18px 34px rgba(15, 23, 42, 0.95);
                    }}
                </style>
                """,
                unsafe_allow_html=True,
            )

            if clicked:
                st.session_state.epv_selected_layer = layer

    st.markdown("---")

    if st.session_state.epv_selected_layer:
        _render_layer_details(st.session_state.epv_selected_layer, adra)


# ============================
#  ANIMATED EXECUTION FLOW
# ============================
def render_execution_flow_graph(adra: Dict[str, Any]):
    if not isinstance(adra, dict):
        return

    st.subheader("⏱️ Animated Execution Flow (L0 → L7)")
    st.caption(
        "Hover for details — arrows pulse to show direction; root-cause layer is emphasised."
    )

    # CSS for pulsing arrows
    st.markdown(
        """
        <style>
        @keyframes epv-flow-pulse {
            0%   { opacity: 0.20; transform: translateX(0px); }
            50%  { opacity: 1.0;  transform: translateX(5px); }
            100% { opacity: 0.20; transform: translateX(0px); }
        }
        .epv-flow-arrow {
            animation: epv-flow-pulse 1.8s infinite ease-in-out;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    layer_order = ["L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7"]

    root = calculate_root_cause(adra)
    root_layer = root.get("layer")
    selected_layer = st.session_state.get("epv_selected_layer", "L0")

    def _hex_to_rgba(hex_color: str, alpha: float) -> str:
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"

    flow_html = """
    <div style="
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem 0.5rem 0.5rem 0.25rem;
    ">
    """

    for i, layer in enumerate(layer_order):
        status = _layer_status(layer, adra)
        base_hex = LAYER_COLORS.get(status, LAYER_COLORS["DEFAULT"])
        title = LAYER_NAMES.get(layer, layer)

        is_selected = (layer == selected_layer)
        is_root = (layer == root_layer)

        col_center = _hex_to_rgba(base_hex, 0.45)
        col_edge = _hex_to_rgba(base_hex, 0.18)

        border_color = (
            _hex_to_rgba(base_hex, 0.85)
            if is_selected or is_root
            else "rgba(55,65,81,0.85)"
        )
        box_shadow = (
            "0 0 0 1px rgba(248, 250, 252, 0.9), 0 10px 22px rgba(15, 23, 42, 0.8)"
            if is_root
            else "0 8px 18px rgba(15, 23, 42, 0.65)"
        )

        flow_html += f"""
        <div
           title="{layer} — {title} ({status})"
           style="
                width: 56px;
                height: 56px;
                border-radius: 999px;
                border: 2px solid {border_color};
                background: radial-gradient(circle at 30% 30%, {col_center}, {col_edge});
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                box-shadow: {box_shadow};
                color: #f9fafb;
                font-size: 0.80rem;
                font-weight: 700;
                text-align: center;
                cursor: default;
                backdrop-filter: blur(14px);
                -webkit-backdrop-filter: blur(14px);
           ">
            <div style="font-size: 0.75rem; margin-bottom: -2px;">{layer}</div>
            <div style="font-size: 0.55rem; opacity: 0.85;">{status}</div>
        </div>
        """

        if i < len(layer_order) - 1:
            flow_html += """
            <div class="epv-flow-arrow" style="
                width: 32px;
                height: 2px;
                background: linear-gradient(
                    90deg,
                    rgba(156,163,175,0.10),
                    rgba(249,250,251,0.85),
                    rgba(156,163,175,0.10)
                );
                border-radius: 999px;
                position: relative;
            ">
                <div style="
                    position: absolute;
                    right: -4px;
                    top: -3px;
                    width: 0;
                    height: 0;
                    border-top: 5px solid transparent;
                    border-bottom: 5px solid transparent;
                    border-left: 7px solid rgba(249,250,251,0.98);
                "></div>
            </div>
            """

    flow_html += "</div>"

    st.markdown(flow_html, unsafe_allow_html=True)
