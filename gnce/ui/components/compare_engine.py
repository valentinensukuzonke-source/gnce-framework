# ui/components/compare_engine.py
from __future__ import annotations

from typing import Dict, Any, List

import pandas as pd
import streamlit as st


# -------------------------------------------------------------------
#  Local regime + severity helpers (avoid cross-module import)
# -------------------------------------------------------------------

REGIME_LABELS = {
    "DSA": "EU Digital Services Act (DSA)",
    "DMA": "EU Digital Markets Act (DMA)",
    "EU_AI_ACT_ISO_42001": "EU AI Act / ISO 42001",
    "GDPR": "EU General Data Protection Regulation (GDPR)",
    "NIST_AI_RMF": "NIST AI Risk Management Framework",
}

SEVERITY_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def _severity_emoji(sev: str | None) -> str:
    s = (sev or "").upper()
    return {
        "LOW": "🟢",
        "MEDIUM": "🟡",
        "HIGH": "🟠",
        "CRITICAL": "🔴",
    }.get(s, "⚪")


def _decision_emoji(decision: str | None) -> str:
    d = (decision or "").upper()
    if d == "ALLOW":
        return "🟢 ALLOW"
    if d == "DENY":
        return "⛔ DENY"
    if d == "REQUIRE_HUMAN":
        return "👁️ REQUIRE_HUMAN"
    return f"⚪ {d or 'N/A'}"


def _bool_emoji(flag: Any, true_label: str, false_label: str) -> str:
    v = bool(flag)
    if v:
        return f"🟢 {true_label}"
    return f"⚪ {false_label}"


def _drift_emoji(outcome: str | None, score: Any | None = None) -> str:
    o = (outcome or "").upper()
    if o == "DRIFT_ALERT":
        if score is not None:
            return f"⚠️ DRIFT_ALERT (score: {score})"
        return "⚠️ DRIFT_ALERT"
    if o in {"NO_DRIFT", "", "NONE"}:
        if score is not None:
            return f"🟦 NO_DRIFT (score: {score})"
        return "🟦 NO_DRIFT"
    return f"ℹ️ {o}"


def _sev_cell(sev: str | None) -> str:
    """Inline severity badge: emoji + text."""
    label = (sev or "UNKNOWN").upper()
    return f"{_severity_emoji(label)} {label}"


def _count_cell(n: Any, kind: str) -> str:
    """Counts with emojis, per kind: violated / satisfied / na / total."""
    try:
        v = int(n or 0)
    except (TypeError, ValueError):
        v = 0

    if kind == "violated":
        return f"⛔ {v}"
    if kind == "satisfied":
        return f"🟢 {v}"
    if kind == "na":
        return f"⚪ {v}"
    # total
    return f"{v}"


# -------------------------------------------------------------------
#  Regime summary builder (simple, local)
# -------------------------------------------------------------------

def _normalise_severity(raw: Any) -> str:
    num_map = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}

    if isinstance(raw, (int, float)):
        return num_map.get(int(raw), "LOW")

    if isinstance(raw, str):
        s = raw.strip().upper()
        if not s:
            return "LOW"
        if s.isdigit():
            return num_map.get(int(s), "LOW")
        if s in SEVERITY_ORDER:
            return s
        return "LOW"

    return "LOW"


def _regime_key_from_policy(p: Dict[str, Any]) -> str:
    regime = (p.get("regime") or p.get("domain") or "").upper()

    if "DSA" in regime:
        return "DSA"
    if "DMA" in regime:
        return "DMA"
    if "GDPR" in regime:
        return "GDPR"
    if "NIST" in regime:
        return "NIST_AI_RMF"
    if "AI ACT" in regime or "ISO 42001" in regime:
        return "EU_AI_ACT_ISO_42001"

    return "DSA"


def _build_regime_summary(policies: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    summary: Dict[str, Dict[str, Any]] = {
        key: {
            "regime_key": key,
            "regime_label": REGIME_LABELS[key],
            "highest_severity": "LOW",
            "violated": 0,
            "satisfied": 0,
            "not_applicable": 0,
            "total_articles": 0,
        }
        for key in REGIME_LABELS.keys()
    }

    for p in policies:
        if not isinstance(p, dict):
            continue

        key = _regime_key_from_policy(p)
        s = summary[key]

        status = str(p.get("status", "")).upper() or "UNKNOWN"
        sev = _normalise_severity(
            p.get("severity")
            or p.get("severity_level")
            or p.get("severity_score")
            or p.get("criticality")
        )

        s["total_articles"] += 1

        if status == "VIOLATED":
            s["violated"] += 1
        elif status == "SATISFIED":
            s["satisfied"] += 1
        elif status == "NOT_APPLICABLE":
            s["not_applicable"] += 1

        # highest severity
        order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        if order.get(sev, 0) > order.get(s["highest_severity"], 0):
            s["highest_severity"] = sev

    return summary


# -------------------------------------------------------------------
#  Core comparison renderer
# -------------------------------------------------------------------

def _extract_policies(adra: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(adra, dict):
        return []
    l4 = adra.get("L4_policy_lineage_and_constitution", {}) or {}
    return l4.get("policies_triggered", []) or []


def block(adra: Dict[str, Any], label: str) -> None:
    """Render verdict, oversight & drift for a single ADRA."""
    l1 = adra.get("L1_the_verdict_and_constitutional_outcome", {}) or {}
    l6 = (
        adra.get("L6_behavioral_drift_and_monitoring")
        or adra.get("L6_drift_monitoring")
        or {}
    ) or {}
    l7 = adra.get("L7_veto_and_execution_feedback", {}) or {}

    decision = str(l1.get("decision_outcome") or l1.get("decision") or "N/A").upper()
    severity = str(l1.get("severity", "UNKNOWN")).upper()
    ts = l1.get("timestamp_utc") or l1.get("timestamp") or "N/A"

    human_oversight = l1.get("human_oversight_required", False)
    safe_state = l1.get("safe_state_triggered", False)
    veto = l7.get("veto_path_triggered") or l7.get("veto_triggered") or (
        decision == "DENY"
    )

    drift_outcome = l6.get("drift_outcome") or l6.get("drift_status") or "NO_DRIFT"
    drift_score = l6.get("drift_score")

    st.markdown(f"**{label}**")
    st.markdown(
        "<ul>"
        + "".join(
            f"<li>{item}</li>"
            for item in [
                f"Decision: {_decision_emoji(decision)}",
                f"Severity: {_sev_cell(severity)}",
                f"Timestamp (UTC): `{ts}`",
                _bool_emoji(
                    human_oversight,
                    "Human oversight required",
                    "Human oversight not required",
                ),
                _bool_emoji(
                    safe_state,
                    "Safe state triggered",
                    "Safe state not triggered",
                ),
                _bool_emoji(veto, "Veto path active", "Veto path not active"),
                f"Drift outcome: {_drift_emoji(drift_outcome, drift_score)}",
            ]
        )
        + "</ul>",
        unsafe_allow_html=True,
    )


def _build_regime_compare_df(
    adra_a: Dict[str, Any],
    adra_b: Dict[str, Any],
    label_a: str,
    label_b: str,
) -> pd.DataFrame:
    policies_a = _extract_policies(adra_a)
    policies_b = _extract_policies(adra_b)

    summary_a = _build_regime_summary(policies_a)
    summary_b = _build_regime_summary(policies_b)

    rows = []
    for key in REGIME_LABELS.keys():
        sa = summary_a.get(key) or {}
        sb = summary_b.get(key) or {}

        label = REGIME_LABELS[key]

        rows.append(
            {
                "Regime": label,
                f"{label_a} — Highest severity": _sev_cell(
                    sa.get("highest_severity", "LOW")
                ),
                f"{label_b} — Highest severity": _sev_cell(
                    sb.get("highest_severity", "LOW")
                ),
                f"{label_a} — Violated": _count_cell(sa.get("violated", 0), "violated"),
                f"{label_b} — Violated": _count_cell(sb.get("violated", 0), "violated"),
                f"{label_a} — Satisfied": _count_cell(
                    sa.get("satisfied", 0), "satisfied"
                ),
                f"{label_b} — Satisfied": _count_cell(
                    sb.get("satisfied", 0), "satisfied"
                ),
                f"{label_a} — Not applicable": _count_cell(
                    sa.get("not_applicable", 0), "na"
                ),
                f"{label_b} — Not applicable": _count_cell(
                    sb.get("not_applicable", 0), "na"
                ),
                f"{label_a} — Total articles": _count_cell(
                    sa.get("total_articles", 0), "total"
                ),
                f"{label_b} — Total articles": _count_cell(
                    sb.get("total_articles", 0), "total"
                ),
            }
        )

    df = pd.DataFrame(rows)
    return df


def render_adra_comparison(
    adra_a: Dict[str, Any],
    adra_b: Dict[str, Any],
    label_a: str = "ADRA A",
    label_b: str = "ADRA B",
) -> None:
    """
    Compare two ADRAs side-by-side, with emoji-rich view:

    1. verdict comparison (L1 + L6 + L7).
    2. Regime outcome comparison (L4 per regime), with inline severity badges.
    3. Raw ADRA objects for deep forensic diff.
    """
    if not isinstance(adra_a, dict) or not isinstance(adra_b, dict):
        st.error("Both ADRA objects must be valid dictionaries for comparison.")
        return

    st.subheader("🧬 Compare two ADRAs (forensic diff)")

    # 1) the-verdict comparison
    st.markdown("#### 1️⃣ the-verdict comparison (L1 + L6 + L7)")

    col_left, col_right = st.columns(2)
    with col_left:
        block(adra_a, label_a)
    with col_right:
        _block(adra_b, label_b)

    # 2) Regime outcome comparison
    st.markdown("#### 2️⃣ Regime outcome comparison (L4 → per regime)")

    df_compare = _build_regime_compare_df(adra_a, adra_b, label_a, label_b)

    st.dataframe(
        df_compare,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "This grid shows how each regime (DSA, DMA, GDPR, NIST AI RMF, "
        "EU AI Act / ISO 42001) presents differently between the two ADRAs, "
        "in terms of highest severity and article counts."
    )

    # 3) Raw ADRA objects
    st.markdown("#### 3️⃣ Raw ADRA objects (for deep forensic diff)")

    col_a, col_b = st.columns(2)
    with col_a:
        with st.expander(f"{label_a} — full ADRA (L0–L7)", expanded=False):
            st.json(adra_a)
    with col_b:
        with st.expander(f"{label_b} — full ADRA (L0–L7)", expanded=False):
            st.json(adra_b)
