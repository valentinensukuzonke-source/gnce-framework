import streamlit as st
import json
from pathlib import Path

# ----------------------------------------------------
#  EPV GRAPH (D3.js Interactive Graph)
# ----------------------------------------------------

ASSET_DIR = Path(__file__).parent / "epv_assets"


def _load_asset(name: str) -> str:
    """Load HTML, JS or CSS asset."""
    path = ASSET_DIR / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def render_execution_flow_graph(adra: dict):
    """
    Renders the D3.js Execution Flow Diagram (Option B).
    Appears below the EPV tile bar.
    """
    if not isinstance(adra, dict):
        return

    st.markdown("### 🔵 Constitutional Execution Graph (Interactive)")

    # ----------------------------------------------------
    # Prepare ADRA data for JS
    # ----------------------------------------------------
    graph_data = {
        "layers": [
            {"id": "L0", "name": "Pre-Execution Validation"},
            {"id": "L1", "name": "Verdict"},
            {"id": "L2", "name": "Input Snapshot"},
            {"id": "L3", "name": "Rule Trace"},
            {"id": "L4", "name": "Policy Lineage"},
            {"id": "L5", "name": "CET Integrity"},
            {"id": "L6", "name": "Drift Monitoring"},
            {"id": "L7", "name": "Execution Veto"},
        ],
        "status": {
            "L0": adra.get("L0_pre_execution_validation", {}).get("validated"),
            "L1": adra.get("L1_the_verdict_and_constitutional_outcome", {}).get("decision_outcome"),
            "L3": adra.get("L3_rule_level_trace", {}).get("summary", {}).get("failed"),
            "L4": any(
                p.get("status") == "VIOLATED"
                for p in adra.get("L4_policy_lineage_and_constitution", {}).get("policies_triggered", [])
            ),
            "L6": adra.get("drift_outcome"),
            "L7": adra.get("L7_veto_and_execution_feedback", {}).get("veto_path_triggered"),
        },
        "timestamps": {
            "L1": adra.get("L1_the_verdict_and_constitutional_outcome", {}).get("timestamp_utc"),
        },
    }

    encoded = json.dumps(graph_data)

    # ----------------------------------------------------
    # Render the HTML container
    # ----------------------------------------------------
    html_template = _load_asset("epv_graph.html")
    js_code = _load_asset("epv_graph.js")
    css_code = _load_asset("epv_graph.css")

    final_html = f"""
    <style>{css_code}</style>
    {html_template}
    <script>
        const GNCE_GRAPH_DATA = {encoded};
        {js_code}
    </script>
    """

    st.components.v1.html(final_html, height=480, scrolling=False)
