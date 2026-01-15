# ui/components/decision_summary.py
from __future__ import annotations

from typing import Any, Dict

import streamlit as st
from .sovereign_loop_panel import render_sovereign_loop_panel
from .severity_legend import render_severity_legend


SEVERITY_COLORS = {
    "LOW": "#00916E",        # green
    "MEDIUM": "#ffb300",     # amber
    "HIGH": "#C62828",       # red
    "CRITICAL": "#8b008b",   # purple
    "UNKNOWN": "#64748b",    # slate/neutral
}


def format_severity_badge(sev: str | None) -> str:
    """
    Return a small HTML badge for a severity string.
    Used both in Decision Summary and other components.
    """
    label = (sev or "UNKNOWN").upper()
    color = SEVERITY_COLORS.get(label, SEVERITY_COLORS["UNKNOWN"])

    return (
        f'<span style="'
        f'display:inline-flex;'
        f'align-items:center;'
        f'padding:0.12rem 0.6rem;'
        f'border-radius:999px;'
        f'font-size:0.78rem;'
        f'font-weight:600;'
        f'letter-spacing:0.03em;'
        f'text-transform:uppercase;'
        f'background:rgba(15,23,42,0.85);'
        f'border:1px solid rgba(148,163,184,0.45);'
        f'color:{color};'
        f'">'
        f'●&nbsp;{label}'
        f"</span>"
    )


def _loop_badge(label: str, tone: str, kind: str | None = None) -> str:
    """
    Tiny governance-loop pill (HTML string).

    tone ∈ {"active", "passive", "neutral"}.
    kind ∈ {"veto", "dda", "sovereign", None} and drives the tooltip text.
    """
    if tone == "active":
        bg = "rgba(34,197,94,0.25)"      # BRIGHTER green background
        border = "rgba(34,197,94,0.8)"   # BRIGHTER green border
        dot = "#45a467"                   # Bright green dot
    elif tone == "passive":
        bg = "rgba(239,68,68,0.2)"       # red-ish
        border = "rgba(239,68,68,0.8)"
        dot = "#ba1f1f"
    else:
        bg = "rgba(148,163,184,0.12)"    # neutral
        border = "rgba(148,163,184,0.6)"
        dot = "#94a3b8"

    # Tooltip / classification text per loop kind
    if kind == "veto":
        tooltip = (
            "Synchronous runtime constitutional loop "
            "(blocking, pre-execution)."
        )
    elif kind == "dda":
        tooltip = (
            "Asynchronous drift loop "
            "(non-blocking, post-execution)."
        )
    elif kind == "sovereign":
        tooltip = (
            "Constitutional Governance Path – human/regulatory oversight loop "
            "that updates GNCE's core governance model and constitutional design."
        )
    else:
        tooltip = ""

    title_attr = (
        f'title="{tooltip}" aria-label="{tooltip}" '
        if tooltip
        else ""
    )

    return (
        f'<span {title_attr}'
        f'style="'
        f'display:inline-flex;'
        f'align-items:center;'
        f'gap:0.35rem;'
        f'padding:0.15rem 0.65rem;'
        f'border-radius:999px;'
        f'font-size:0.75rem;'
        f'font-weight:600;'
        f'border:2px solid {border};'  # Thicker border
        f'background:{bg};'
        f'white-space:nowrap;'
        f'margin-right:0.35rem;'
        f'margin-bottom:0.35rem;'
        f'">'
        f'<span style="width:0.5rem;height:0.5rem;'
        f'border-radius:999px;background:{dot};'
        f'box-shadow:0 0 8px {dot};"></span>'  # Glowing dot
        f'&nbsp;{label}'
        f"</span>"
    )

def _drift_only_badge() -> str:
    """
    Special tiny badge for 'pure drift' scenarios:
    decision == ALLOW and drift_outcome == DRIFT_ALERT.
    """
    return (
        '<span style="'
        'display:inline-flex;'
        'align-items:center;'
        'padding:0.10rem 0.55rem;'
        'border-radius:999px;'
        'font-size:0.72rem;'
        'font-weight:600;'
        'text-transform:uppercase;'
        'letter-spacing:0.03em;'
        'background:rgba(30,64,175,0.75);'
        'border:1px solid rgba(129,140,248,0.9);'
        'color:#e0e7ff;'
        'margin-left:0.35rem;'
        '">'
        '⚠️ DRIFT-ONLY SCENARIO'
        '</span>'
    )


def _render_cet_panel(l5: Dict[str, Any]) -> None:
    """
    Render the Cryptographic Evidence Token (CET v0.4) panel (L5).
    """
    if not l5:
        return

    content_hash = l5.get("content_hash_sha256")
    nonce = l5.get("nonce")
    pseudo_sig = l5.get("pseudo_signature_sha256")
    strategy = l5.get("signing_strategy", "GNCE_v0.4_pseudo_signature")

    if not (content_hash or nonce or pseudo_sig):
        # Nothing meaningful to show
        return

    st.markdown("---")
    st.markdown("**🔐 Cryptographic Evidence Token (CET v0.4)**")

    st.markdown(
        f"""
<div style="border-radius:0.9rem;
            border:1px solid rgba(129,140,248,0.6);
            background:radial-gradient(circle at top left,
                       rgba(79,70,229,0.18),rgba(15,23,42,0.95));
            padding:0.85rem 0.95rem;
            box-shadow:0 10px 28px rgba(15,23,42,0.75);
            font-size:0.82rem;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.75rem;">
    <div style="max-width:70%;">
      <div style="font-size:0.9rem;font-weight:600;margin-bottom:0.25rem;">
        CET v0.4 — Immutable decision evidence for this ADRA.
      </div>
      <p style="margin:0 0 0.35rem 0;opacity:0.9;line-height:1.45;">
        GNCE seals the constitutional substrate of this decision (L1 verdict,
        rule trace and policy lineage) into a <strong>Cryptographic Evidence Token (CET)</strong>.
        The CET can be verified independently by regulators, auditors or counterparties.
      </p>
    </div>
    <div style="text-align:right;">
      <span style="display:inline-flex;align-items:center;
                   padding:0.10rem 0.6rem;border-radius:999px;
                   border:1px solid rgba(129,140,248,0.8);
                   background:rgba(30,64,175,0.35);
                   font-size:0.72rem;color:#e0e7ff;">
        🔏 Signing strategy:&nbsp;<strong>{strategy}</strong>
      </span>
    </div>
  </div>
""",
        unsafe_allow_html=True,
    )

    rows = []
    if content_hash:
        rows.append(("Content hash (L1+L3+L4)", content_hash))
    if nonce:
        rows.append(("Nonce (replay guard)", nonce))
    if pseudo_sig:
        rows.append(("Pseudo-signature (SHA-256)", pseudo_sig))

    if rows:
        html_rows = "".join(
            f"<tr>"
            f"<td style='padding:0.18rem 0.4rem;font-weight:500;white-space:nowrap;"
            f"vertical-align:top;'>• {label}</td>"
            f"<td style='padding:0.18rem 0.4rem;font-family:monospace;"
            f"font-size:0.78rem;word-break:break-all;opacity:0.9;'>{value}</td>"
            f"</tr>"
            for label, value in rows
        )

        st.markdown(
            "<table style='width:100%;margin-top:0.35rem;border-spacing:0;'>"
            f"{html_rows}"
            "</table>"
            "</div>",  # closes outer CET card div
            unsafe_allow_html=True,
        )


def _render_veto_artifact_panel(l7: Dict[str, Any], veto_triggered: bool) -> None:
    """
    Render the Constitutional Veto Artifact (L7) panel.
    """
    st.markdown("---")
    st.markdown("**⛔ Constitutional Veto Artifact (L7)**")

    if not l7 or not veto_triggered:
        st.markdown(
            "<p style='font-size:0.85rem;opacity:0.9;'>"
            "No constitutional veto was raised for this ADRA. "
            "Execution is eligible under the current GNCE constitution, "
            "subject to external system-level checks."
            "</p>",
            unsafe_allow_html=True,
        )
        return

    veto_category = l7.get("veto_category", "CONSTITUTIONAL_BLOCK")
    escalation = l7.get("escalation_required", "HUMAN_REVIEWER")
    citation = l7.get("constitutional_citation", "")
    basis = l7.get("veto_basis") or []
    artifact_hash = l7.get("veto_artifact_hash_sha256")

    # Header pill
    if veto_category == "CONSTITUTIONAL_BLOCK":
        cat_label = "Constitutional block"
        cat_color = "#ef4444"
        cat_bg = "rgba(239,68,68,0.18)"
        cat_border = "rgba(239,68,68,0.6)"
    else:
        cat_label = veto_category.replace("_", " ").title()
        cat_color = "#eab308"
        cat_bg = "rgba(234,179,8,0.18)"
        cat_border = "rgba(234,179,8,0.6)"

    header_html = f"""
<div style="border-radius:0.9rem;
            border:1px solid rgba(71,85,105,0.9);
            background:radial-gradient(circle at top left,
                       rgba(127,29,29,0.20),rgba(15,23,42,0.96));
            padding:0.85rem 0.95rem;
            box-shadow:0 10px 28px rgba(15,23,42,0.75);
            font-size:0.82rem;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.75rem;">
    <div style="max-width:70%;">
      <div style="font-size:0.9rem;font-weight:600;margin-bottom:0.25rem;">
        A constitutional veto prevented execution of this ADRA.
      </div>
      <p style="margin:0 0 0.35rem 0;opacity:0.9;line-height:1.45;">
        GNCE generated a <strong>Veto Artifact</strong> explaining which governing articles were violated,
        how they map to the GNCE constitution, and which escalation path is required.
      </p>
    </div>
    <div style="text-align:right;display:flex;flex-direction:column;gap:0.3rem;align-items:flex-end;">
      <span style="display:inline-flex;align-items:center;
                   padding:0.10rem 0.6rem;border-radius:999px;
                   border:1px solid {cat_border};
                   background:{cat_bg};
                   font-size:0.72rem;color:{cat_color};">
        ⛔&nbsp;<strong>{cat_label}</strong>
      </span>
      <span style="display:inline-flex;align-items:center;
                   padding:0.10rem 0.6rem;border-radius:999px;
                   border:1px solid rgba(248,250,252,0.25);
                   background:rgba(15,23,42,0.85);
                   font-size:0.72rem;color:#e5e7eb;">
        👤 Escalation: <strong style="margin-left:0.25rem;">{escalation}</strong>
      </span>
    </div>
  </div>
"""
    st.markdown(header_html, unsafe_allow_html=True)

    # Constitutional citation
    if citation:
        st.markdown(
            "<div style='margin-top:0.35rem;font-size:0.82rem;opacity:0.95;'>"
            f"<strong>Constitutional citation:</strong><br/>{citation}"
            "</div>",
            unsafe_allow_html=True,
        )

    # Veto basis bullets
    if basis:
        items_html = ""
        for item in basis:
            art = item.get("article", "Unknown article")
            status = str(item.get("status", "VIOLATED")).upper()
            sev = str(item.get("severity", "UNKNOWN")).upper()
            clause = item.get("constitutional_clause", "")
            expl = item.get("explanation", "")

            badge = format_severity_badge(sev)

            items_html += (
                "<li style='margin-bottom:0.45rem;'>"
                f"<div style='font-size:0.83rem;font-weight:600;margin-bottom:0.05rem;'>"
                f"{art} — {status}</div>"
                f"<div style='margin-bottom:0.10rem;'>{badge}</div>"
                f"<div style='font-size:0.80rem;opacity:0.95;'>"
                f"{expl}</div>"
                f"<div style='font-size:0.78rem;opacity:0.8;margin-top:0.10rem;'>"
                f"<em>{clause}</em></div>"
                "</li>"
            )

        st.markdown(
            "<div style='margin-top:0.5rem;font-size:0.82rem;'>"
            "<strong>Veto basis (governing articles):</strong>"
            "<ul style='margin-top:0.25rem;padding-left:1.1rem;'>"
            f"{items_html}"
            "</ul>"
            "</div>",
            unsafe_allow_html=True,
        )

    # Artifact hash
    if artifact_hash:
        st.markdown(
            "<div style='margin-top:0.35rem;font-size:0.78rem;opacity:0.9;'>"
            f"<strong>Veto Artifact hash (SHA-256):</strong><br/>"
            f"<span style='font-family:monospace;'>{artifact_hash}</span>"
            "</div>"
            "</div>",  # closes main veto card div
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "</div>",  # close main veto card div when no hash section
            unsafe_allow_html=True,
        )


def render_decision_summary(adra: Dict[str, Any], key_prefix: str = "decision") -> None:
    """
    🧾 Decision Summary (L1 + L5 + L6 + L7)
    - Constitutional verdict (L1).
    - Oversight / safe state / veto flags.
    - Governance loops: Veto path, DDA, GNCE general constitutional values loop.
    - GNCE General Constitutional Values + Governance Context (owners & custodians).
    - Constitutional Veto Artifact (L7).
    - CET v0.4 evidence (L5).
    """
    if not isinstance(adra, dict):
        st.warning("ADRA is not a valid object.")
        return

    st.markdown("---")

    # ---------------- Decision Summary Header + Severity Bands ----------------
    render_severity_legend()
    st.markdown("---")

    # ---------------- Extract layers ----------------
    l1 = adra.get("L1_the_verdict_and_constitutional_outcome", {}) or {}
    l5 = adra.get("L5_integrity_and_tokenization", {}) or {}
    l6 = (
        adra.get("L6_behavioral_drift_and_monitoring")
        or adra.get("L6_drift_monitoring")
        or {}
    ) or {}
    l7 = adra.get("L7_veto_and_execution_feedback", {}) or {}

    decision = str(l1.get("decision_outcome") or l1.get("decision") or "N/A").upper()
    severity = str(l1.get("severity", "UNKNOWN")).upper()
    basis = l1.get("basis", "")

    human_oversight = bool(l1.get("human_oversight_required", False))
    safe_state = bool(l1.get("safe_state_triggered", False))

    veto_triggered = bool(
        l7.get("veto_path_triggered")
        or l7.get("veto_triggered")
    )
 
    drift_outcome_raw = str(l6.get("drift_outcome", "NO_DRIFT"))
    drift_outcome = drift_outcome_raw.upper()
    drift_score = l6.get("drift_score", 0)
    drift_human_rationale = l6.get("human_rationale") or ""

    # Pure drift = ALLOW + DRIFT_ALERT + no veto/safe-state
    is_pure_drift = (
        decision == "ALLOW"
        and drift_outcome == "DRIFT_ALERT"
        and not veto_triggered
        and not safe_state
    )

    # ---------------- Top line: decision + flags ----------------
    col1, col2 = st.columns([1.3, 1.7])

    with col1:
        st.markdown("**L1 the-Verdict**")

        severity_badge = format_severity_badge(severity)
        drift_badge = _drift_only_badge() if is_pure_drift else ""

        st.markdown(
            f"""
<div style="margin-top:0.25rem;display:flex;flex-direction:column;gap:0.25rem;">
  <div style="font-size:1.1rem;font-weight:600;">
    Decision: <span style="font-weight:700;">{decision}</span>
  </div>
  <div>{severity_badge}{drift_badge}</div>
</div>
""",
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown("**Execution & Oversight Flags**")

        flags: list[str] = []
        if human_oversight:
            flags.append("👁️ Human oversight **required (post-decision, outside runtime loop)**")
        else:
            flags.append("👁️ Human oversight **not required (GNCE verdict stands autonomously)**")

        if safe_state:
            flags.append("🛟 Safe state **triggered**")
        else:
            flags.append("🛟 Safe state **not triggered**")

        if veto_triggered:
            flags.append("⛔ Veto path **active** for this ADRA")
        else:
            flags.append("✅ No veto: action is eligible for execution")

        if drift_outcome == "DRIFT_ALERT":
            if is_pure_drift:
                flags.append(
                    f"📈 Drift outcome: **DRIFT_ALERT** (score: {drift_score}) — "
                    "drift-only scenario (ALLOW + DRIFT_ALERT; no veto / safe-state)."
                )
            else:
                flags.append(f"📈 Drift outcome: **DRIFT_ALERT** (score: {drift_score})")
        else:
            flags.append("📉 Drift outcome: **NO_DRIFT**")

        st.markdown(
            "<ul style='padding-left:1.1rem;margin-top:0.25rem;'>"
            + "".join(f"<li style='margin-bottom:0.1rem;'>{f}</li>" for f in flags)
            + "</ul>",
            unsafe_allow_html=True,
        )

    # =====================================================================
    # ✅ L1 Narrative Enrichment
    # =====================================================================
    hr = l1.get("human_readable_outcome")
    because = l1.get("because") or []
    regulator_summary = l1.get("regulator_summary")
    
    # Get original recommended actions
    original_recommended_actions = l1.get("recommended_actions") or []

    if hr or because or regulator_summary or original_recommended_actions:
        st.markdown("---")

    if hr:
        st.markdown(f"### 🧠 {hr}")

    if because:
        with st.expander("Why GNCE decided this", expanded=True):
            for b in because:
                st.markdown(f"- {b}")

    if regulator_summary:
        with st.expander("⚖️ Regulator Summary", expanded=False):
            st.write(regulator_summary)

    # =====================================================================
    # 🛠️ GNCE Architectural Recommendation Generation
    # Consistent with L0-L7 constitutional layers - NO CONTRADICTIONS
    # =====================================================================
    
    # Base recommendations that respect GNCE architecture
    recommended_actions = []
    
    # L1 Verdict-based recommendations (Constitutional Outcome)
    if decision == "ALLOW":
        recommended_actions.extend([
            "✅ L1 constitutional verdict: Action is constitutionally permissible",
            "✅ L2 ethical substrate: No ethical boundary violations detected",
            "✅ L3 constraint validation: All runtime constraints satisfied"
        ])
        
        # Additional ALLOW-specific recommendations
        if not veto_triggered and not human_oversight:
            recommended_actions.append("✅ Execution path: Proceed with autonomous execution")
            recommended_actions.append("✅ Governance: No corrective action required")
        elif human_oversight:
            recommended_actions.append("👁️ Governance: Human oversight required before execution")
            
    elif decision == "DENY":
        recommended_actions.extend([
            "⛔ L1 constitutional verdict: Action is constitutionally impermissible",
            "⛔ L3 constraint validation: One or more runtime constraints violated",
            "🔄 L7 corrective feedback: Refer to veto artifact for specific violations"
        ])
        
        # Additional DENY-specific recommendations
        recommended_actions.append("⛔ Execution gate: Action blocked from execution")
        recommended_actions.append("🔄 Remediation: Agent must re-plan based on corrective signal")
        recommended_actions.append("📋 Route to policy owner for constitutional review")
        recommended_actions.append("🔍 Collect evidence of policy violation")
        recommended_actions.append("🛠️ Implement mitigation based on corrective signal")
        recommended_actions.append("🔄 Re-run GNCE after mitigation actions are complete")
        
    else:  # OTHER/VETO/UNKNOWN
        recommended_actions.extend([
            "⚠️ L1 constitutional verdict: Requires constitutional interpretation",
            "👥 Sovereign governance: Route to constitutional governance committee",
            "📜 L0-L7 review: Complete constitutional layer analysis required"
        ])

    # L4 Policy Lineage recommendations
    violated_articles = adra.get("violated_articles") or []
    if violated_articles and decision == "DENY":
        recommended_actions.append(f"📋 L4 policy trace: {len(violated_articles)} article(s) violated - review policy lineage")
    elif decision == "ALLOW":
        recommended_actions.append("✅ L4 policy lineage: All applicable articles satisfied")

    # L5 CET recommendations
    if l5.get("content_hash_sha256"):
        recommended_actions.append("🔐 L5 CET: Cryptographic evidence token generated for audit")
    else:
        recommended_actions.append("⚠️ L5 CET: No cryptographic evidence token present")

    # L6 Drift recommendations
    if drift_outcome == "DRIFT_ALERT":
        recommended_actions.extend([
            f"📈 L6 drift detection: DRIFT_ALERT raised (score: {drift_score})",
            "🔄 DDA loop: Continuous Drift Detection Agent monitoring active"
        ])
    else:
        recommended_actions.append("✅ L6 drift detection: No behavioral drift detected")

    # L7 Veto recommendations
    if veto_triggered:
        recommended_actions.extend([
            "⛔ L7 veto path: Constitutional veto artifact generated",
            "🔄 Corrective signal: Agent must re-plan based on veto feedback",
            "📋 SARS ledger: Veto evidence recorded in sovereign audit trail"
        ])
    else:
        recommended_actions.append("✅ L7 execution feedback: No constitutional veto required")

    # Execution authorization recommendations
    exec_auth = l1.get("execution_authorized") or l7.get("execution_authorized")
    if exec_auth is True:
        recommended_actions.append("✅ Execution Gate: Action authorized for execution")
    elif exec_auth is False:
        recommended_actions.append("⛔ Execution Gate: Action blocked from execution")
        if decision == "ALLOW" and exec_auth is False:
            recommended_actions.append("⚠️ Constitutional paradox: L1 ALLOW but execution blocked - requires sovereign review")
    else:
        recommended_actions.append("⚠️ Execution Gate: Authorization status not explicitly set")

    # Safe state recommendations
    if safe_state:
        recommended_actions.extend([
            "🛡️ Safe state: Protective constitutional posture activated",
            "🔒 L0 foundational: Operating in reduced-risk constitutional mode"
        ])

    # Human oversight recommendations
    if human_oversight:
        recommended_actions.extend([
            "👁️ Human oversight: Constitutional review required before execution",
            "📋 Sovereign loop: Route to designated constitutional custodian"
        ])
    else:
        recommended_actions.append("✅ Autonomous execution: No human oversight required")

    # Display recommended actions with architectural context
    with st.expander("🛠️ Constitutional Recommendations", expanded=True):
        st.markdown("**GNCE Layer-by-Layer Analysis:**")
        
        # Show verdict summary
        verdict_summary = f"**L1 Verdict:** {decision} • **Severity:** {severity}"
        if veto_triggered:
            verdict_summary += " • **L7 Veto:** ⛔ Triggered"
        if drift_outcome == "DRIFT_ALERT":
            verdict_summary += f" • **L6 Drift:** 📈 Alert (score: {drift_score})"
            
        st.markdown(verdict_summary)
        st.markdown("---")
        
        # Display all recommendations
        for action in recommended_actions:
            st.markdown(f"- {action}")
        
        # Show note about original recommendations if they exist
        if original_recommended_actions:
            st.markdown("---")
            st.info(f"**Original L1 recommendations ({len(original_recommended_actions)}):**")
            for action in original_recommended_actions:
                st.markdown(f"  - {action}")

    # ---------------- Governance loops chips ----------------
    st.markdown("---")
    st.markdown("**Governance loops engaged for this ADRA**")

    # Always define before loop chips (prevents NameError)
    constitutional_invoked = bool(
        adra.get("constitutional_review_invoked")
        or adra.get("sovereign_governance_invoked")
        or adra.get("policy_change_commit_pending")
    )

    loops_html: list[str] = []

    # 1) Veto Feedback Path
    if veto_triggered:
        loops_html.append(_loop_badge("Veto Feedback Path (triggered)", "passive", kind="veto"))
    else:
        loops_html.append(_loop_badge("Veto Feedback Path (not triggered)", "neutral", kind="veto"))

    # 2) Continuous Drift Detection Agent (always active)
    if drift_outcome == "DRIFT_ALERT":
        loops_html.append(_loop_badge(f"🟢 Continuous Drift Detection Agent (drift detected, score: {drift_score})", "active", kind="dda"))
    else:
        loops_html.append(_loop_badge("🟡 Continuous Drift Detection Agent (monitoring)", "active", kind="dda"))

    # 3) 🏛 Constitutional Governance Path
    loops_html.append(
        _loop_badge(
            "🏛 Constitutional Governance Path",
            "active" if constitutional_invoked else "neutral",
            kind="sovereign",
        )
    )

    loops_container_html = (
        "<div style='display:flex;flex-wrap:wrap;gap:0.0rem;margin-top:0.25rem;'>"
        + "".join(loops_html)
        + "</div>"
    )
    st.markdown(loops_container_html, unsafe_allow_html=True)

    # Constitutional values (if present)
    const_vals = adra.get("constitutional_values_active") or []

    # ---------------- Governance loop explanations (radio, auto-selected) ----------------
    st.markdown(
        "<div style='margin-top:0.5rem;font-size:0.85rem;opacity:0.9;'>"
        "Select a governance loop to view detailed explanation:"
        "</div>",
        unsafe_allow_html=True,
    )

    options = []
    option_keys = []

    # Veto Feedback Path
    if veto_triggered:
        options.append("🔴 Veto Feedback Path (triggered)")
        option_keys.append("veto")
    else:
        options.append("⚪ Veto Feedback Path (not triggered)")
        option_keys.append("veto")

    # Continuous Drift Detection Agent
    if drift_outcome == "DRIFT_ALERT":
        options.append(f"🟢 Continuous Drift Detection Agent (DRIFT ALERT: score {drift_score})")
        option_keys.append("dda")
    else:
        options.append("🟡 Continuous Drift Detection Agent (monitoring)")
        option_keys.append("dda")

    # Constitutional Governance Path (always visible)
    options.append("🏛️ Constitutional Governance Path (out-of-band)")
    option_keys.append("constitutional")

    # Auto-select most relevant loop
    if veto_triggered:
        default_index = 0
    elif drift_outcome == "DRIFT_ALERT":
        default_index = 1
    else:
        default_index = 1  # DDA is default (always monitoring)

    selected_loop = st.radio(
        "",
        options,
        index=default_index,
        key=f"{key_prefix}_governance_loop_selector",
        horizontal=False,
        label_visibility="collapsed"
    )

    selected_key = option_keys[options.index(selected_loop)]

    st.markdown("---")

    # Show details based on selection
    if selected_key == "veto":
        st.markdown("### Veto Feedback Path (Blocking Pre-Execution Loop)")

        if veto_triggered:
            st.error("**⛔ ACTIVE** - This loop was triggered for this ADRA")
            veto_cat = l7.get("veto_category", "UNKNOWN")
            escalation = l7.get("escalation_required", "NONE")
            st.markdown(
                f"- **Veto category:** `{veto_cat}`\n"
                f"- **Escalation required:** `{escalation}`"
            )
            signal = (l7 or {}).get("corrective_signal") or {}
            violations = signal.get("violations") or []

            if violations:
                st.markdown("**Corrective signal to agent (what to fix):**")
                for v in violations:
                    st.markdown(
                        f"- **{v.get('article','UNKNOWN')}** "
                        f"({v.get('severity','UNKNOWN')}): {v.get('explanation','')}"
                    )
            else:
                st.info("No corrective signal payload attached (yet).")

        else:
            st.success("**✅ NOT TRIGGERED** - No veto raised for this ADRA")

            
        st.markdown("""
                 
**How it works:**
- This loop is **synchronous and blocking**: it runs *before execution* and stops the request.
- It is activated whenever GNCE blocks a requested action due to a **blocking policy violation** at the Constraint Validation or Execution Gate.
- The request **cannot proceed** until the violation is resolved.

**When active, GNCE:**
- Generates a **Veto Artifact** and logs it into the **SARS ledger** (proof of prevention).
- Sends a **corrective signal** back to the requesting agent, indicating exactly which rule was breached so the agent can re-plan and resubmit a compliant request.

*Classification: synchronous runtime constitutional loop (blocking, pre-execution).*
""")


    elif selected_key == "dda":
        st.markdown("### Continuous Drift Detection Agent (Asynchronous Monitoring Loop)")
        
        if drift_outcome == "DRIFT_ALERT":
            st.warning(f"**📈 DRIFT DETECTED** - Score: {drift_score}")
            if drift_human_rationale:
                st.markdown(f"**Rationale:** {drift_human_rationale}")
        else:
            st.success("**✅ NO DRIFT** - Behavior within baseline")
        
        st.markdown("""

**How it works:**
- This loop runs **asynchronously and autonomously** in the background.
- It monitors the stream of **executed** ADRAs/CETs to detect behavioral drift.
- It does **not block** the current execution; it observes and reacts.

**When the DDA identifies drift, GNCE:**
- Raises a **DRIFT_ALERT** in L6 for the affected ADRAs.
- Issues a **Forced Recalibration Request** back into the policy/model space.
- Execution proceeds normally while the system adapts in the background.

*Classification: asynchronous drift loop (non-blocking, post-execution).*

        """)

    else:  # constitutional
        st.markdown("### 🏛️ Constitutional Governance Path")
        
        if constitutional_invoked:
            st.info("**🏛 Engaged (out-of-band)** — sovereign governance signals are present for this run.")
        else:
            st.success("**⚪ Monitoring** — sovereign governance loop monitoring constitutional performance.")

        if const_vals:
            st.markdown(f"**Constitutional values active for this ADRA:** {', '.join(const_vals)}")
        
        st.markdown("""
**How it works:**
- This loop represents the **highest level of oversight** in GNCE – it governs the governance 
model itself rather than individual ADRAs.
- It is intended for **human and/or regulatory approval** of fundamental policy and 
constitutional changes that shape how the system operates.

**Handled by:**
- **Block O – Sovereign Governance Dashboard:** humans and regulators review GNCE's governance 
posture, SARS audit trails and constitutional performance.
- **Block P – Policy Feedback Commit Handler:** approved governance changes are committed back 
into GNCE as updated Governance-as-Code (policies, constraints, weightings).

**Characteristics:**
- Slow, periodic and intentional – in stark contrast to the continuous, machine-speed loops of 
the DRE and Drift Detection Engine.
- Operates **out-of-band** from runtime execution; it never participates in live verdicts.

**Purpose & Impact:**
- Reviews and updates the **governance model itself** (e.g. core policies, DRE constraints, 
CSE weighting factors, constitutional exceptions).
- Changes flowing through this path are **human/regulatory approved**, may carry **legal 
consequences**, and are recorded in the **SARS subsystem** so that the *reason why* the 
governance changed is immutably auditable.

*Classification: supervisory constitutional governance loop (slow, sovereign, out-of-band).*
        """)

    # ---------------- Constitutional basis (L1) ----------------
    if basis:
        st.markdown("---")
        st.markdown("**📜 Constitutional basis (L1 policy rationale)**")
        st.markdown(
            f"<p style='font-size:0.9rem;line-height:1.45;'>{basis}</p>",
            unsafe_allow_html=True,
        )

    # ---------------- Veto Artifact panel (L7) — BEFORE CET ----------------
    _render_veto_artifact_panel(l7, veto_triggered=veto_triggered)

    # ---------------- CET v0.4 panel (L5) ----------------
    _render_cet_panel(l5)

    # ---------------- Drift rationale (L6) ----------------
    if drift_outcome == "DRIFT_ALERT":
        st.markdown("---")
        st.markdown("**Drift rationale (L6 – Continuous Drift Detection Agent)**")

        if drift_human_rationale:
            st.markdown(
                f"<p style='font-size:0.92rem;line-height:1.45;'>{drift_human_rationale}</p>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<p style='font-size:0.92rem;line-height:1.45;'>"
                "GNCE's Continuous Drift Detection Agent (DDA) raised a DRIFT_ALERT "
                "for this ADRA, indicating that recent behaviour or input patterns "
                "have diverged significantly from the expected baseline. This feeds "
                "a Forced Recalibration Request back into the policy loop even when "
                "constitutional checks remain within bounds."
                "</p>",
                unsafe_allow_html=True,
            )