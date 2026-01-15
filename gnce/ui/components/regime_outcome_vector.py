# ui/components/regime_outcome_vector.py
from __future__ import annotations

from typing import Any, Dict, List
import streamlit as st
import pandas as pd

from gnce.ui.components.l4_regimes import render_l4_regimes
from gnce.gn_kernel.regimes.register import REGIME_REGISTRY, init_registry

def _is_live_wired(regime_id: str) -> bool:
    """Return True when a regime is truly wired (has callable applicability+resolver and is marked executable)."""
    try:
        spec = REGIME_REGISTRY.get(regime_id) or {}
        # If not registered but appears in policies, treat as live evidence (not a stub surface).
        if not spec:
            return True
        if not spec.get('l4_executable', False):
            return False
        return callable(spec.get('applicability')) and callable(spec.get('resolver'))
    except Exception:
        return False



# -------------------------------------------------------------------
#  Severity & regime configuration
# -------------------------------------------------------------------

SEVERITY_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
SEVERITY_RANK = {s: i for i, s in enumerate(SEVERITY_ORDER, start=1)}

# Regimes we want to show (even if only as neutral / stub)
REGIME_LABELS = {
    "DSA": "EU Digital Services Act (DSA)",
    "DMA": "EU Digital Markets Act (DMA)",
    "EU_AI_ACT": "EU AI Act (Regulation)",
    "ISO_42001": "ISO/IEC 42001 (Governance Standard)",
    "GDPR": "EU General Data Protection Regulation (GDPR)",
    "NIST_AI_RMF": "NIST AI Risk Management Framework",
    "UNKNOWN": "Unknown / Unmapped regime",
    "PCI_DSS": "PCI DSS (Payment Card Industry Data Security Standard)",

}

JURIS_OPTIONS = ["AUTO", "ALL", "EU", "US", "US-NY", "GLOBAL"]


def _normalize_juris(j: Any) -> str:
    return str(j or "").strip().upper()


def _effective_jurisdiction(adra: Dict[str, Any], choice: str) -> str:
    choice = _normalize_juris(choice)
    if choice and choice != "AUTO":
        return choice

    # AUTO: try to infer from ADRA
    meta = adra.get("meta", {}) or {}
    inferred = meta.get("jurisdiction") or adra.get("jurisdiction")
    return _normalize_juris(inferred) or "ALL"


def _juris_ok(reg_j: str, selected: str) -> bool:
    reg_j = _normalize_juris(reg_j)
    selected = _normalize_juris(selected)

    if selected in {"ALL", ""}:
        return True

    # GLOBAL regimes are always shown alongside any specific jurisdiction
    if reg_j == "GLOBAL":
        return True

    if selected == "GLOBAL":
        return reg_j == "GLOBAL"

    # US includes US-* (e.g., US-NY)
    if selected == "US":
        return reg_j == "US" or reg_j.startswith("US-")

    # EU includes EU-* (if you ever add EU-DE etc.)
    if selected == "EU":
        return reg_j == "EU" or reg_j.startswith("EU-")

    # Exact match (e.g., US-NY)
    return reg_j == selected


# -------------------------------------------------------------------
#  Helper mappers
# -------------------------------------------------------------------

def _normalise_severity(raw: Any) -> str:
    """Normalise arbitrary severity representation into LOW/MEDIUM/HIGH/CRITICAL."""
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
    """
    Map a policy record to one of our canonical regime keys.
    """
    regime = (p.get("regime") or p.get("domain") or "").upper()

    if "DSA" in regime:
        return "DSA"
    if "DMA" in regime:
        return "DMA"
    if "GDPR" in regime:
        return "GDPR"
    if "NIST" in regime:
        return "NIST_AI_RMF"
    if "ISO" in regime and "42001" in regime:
        return "ISO_42001"

    if "AI ACT" in regime or "EU_AI_ACT" in regime:
        return "EU_AI_ACT"
    if "PCI" in regime and "DSS" in regime:
        return "PCI_DSS"


    # Fallback – unmapped regimes
    return "UNKNOWN"

def _impact_emoji(code: str) -> str:
    """Emoji per impact posture."""
    return {
        "CONSTITUTIONAL_BREACH": "🔥", # hard breach
        "NON_BLOCKING_BREACH": "⚠️",   # soft breach
        "IN_SCOPE_SATISFIED": "🟢",    # in-scope & satisfied
        "NEUTRAL_STUB_ONLY": "⚪",     # neutral stub surface
        "NOT_RUN": "🟣",  # ✅ registered but not applicable / not evaluated
    }.get(code, "⚪")



def _severity_emoji(sev: str) -> str:
    """Emoji for severity band."""
    sev = (sev or "").upper()
    return {
        "LOW": "🟢",
        "MEDIUM": "🟡",
        "HIGH": "🟠",
        "CRITICAL": "🔴",
    }.get(sev, "⚪")


def _stub_emoji(is_stub: bool) -> str:
    """Emoji + label for stub/live-wired distinction."""
    return "⚪ Stub surface" if is_stub else "🔗 Live-wired"


# -------------------------------------------------------------------
#  Regime summarisation
# -------------------------------------------------------------------

def _build_regime_summary(policies: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Group L4 policies per regime and derive impact, severity, counts.
    """
    # Initialise all regimes so they always appear
    summary: Dict[str, Dict[str, Any]] = {
        key: {
            "regime_key": key,
            "regime_label": REGIME_LABELS[key],
            "highest_severity": "LOW",
            "violated": 0,
            "satisfied": 0,
            "not_applicable": 0,
            "total_articles": 0,
            "stub_only": True,       # flipped to False once we see SATISFIED/VIOLATED
            "impact_code": "NEUTRAL_STUB_ONLY",
            "impact_label": "NEUTRAL",
            "registry_only": False,

        }
        for key in REGIME_LABELS.keys()
    }

    for p in policies:
        if not isinstance(p, dict):
            continue

        key = _regime_key_from_policy(p)
        s = summary[key]

        status = str(p.get("status", "")).upper() or "UNKNOWN"
        sev_raw = (
            p.get("severity")
            or p.get("severity_level")
            or p.get("severity_score")
            or p.get("criticality")
        )
        sev = _normalise_severity(sev_raw)
        sev_rank = SEVERITY_RANK.get(sev, 0)

        s["total_articles"] += 1

        if status == "VIOLATED":
            s["violated"] += 1
            s["stub_only"] = False
        elif status == "SATISFIED":
            s["satisfied"] += 1
            s["stub_only"] = False
        elif status == "NOT_APPLICABLE":
            s["not_applicable"] += 1

        current_rank = SEVERITY_RANK.get(s["highest_severity"], 0)
        if sev_rank > current_rank:
            s["highest_severity"] = sev

    # Derive impact per regime
    for key, s in summary.items():
        violated = s["violated"]
        satisfied = s["satisfied"]
        live_wired = _is_live_wired(key)
        all_na = (s["total_articles"] > 0 and violated == 0 and satisfied == 0 and s["not_applicable"] == s["total_articles"])
        stub_only = (not live_wired) and all_na
        s["stub_only"] = stub_only
        highest_sev = s["highest_severity"]

        impact_code = "NEUTRAL_STUB_ONLY" if stub_only else "NOT_RUN"
        impact_label = "NEUTRAL"

        if violated > 0:
            if highest_sev in {"HIGH", "CRITICAL"}:
                impact_code = "CONSTITUTIONAL_BREACH"
                impact_label = "BREACH"
            else:
                impact_code = "NON_BLOCKING_BREACH"
                impact_label = "ATTENTION"
        elif satisfied > 0:
            impact_code = "IN_SCOPE_SATISFIED"
            impact_label = "IN SCOPE"
        else:
            impact_code = "NEUTRAL_STUB_ONLY"
            impact_label = "NEUTRAL"

        s["impact_code"] = impact_code
        s["impact_label"] = impact_label

    return summary


def _impact_badge(impact_code: str, impact_label: str) -> str:
    """HTML pill for the per-regime cards."""
    if impact_code == "CONSTITUTIONAL_BREACH":
        color = "#ef4444"  # red
    elif impact_code == "NON_BLOCKING_BREACH":
        color = "#eab308"  # amber
    elif impact_code == "IN_SCOPE_SATISFIED":
        color = "#22c55e"  # green
    else:
        color = "#64748b"  # neutral

    return f"""
<span style="
  display:inline-flex;
  align-items:center;
  padding:0.18rem 0.7rem;
  border-radius:999px;
  border:1px solid rgba(148,163,184,0.6);
  background:rgba(15,23,42,0.9);
  font-size:0.78rem;
">
  <span style="width:0.45rem;height:0.45rem;border-radius:999px;background:{color};margin-right:0.35rem;"></span>
  <strong style="letter-spacing:0.03em;text-transform:uppercase;color:{color};">{impact_label}</strong>
</span>
"""


# -------------------------------------------------------------------
#  Main renderer
# -------------------------------------------------------------------

def render_regime_outcome_vector(adra: Dict[str, Any]) -> None:
    """
    🧭 Regime Outcome Vector (this ADRA)

    GNCE-style view of how this ADRA resolves per regime:
      - Which regimes are constitutionally breached, attention, in-scope, or neutral stubs.
      - Highest severity and article counts per regime.
    """
    init_registry()

    if not isinstance(adra, dict):
        st.warning("No valid ADRA loaded for regime view.")
        return

    l4 = adra.get("L4_policy_lineage_and_constitution", {}) or {}
    policies = l4.get("policies_triggered", []) or []

    # Ensure registry is loaded
    init_registry()

    # -------- Jurisdiction filter UI --------
    choice = st.selectbox(
        "Jurisdiction filter",
        JURIS_OPTIONS,
        index=0,
        help="Filters the regime overview and posture cards. AUTO uses ADRA meta.jurisdiction if present."
    )
    selected_juris = _effective_jurisdiction(adra, choice)

    # Build allowed regime set from registry metadata
    allowed_regimes = set()
    for rid, spec in (REGIME_REGISTRY or {}).items():
        if _juris_ok(spec.get("jurisdiction"), selected_juris):
            allowed_regimes.add(rid)

    # Filter policies down to allowed regimes (keep UNKNOWN always)
    filtered_policies = []
    for p in (policies or []):
        if not isinstance(p, dict):
            continue
        rk = _regime_key_from_policy(p)
        if rk == "UNKNOWN" or rk in allowed_regimes:
            filtered_policies.append(p)

    policies = filtered_policies
    regime_summary = _build_regime_summary(policies)

    show_all_registered = st.toggle(
        "Include all registered regimes (even if not triggered)",
        value=False,
        help="NOT RUN = Registered in GNCE but not applicable to this ADRA input. NEUTRAL = Evaluated but only NOT_APPLICABLE items."

    )

    if show_all_registered:
        for rid, spec in (REGIME_REGISTRY or {}).items():
            if rid not in allowed_regimes:
                continue
            if rid not in regime_summary:
                regime_summary[rid] = {
                    "regime_key": rid,
                    "regime_label": spec.get("display_name", rid),
                    "highest_severity": "LOW",
                    "violated": 0,
                    "satisfied": 0,
                    "not_applicable": 0,
                    "total_articles": 0,
                    "stub_only": True,
                    "impact_code": "NOT_RUN",
                    "impact_label": "NOT RUN",
                }

    # ✅ ALWAYS build rows/df (regardless of toggle)
    rows = list(regime_summary.values())
    df = pd.DataFrame(rows)


    st.markdown("### 🧭 Regime Outcome Vector")
    st.caption(
        "How this ADRA resolves per regulatory regime under the GNCE constitution. "
        "DSA is live-wired to this ADRA; DMA, EU AI Act, ISO/IEC 42001, GDPR and NIST AI RMF "

        "inherit the GN verdict as in-scope or neutral regimes."
    )

    if df.empty:
        st.info("No L4 policies available to build a regime outcome vector.")
        return

    # ---------- Header chips: quick posture snapshot ----------
    breach_count = sum(1 for r in rows if r["impact_code"] == "CONSTITUTIONAL_BREACH")
    attention_count = sum(1 for r in rows if r["impact_code"] == "NON_BLOCKING_BREACH")
    in_scope_count = sum(1 for r in rows if r["impact_code"] == "IN_SCOPE_SATISFIED")
    neutral_count = sum(1 for r in rows if r["impact_code"] == "NEUTRAL_STUB_ONLY")

    chip_html = f"""
<div style="display:flex;flex-wrap:wrap;gap:0.4rem;margin-bottom:0.4rem;">
  <span style="
      padding:0.15rem 0.7rem;
      border-radius:999px;
      background:rgba(30,64,175,0.25);
      border:1px solid rgba(129,140,248,0.7);
      font-size:0.78rem;
  ">
    <strong>{breach_count}</strong> regime(s) in <span style="color:#ef4444;">constitutional breach</span>
  </span>
  <span style="
      padding:0.15rem 0.7rem;
      border-radius:999px;
      background:rgba(120,53,15,0.25);
      border:1px solid rgba(251,191,36,0.7);
      font-size:0.78rem;
  ">
    <strong>{attention_count}</strong> regime(s) need <span style="color:#eab308;">attention</span>
  </span>
  <span style="
      padding:0.15rem 0.7rem;
      border-radius:999px;
      background:rgba(22,101,52,0.25);
      border:1px solid rgba(74,222,128,0.7);
      font-size:0.78rem;
  ">
    <strong>{in_scope_count}</strong> regime(s) are <span style="color:#22c55e;">in scope &amp; satisfied</span>
  </span>
  <span style="
      padding:0.15rem 0.7rem;
      border-radius:999px;
      background:rgba(15,23,42,0.7);
      border:1px solid rgba(148,163,184,0.6);
      font-size:0.78rem;
  ">
    <strong>{neutral_count}</strong> regime(s) are neutral stubs only
  </span>
</div>
"""
    st.markdown(chip_html, unsafe_allow_html=True)

    # ---------- Overview table (bold GNCE style) ----------
    overview_df = df[
        [
            "regime_label",
            "impact_code",
            "impact_label",
            "highest_severity",
            "violated",
            "satisfied",
            "not_applicable",
            "total_articles",
            "stub_only",
        ]
    ].copy()

    # Emoji + text posture
    overview_df["Posture"] = overview_df.apply(
        lambda r: f"{_impact_emoji(r['impact_code'])} {r['impact_label']}",
        axis=1,
    )

    # Emoji severity band
    overview_df["Highest severity"] = overview_df["highest_severity"].apply(
        lambda s: f"{_severity_emoji(s)} {s}"
    )

    # Stub vs live-wired surface
    overview_df["Neutral stub only"] = overview_df["stub_only"].apply(_stub_emoji)

    # Rename + select final display columns
    overview_df = overview_df.rename(
        columns={
            "regime_label": "Regime",
            "violated": "Violated",
            "satisfied": "Satisfied",
            "not_applicable": "Not applicable",
            "total_articles": "Total articles",
        }
    )[
        [
            "Regime",
            "Posture",             # 🔥/⚠️/🟢/⚪ + label
            "Highest severity",    # 🟢 LOW, 🔴 CRITICAL, etc.
            "Violated",
            "Satisfied",
            "Not applicable",
            "Total articles",
            "Neutral stub only",   # ⚪ Stub surface / 🔗 Live-wired
        ]
    ]

    # Sort in canonical GN order
    order_labels = [REGIME_LABELS[k] for k in REGIME_LABELS.keys()]
    overview_df["__order"] = overview_df["Regime"].apply(
        lambda x: order_labels.index(x) if x in order_labels else len(order_labels)
    )
    overview_df = overview_df.sort_values("__order").drop(columns="__order")


    st.markdown("#### Overview grid")

    column_config = {
        "Posture": st.column_config.TextColumn(
            "Posture",
            help="NOT RUN = Registered in GNCE but not applicable to this ADRA input. "
                "NEUTRAL = Evaluated but only NOT_APPLICABLE items.",
        ),
        
        "Neutral stub only": st.column_config.TextColumn(
            "Neutral stub only",
            help="Stub surface = regime present as a constitutional hook, but not driving this ADRA’s verdict.",
        ),
    }

    if show_all_registered:
        registry_only_df = overview_df[overview_df["Posture"].str.contains("NOT RUN")].copy()
        primary_df = overview_df[~overview_df["Posture"].str.contains("NOT RUN")].copy()

        st.dataframe(primary_df, use_container_width=True, hide_index=True, column_config=column_config)

        with st.expander("Registry-only regimes (registered, not applicable to this ADRA)", expanded=False):
            st.dataframe(registry_only_df, use_container_width=True, hide_index=True, column_config=column_config)
    else:
        st.dataframe(overview_df, use_container_width=True, hide_index=True, column_config=column_config)


    # ---------- Per-regime posture cards ----------
    st.markdown("#### Per-regime constitutional posture")     

    impact_explanations = {
        "CONSTITUTIONAL_BREACH": (
            "Constitutional breach for this regime under the current ADRA. "
            "At least one HIGH/CRITICAL article is violated and contributes to a DENY verdict."
        ),
        "NON_BLOCKING_BREACH": (
            "Policy breach detected in this regime (LOW/MEDIUM severity). "
            "Does not alone block execution but should feed back into policy refinement."
        ),
        "IN_SCOPE_SATISFIED": (
            "Regime is in-scope and satisfied for this ADRA. No violated articles were found."
        ),
        "NEUTRAL_STUB_ONLY": (
            "Regime is present as a neutral / stub surface only (NOT_APPLICABLE articles). "
            "It does not influence this ADRA’s verdict, but the constitutional hooks exist."
        ),
    }

    session_ledger = st.session_state.get("gn_ledger", []) or []
    total_session_adras = len(session_ledger)

    # Show cards for whatever is in the regime_summary (canonical + registry-added)
    regime_keys_in_order = list(REGIME_LABELS.keys()) + [
    k for k in regime_summary.keys() if k not in REGIME_LABELS
]
    for i in range(0, len(regime_keys_in_order), 2):
        cols = st.columns(2)
        for idx, col in enumerate(cols):
            if i + idx >= len(regime_keys_in_order):
                continue
            key = regime_keys_in_order[i + idx]
            s = regime_summary[key]

            with col:
                impact_code = s["impact_code"]
                impact_label = s["impact_label"]
                highest_sev = s["highest_severity"]
                violated = s["violated"]
                satisfied = s["satisfied"]
                na = s["not_applicable"]
                total = s["total_articles"]
                stub_only = s["stub_only"]
                label = s["regime_label"]

                # Left border colour per impact
                if impact_code == "CONSTITUTIONAL_BREACH":
                    border_color = "#ef4444"
                elif impact_code == "NON_BLOCKING_BREACH":
                    border_color = "#eab308"
                elif impact_code == "IN_SCOPE_SATISFIED":
                    border_color = "#22c55e"
                else:
                    border_color = "#475569"

                if stub_only:
                    stub_text = (
                        "<br/><span style='font-size:0.74rem;opacity:0.8;'>"
                        "Present as neutral/stub only; does not drive the verdict in this ADRA."
                        "</span>"
                    )
                else:
                    stub_text = ""

                card_html = f"""
<div style="
  border-radius:0.9rem;
  border:1px solid rgba(51,65,85,0.9);
  background:radial-gradient(circle at top left,rgba(30,64,175,0.18),rgba(15,23,42,0.95));
  padding:0.85rem 0.95rem;
  box-shadow:0 8px 24px rgba(15,23,42,0.65);
  position:relative;
">
  <div style="
      position:absolute;
      left:-1px;
      top:0;
      bottom:0;
      width:4px;
      border-radius:0.9rem 0 0 0.9rem;
      background:{border_color};
  "></div>

  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.5rem;">
    <div>
      <div style="font-size:0.9rem;font-weight:600;margin-bottom:0.15rem;">{label}</div>
      <div style="font-size:0.75rem;opacity:0.85;">
        Highest severity: <strong>{highest_sev}</strong><br/>
        Articles: <strong>{total}</strong> total · <strong>{violated}</strong> violated ·
        <strong>{satisfied}</strong> satisfied · <strong>{na}</strong> N/A
      </div>
    </div>
    <div>{_impact_badge(impact_code, impact_label)}</div>
  </div>

  <div style="margin-top:0.45rem;font-size:0.8rem;opacity:0.92;">
    {impact_explanations.get(impact_code, "")}{stub_text}
  </div>
</div>
"""
                st.markdown(card_html, unsafe_allow_html=True)

    if total_session_adras:
        st.caption(
            f"This view is ADRA-scoped. Session context: {total_session_adras} ADRAs evaluated."
        )

  