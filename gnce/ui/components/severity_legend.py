# ui/components/severity_legend.py
from typing import Any
import streamlit as st


def inject_severity_css() -> None:
    """
    Global CSS for GNCE severity pills + Streamlit tag components.

    This is injected once from gn_app.py so all components share the same look.
    """
    st.markdown(
        """
<style>
/* Base tags used by st.tags / BaseWeb Tag */
div[data-baseweb="tag"] {
    border-radius: 999px !important;
    padding: 2px 8px !important;
    font-size: 0.70rem !important;
    font-weight: 600 !important;
    background-color: #111827 !important;
    color: #e5e7eb !important;
    border: 1px solid #1f2937 !important;
}

/* Severity-specific pills (we use classes in severity_tag) */
.gnce-pill {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0.14rem 0.65rem;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    white-space: nowrap;
}

/* Color bands */
.gnce-pill-low {
    background: #00916E;
    color: #020617;
}

.gnce-pill-medium {
    background: #ffb300;
    color: #111827;
}

.gnce-pill-high {
    background: #C62828;
    color: #F9FAFB;
}

.gnce-pill-critical {
    background: #8b008b;
    color: #F9FAFB;
}

.gnce-pill-unknown {
    background: #4b5563;
    color: #e5e7eb;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def severity_tag(sev: Any) -> str:
    """
    Return an HTML pill for a severity band:
    LOW / MEDIUM / HIGH / CRITICAL / UNKNOWN.
    """
    s = str(sev or "").upper()
    if s == "LOW":
        cls = "gnce-pill gnce-pill-low"
        label = "LOW"
    elif s == "MEDIUM":
        cls = "gnce-pill gnce-pill-medium"
        label = "MEDIUM"
    elif s == "HIGH":
        cls = "gnce-pill gnce-pill-high"
        label = "HIGH"
    elif s == "CRITICAL":
        cls = "gnce-pill gnce-pill-critical"
        label = "CRITICAL"
    else:
        cls = "gnce-pill gnce-pill-unknown"
        label = s or "UNKNOWN"

    return f"<span class='{cls}'>{label}</span>"


def render_severity_legend() -> None:
    """
    Small legend showing what the four severity bands mean.
    """
    st.markdown("#### GNCE Severity Bands")

    col_low, col_med, col_high, col_crit = st.columns(4)

    col_low.markdown(severity_tag("LOW"), unsafe_allow_html=True)
    col_low.caption("Residual risk is acceptable with standard controls.")

    col_med.markdown(severity_tag("MEDIUM"), unsafe_allow_html=True)
    col_med.caption("Meaningful risk; needs closer oversight or mitigation.")

    col_high.markdown(severity_tag("HIGH"), unsafe_allow_html=True)
    col_high.caption("Serious risk; only justified in exceptional scenarios.")

    col_crit.markdown(severity_tag("CRITICAL"), unsafe_allow_html=True)
    col_crit.caption("Unacceptable risk under the current constitution.")
