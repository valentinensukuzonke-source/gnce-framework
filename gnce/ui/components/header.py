# ui/components/header.py
from pathlib import Path
import base64
import streamlit as st

def _load_logo_base64(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def render_header(stats: dict, mode: str, base_dir: Path) -> None:
    """Top header: title, badges, metrics, spinning GN logo."""
    assets_dir = base_dir / "ui" / "assets"
    logo_mark_path = assets_dir / "gn_logo_mark.png"
    logo_mark_b64 = _load_logo_base64(logo_mark_path)

    st.set_page_config(
        page_title="The Gordian Nexus Constitutional Engine — v0.7.0",
        page_icon="🧠",
        layout="wide",
    )

    # global CSS you already had (block-container, gn-badge, etc.)
    st.markdown(
        """
        <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        header { visibility: hidden; }
        .gn-header-title { font-size: 2.1rem; font-weight: 700; margin-bottom: 0.25rem; }
        .gn-header-subtitle { font-size: 0.95rem; opacity: 0.8; margin-bottom: 0.5rem; }
        .gn-badge {
            display:inline-block; padding:0.15rem 0.6rem; border-radius:999px;
            font-size:0.75rem; font-weight:600;
            background:rgba(0,179,201,0.1); color:#00b3c9;
            border:1px solid rgba(0,179,201,0.3); margin-right:0.25rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    col_title, col_metrics, col_logo = st.columns([5, 3, 2])

    with col_title:
        st.markdown(
            """
            <div style="display:flex; flex-direction:column; gap:0.25rem;">
                <div class="gn-header-title">
                    The Gordian Nexus Constitutional Engine — v0.7.0
                </div>
                <div class="gn-header-subtitle">
                    Constitutional OS for Autonomous Systems 
                </div>
                <div style="display:flex; gap:0.5rem; margin-top:0.4rem;">
                    <span class="gn-badge">Deterministic Governance</span>
                    <span class="gn-badge">ADRA Engine</span>
                    <span class="gn-badge">GNCE Constitutional Layers</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_metrics:
        total_runs = stats.get("total_runs", 0)
        allow_rate = (
            stats.get("allow_count", 0) / total_runs if total_runs else 0.0
        )
        deny_rate = (
            stats.get("deny_count", 0) / total_runs if total_runs else 0.0
        )
        risk_band = stats.get("session_risk_band", "N/A")
        avg_score = stats.get("avg_severity_score", 0.0)

        mcols = st.columns(4)
        label_total = (
            "Total ADRAs (session)"
            if mode == "Production View"
            else "Total runs (lab session)"
        )
        mcols[0].metric(label_total, total_runs)
        mcols[1].metric("ALLOW % (session)", f"{allow_rate * 100:0.1f}%")
        mcols[2].metric("DENY % (session)", f"{deny_rate * 100:0.1f}%")
        mcols[3].metric("Session Risk Level", f"{risk_band} ({avg_score:0.2f})")

    with col_logo:
        st.markdown(
            f"""
            <style>
            .gn-logo-card {{
                display:flex; justify-content:center; align-items:center;
                width:160px; height:100px; border-radius:20px;
                background: radial-gradient(circle at 0% 0%, #e3f6ff, #0f172a);
                box-shadow: 0 10px 25px rgba(0,0,0,0.35); padding:8px;
            }}
            .gn-logo-mark {{
                width:120px; animation: gn-spin 16s linear infinite;
            }}
            @keyframes gn-spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            </style>
            <div class="gn-logo-card">
                <img src="data:image/png;base64,{logo_mark_b64}" class="gn-logo-mark" />
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
