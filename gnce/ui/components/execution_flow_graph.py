import streamlit as st
from typing import Dict, Any
import uuid
import json
import hashlib

LAYER_ORDER = ["L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7"]

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

def _layer_status(layer: str, adra: Dict[str, Any]) -> str:
    """Status logic aligned with EPV tiles."""
    try:
        if layer == "L0":
            return "FAIL" if not adra["L0_pre_execution_validation"].get("validated") else "PASS"
        if layer == "L1":
            return "FAIL" if adra["L1_the_verdict_and_constitutional_outcome"]["decision_outcome"] == "DENY" else "PASS"
        if layer == "L3":
            return "WARN" if adra["L3_rule_level_trace"]["summary"].get("failed", 0) > 0 else "PASS"
        if layer == "L4":
            violated = any(
                p.get("status") == "VIOLATED"
                for p in adra["L4_policy_lineage_and_constitution"]["policies_triggered"]
            )
            return "FAIL" if violated else "PASS"
        if layer == "L6":
            return "FAIL" if adra.get("drift_outcome") == "DRIFT_ALERT" else "PASS"
        if layer == "L7":
            return "FAIL" if adra["L7_veto_and_execution_feedback"].get("veto_path_triggered") else "PASS"
    except Exception:
        return "DEFAULT"
    return "DEFAULT"


COLOR_MAP = {
    "PASS": "#2ecc71AA",     # Glass green
    "WARN": "#f1c40fAA",     # Glass yellow
    "FAIL": "#e74c3cAA",     # Glass red
    "DEFAULT": "#95a5a6AA",  # Glass grey
}

def _sha256_obj(obj: Any) -> str:
    try:
        s = json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
        return "sha256:" + hashlib.sha256(s).hexdigest()
    except Exception:
        return ""

def _extract_cet(adra: Dict[str, Any]) -> Dict[str, Any]:
    # Accept a few common shapes across versions
    cet = adra.get("cet") or adra.get("CET")
    if isinstance(cet, dict):
        return cet

    # Sometimes embedded under L5
    l5 = (
        adra.get("L5_integrity_and_tokenization")
        or adra.get("L5_integrity_and_tokenization_(CET)")
        or {}
    )
    if isinstance(l5, dict):
        cet2 = l5.get("CET") or l5.get("cet")
        if isinstance(cet2, dict):
            return cet2

    return {}

def _cet_hash_for_layer(adra: Dict[str, Any], layer: str) -> str:
    """
    Best-effort:
    1) Look for explicit CET-provided hashes
    2) Fallback to hashing the layer payload deterministically
    """
    cet = _extract_cet(adra)

    for key in ("content_hashes", "layer_hashes", "hashes"):
        m = cet.get(key)
        if isinstance(m, dict):
            v = m.get(layer)
            if isinstance(v, str) and v:
                return v

    # Sometimes CET has a single hash (still useful)
    if layer in ("L1", "L3", "L4"):
        v = cet.get("content_hash") or cet.get("hash") or ""
        if isinstance(v, str) and v:
            return v

    # Fallback: hash the layer object itself
    layer_obj: Any = None
    if layer == "L1":
        layer_obj = adra.get("L1_the_verdict_and_constitutional_outcome")
    elif layer == "L3":
        layer_obj = adra.get("L3_rule_level_trace")
    elif layer == "L4":
        layer_obj = adra.get("L4_policy_lineage_and_constitution")

    if layer_obj is not None:
        return _sha256_obj(layer_obj)

    return ""

def _short_hash(h: str, n: int = 12) -> str:
    if not h:
        return ""
    if h.startswith("sha256:") and len(h) > 7:
        return "sha256:" + h[7: 7 + n]
    return h[:n]

def render_execution_flow_graph(adra: Dict[str, Any], key_prefix: str = "flow") -> None:
    """SVG interactive flow between L0→L7 with CET binding on L1/L3/L4."""
    if not isinstance(adra, dict):
        return

    st.markdown("### 🧭 Animated Execution Flow (L0 → L7)")
    st.caption("Hover for details — CET binds are shown on L1/L3/L4. Click a node to jump to the layer in the Execution Path Visualizer.")

    svg_id = f"epv_svg_{key_prefix}_{uuid.uuid4().hex}"
    tip_id = f"epv_tip_{key_prefix}_{uuid.uuid4().hex}"
    wrap_id = f"epv_wrap_{key_prefix}_{uuid.uuid4().hex}"

    # Single source of truth for CET binds
    cet_map: Dict[str, Dict[str, str]] = {}
    for L in ("L1", "L3", "L4"):
        h = _cet_hash_for_layer(adra, L)
        if h:
            cet_map[L] = {
                "hash": h,
                "short": _short_hash(h),
                "label": LAYER_NAMES.get(L, L),
            }

    circles_svg = ""
    arrows_svg = ""

    # Layout tuned to fit in your middle column cleanly
    x_step = 78
    y_center = 60
    start_x = 26
    node_r = 18

    for i, layer in enumerate(LAYER_ORDER):
        x = start_x + i * x_step
        status = _layer_status(layer, adra)
        color = COLOR_MAP.get(status, COLOR_MAP["DEFAULT"])
        name = LAYER_NAMES.get(layer, layer)

        # CET visual binding: subtle glow ring on L1/L3/L4 (no hash text under node)
        cet_ring = ""
        if layer in cet_map:
            ring_r = node_r + 5
            cet_ring = f"""
            <circle cx="{x}" cy="{y_center}" r="{ring_r}"
                    fill="none"
                    stroke="rgba(56,189,248,0.55)"
                    stroke-width="2.5"/>
            <circle cx="{x}" cy="{y_center}" r="{ring_r + 2}"
                    fill="none"
                    stroke="rgba(56,189,248,0.18)"
                    stroke-width="6"/>
            """
        circles_svg += f"""
        <g class="node" data-layer="{layer}" data-name="{name}">
            {cet_ring}
            <circle cx="{x}" cy="{y_center}" r="{node_r}"
                    fill="{color}" stroke="#ffffffAA" stroke-width="2"/>
            <text x="{x}" y="{y_center+4}" text-anchor="middle"
                  fill="white" font-size="12" font-weight="600">{layer}</text>
        </g>
        """

        if i < len(LAYER_ORDER) - 1:
            x2 = start_x + (i + 1) * x_step
            arrows_svg += f"""
            <line x1="{x + node_r + 10}" y1="{y_center}"
                  x2="{x2 - node_r - 10}" y2="{y_center}"
                  stroke="rgba(255,255,255,0.65)" stroke-width="2"
                  marker-end="url(#arrow)"/>
            """

    total_w = int(2 * start_x + (len(LAYER_ORDER) - 1) * x_step + 2 * node_r)

    # JSON injection (safe)
    cet_json = json.dumps(cet_map, ensure_ascii=False)

    html = f"""
<div id="{wrap_id}" style="position:relative; width:100%;">
  <svg id="{svg_id}" width="100%" height="156" viewBox="0 0 {total_w} 156"
       preserveAspectRatio="xMidYMid meet"
       style="margin-top:10px; width:100%; max-width:100%; display:block;">
      <defs>
          <marker id="arrow" markerWidth="12" markerHeight="12" refX="6" refY="6"
                  orient="auto" markerUnits="strokeWidth">
              <path d="M0,0 L0,12 L12,6 z" fill="rgba(255,255,255,0.65)" />
          </marker>
      </defs>
      {arrows_svg}
      {circles_svg}
  </svg>

  <div id="{tip_id}"
       style="
        position:absolute; display:none; z-index:9999;
        min-width:240px; max-width:360px;
        background: rgba(2,6,23,0.92);
        border: 1px solid rgba(148,163,184,0.25);
        border-radius: 14px;
        padding: 10px 12px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.45);
        color: #e2e8f0;cet_map
       "></div>

  <div style="margin-top:10px; display:flex; gap:10px; flex-wrap:wrap;">
    <div style="opacity:0.8; color:#ffffff;CET binds font-size:0.86rem;">🔐 CET binds:</div>
    <div id="{wrap_id}_chips" style="display:flex; gap:10px; flex-wrap:wrap;"></div>
  </div>

  <div style="
        margin-top:12px;
        padding:10px 12px;
        border-radius:14px;
        border:1px solid rgba(148,163,184,0.16);
        background:rgba(2,6,23,0.35);
    ">
    <div style="display:flex; align-items:center; justify-content:space-between; gap:12px;">
        <div style="font-weight:800; opacity:0.9;">🔐 CET proof bindings</div>
        <div style="opacity:0.7; font-size:0.82rem;">click a pill to copy</div>
    </div>
    <div id="{wrap_id}_chips" style="margin-top:10px; display:flex; gap:10px; flex-wrap:wrap;"></div>
   </div>

  


    # replace L222-L225 block inside the html f-string
    <div style="
        margin-top:12px;
        padding:10px 12px;
        border-radius:14px;
        border:1px solid rgba(148,163,184,0.16);
        background:rgba(2,6,23,0.35);
    ">
    <div style="display:flex; align-items:center; justify-content:space-between; gap:12px;">
        <div style="font-weight:800; opacity:0.9;">🔐 CET proof bindings</div>
        <div style="opacity:0.7; font-size:0.82rem;">click a pill to copy</div>
    </div>
    <div id="{wrap_id}_chips" style="margin-top:10px; display:flex; gap:10px; flex-wrap:wrap;"></div>
    </div>

    





  <script>
    const CET = {cet_json};

    const wrap = document.getElementById("{wrap_id}");
    const svg = document.getElementById("{svg_id}");
    const tip = document.getElementById("{tip_id}");
    const chips = document.getElementById("{wrap_id}_chips");

    function esc(s) {{
      return String(s || "").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
    }}

    function showTip(evt, layer, name) {{
      const has = (CET && CET[layer] && CET[layer].hash);
      const badge = has
        ? '<div style="padding:5px 10px;border-radius:999px;border:1px solid rgba(56,189,248,0.35);background:rgba(56,189,248,0.08);color:#38bdf8;font-weight:900;font-size:0.80rem;">CET-bound</div>'
        : '';

      const hashLine = has
        ? ('<div style="margin-top:8px;font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, \\'Liberation Mono\\', \\'Courier New\\', monospace;font-size:0.88rem;opacity:0.95;">' + esc(CET[layer].hash) + '</div>')
        : '';

      tip.innerHTML =
        '<div style="display:flex;justify-content:space-between;gap:12px;align-items:center;">' +
          '<div>' +
            '<div style="font-weight:900;font-size:1.02rem;">' + esc(layer) + ' — ' + esc(name) + '</div>' +
            '<div style="opacity:0.85;margin-top:2px;">Hover proof • Click to jump</div>' +
          '</div>' +
          badge +
        '</div>' +
        hashLine;

      const r = wrap.getBoundingClientRect();
      const x = evt.clientX - r.left + 12;
      const y = evt.clientY - r.top + 12;

      tip.style.left = x + "px";
      tip.style.top = y + "px";
      tip.style.display = "block";
    }}

    function hideTip() {{
      tip.style.display = "none";
    }}

    // Chips row (click to copy)
    ["L1","L3","L4"].forEach(L => {{
      if (!CET[L] || !CET[L].hash) return;
      const el = document.createElement("div");
      el.style.cssText = "cursor:pointer; padding:6px 10px; border-radius:999px; border:1px solid rgba(148,163,184,0.22); background:rgba(2,6,23,0.55); color:#e2e8f0; font-weight:900; font-size:0.86rem;";
      el.innerHTML = "🔐 " + L + " • <span style=\\"font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; opacity:0.9;\\">" + esc(CET[L].short || CET[L].hash) + "</span>";
      el.onclick = async () => {{
        try {{
          await navigator.clipboard.writeText(CET[L].hash);
          el.style.borderColor = "rgba(56,189,248,0.55)";
          el.style.boxShadow = "0 0 0 1px rgba(56,189,248,0.15) inset";
          setTimeout(() => {{
            el.style.borderColor = "rgba(148,163,184,0.22)";
            el.style.boxShadow = "none";
          }}, 800);
        }} catch(e) {{}}
      }};
      chips.appendChild(el);
    }});

    // Node events
    svg.querySelectorAll(".node").forEach(n => {{
      const layer = n.getAttribute("data-layer");
      const name = n.getAttribute("data-name") || layer;

      n.addEventListener("mouseenter", (evt) => showTip(evt, layer, name));
      n.addEventListener("mousemove", (evt) => showTip(evt, layer, name));
      n.addEventListener("mouseleave", hideTip);

      n.addEventListener("click", () => {{
        window.parent.postMessage({{ type: "epv_select_layer", layer: layer }}, "*");
      }});
    }});
  </script>
</div>
"""

    st.components.v1.html(html, height=250, scrolling=False)
