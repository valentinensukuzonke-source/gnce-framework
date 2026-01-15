# gnce/ui/components/executive_summary.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st


# -----------------------------------------------------------
# TELEMETRY UTILS (copied from telemetry_utils.py since it no longer exists)
# -----------------------------------------------------------

def _safe_upper(v: Any) -> str:
    return str(v or "").strip().upper()


def _as_bool(v: Any) -> Optional[bool]:
    if isinstance(v, bool):
        return v
    if v is None:
        return None
    s = str(v).strip().lower()
    if s in {"true", "yes", "y", "1"}:
        return True
    if s in {"false", "no", "n", "0"}:
        return False
    return None


def severity_to_score(raw: Any) -> int:
    """Map severity label or numeric to a risk score."""
    num_map = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}

    if isinstance(raw, (int, float)):
        label = num_map.get(int(raw), "UNKNOWN")
    else:
        label = _safe_upper(raw)

    mapping = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    return mapping.get(label, 0)


def _adra_for_id(adra_store: Dict[str, Any], adra_id: Optional[str]) -> Dict[str, Any]:
    if not adra_id:
        return {}
    adra = (adra_store or {}).get(adra_id, {}) or {}
    return adra if isinstance(adra, dict) else {}


def _extract_decision_severity(adra: Dict[str, Any], row: Dict[str, Any]) -> Tuple[str, str]:
    l1 = _l(adra, "L1_the_verdict_and_constitutional_outcome")
    decision = (
        l1.get("decision_outcome")
        or l1.get("verdict")
        or l1.get("decision")
        or row.get("Decision")
        or row.get("GNCE Decision")
        or "N/A"
    )
    severity = (
        l1.get("severity")
        or row.get("Severity")
        or row.get("GNCE Severity")
        or "—"
    )
    return _safe_upper(decision) or "N/A", _safe_upper(severity) or "—"


def _l(adra: Dict[str, Any], key: str) -> Dict[str, Any]:
    blk = (adra or {}).get(key, {}) or {}
    return blk if isinstance(blk, dict) else {}


def _extract_drift(adra: Dict[str, Any], row: Dict[str, Any]) -> str:
    l6 = _l(adra, "L6_behavioral_drift_and_monitoring")
    drift = (
        l6.get("drift_outcome")
        or l6.get("status")
        or adra.get("drift_outcome")
        or row.get("Drift")
        or "NO_DRIFT"
    )
    return _safe_upper(drift) or "NO_DRIFT"


def _extract_veto(adra: Dict[str, Any], row: Dict[str, Any]) -> Tuple[Optional[bool], str]:
    l7 = _l(adra, "L7_veto_and_execution_feedback")
    veto_triggered = (
        _as_bool(l7.get("veto_triggered"))
        if "veto_triggered" in l7
        else _as_bool(row.get("Veto Triggered"))
    )
    veto_cat = (
        l7.get("veto_category")
        or l7.get("veto_path_triggered")
        or row.get("Veto category")
        or row.get("Veto Category")
        or ""
    )
    return veto_triggered, _safe_upper(veto_cat)


def _extract_timestamp(adra: Dict[str, Any], row: Dict[str, Any]) -> str:
    ts = (
        row.get("Timestamp (UTC)")
        or adra.get("timestamp_utc")
        or adra.get("created_at_utc")
        or ""
    )
    return str(ts or "—")


# -----------------------------------------------------------
# END OF TELEMETRY UTILS
# -----------------------------------------------------------

# Tooltip helper (theme-safe)
# Streamlit's st.metric(tooltip=...) renders a tiny help icon that can be hidden by custom CSS/themes.
# This helper renders an explicit ⓘ icon with an HTML title tooltip next to the label.
# -----------------------------------------------------------
import html as _html


import html as _html

def _metric_with_tooltip(col, label: str, value, delta=None, *, delta_color="normal", tooltip: str = ""):
    tip = _html.escape(str(tooltip or "")).replace("\n", "&#10;")

    # Choose icon fill color by metric semantics
    lab = str(label).upper()
    bg = "rgba(148,163,184,0.35)"  # neutral default (slate)
    if "ALLOW" in lab:
        bg = "rgba(16,185,129,0.85)"   # green
    elif "DENY" in lab:
        bg = "rgba(239,68,68,0.85)"    # red
    elif "RISK" in lab or "SEVERITY" in lab:
        bg = "rgba(168,85,247,0.85)"   # purple

    # Render label + filled-circle tooltip icon
    col.markdown(
        f'<div style="display:flex;align-items:center;gap:6px;">'
        f'  <span style="font-weight:700;">{_html.escape(str(label))}</span>'
        f'  <span title="{tip}" '
        f'        style="'
        f'          cursor:help;'
        f'          display:inline-flex;align-items:center;justify-content:center;'
        f'          width:16px;height:16px;'
        f'          border-radius:999px;'
        f'          background:{bg};'
        f'          color:rgba(255,255,255,0.95);'
        f'          font-size:11px;font-weight:900;'
        f'          line-height:1;'
        f'          user-select:none;'
        f'        ">i</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Render metric card without label (we already printed it above)
    col.metric(label="", value=value, delta=delta, delta_color=delta_color)

# ---------------------------
# Ledger coherence helpers
# ---------------------------

def _row_adra_id(row: Dict[str, Any]) -> str | None:
    """Extract ADRA ID from any supported ledger schema.

    Supports both legacy UI-ledger keys ("ADRA ID") and sovereign ledgers
    ("adra_id" / "ADRA_ID"). Returns None if missing.
    """
    if not isinstance(row, dict):
        return None
    return (
        row.get("ADRA ID")
        or row.get("adra_id")
        or row.get("ADRA_ID")
        or row.get("ADRAID")
        or row.get("id")
    )

def _row_decision(row: Dict[str, Any]) -> str | None:
    if not isinstance(row, dict):
        return None
    return (
        row.get("decision_outcome")
        or row.get("verdict")
        or row.get("Decision Outcome")
        or row.get("Decision")
        or row.get("decision")
    )

def _row_severity(row: Dict[str, Any]) -> str | None:
    if not isinstance(row, dict):
        return None
    return row.get("severity") or row.get("Severity")

def _adra_for_row(adra_store: Dict[str, Any], row: Dict[str, Any]) -> Any:
    """Best-effort to resolve the authoritative ADRA for a ledger row.

    Priority:
      1) Resolve from the in-memory ADRA store via the row's ADRA id.
      2) Fall back to an embedded raw ADRA envelope stored on the row (key: '_raw').
      3) Otherwise return an empty dict.
    """
    try:
        adra_id = _row_adra_id(row)
    except Exception:
        adra_id = None

    adra: Any = {}
    if adra_store and adra_id:
        try:
            adra = _adra_for_id(adra_store, adra_id)
        except Exception:
            adra = {}

    if isinstance(adra, dict) and adra:
        return adra

    raw = row.get("_raw") if isinstance(row, dict) else None
    return raw if isinstance(raw, dict) else (adra if isinstance(adra, dict) else {})



# ---------------------------
# ---------------------------
# Trend helpers (semantic deltas)
# ---------------------------

def _semantic_delta_pp(
    curr_rate: float | None,
    prev_rate: float | None,
    *,
    higher_is_worse: bool,
    stable_threshold_pp: float = 0.05,
) -> tuple[str, str]:
    """Return (delta_text, delta_color) for st.metric.

    - curr_rate/prev_rate are fractions (0..1)
    - stable_threshold_pp is in percentage-points
    - delta_color ∈ {"normal","inverse","off"}
    """
    if curr_rate is None or prev_rate is None:
        return "—", "off"

    delta_pp = (curr_rate - prev_rate) * 100.0
    if abs(delta_pp) < stable_threshold_pp:
        return "→ 0.0% (stable)", "off"

    arrow = "↑" if delta_pp > 0 else "↓"

    # If higher_is_worse: increase = worsening; decrease = improving.
    # If higher_is_worse is False: increase = improving; decrease = worsening.
    improving = (delta_pp < 0 and higher_is_worse) or (delta_pp > 0 and not higher_is_worse)
    label = "improving" if improving else "worsening"

    delta_color = "inverse" if higher_is_worse else "normal"
    return f"{arrow} {abs(delta_pp):.1f}% ({label})", delta_color


def _rate(n: int, d: int) -> float | None:
    return None if d <= 0 else n / d


def _pick_prev_window_ids(ledger: List[Dict[str, Any]], window_ids: List[str]) -> List[str]:
    """Best-effort previous-window selection (no assumptions).

    - If a specific window is selected (window_ids non-empty), we take the
      contiguous block *immediately preceding* the earliest element of that window,
      with the same size.
    - If entire-session is selected (window_ids empty), we use the most recent N
      vs the previous N (N = min(200, total//2), min 1).
    """
    ids = [str(_row_adra_id(r) or "") for r in ledger]
    ids = [i for i in ids if i]

    if not ids:
        return []

    if window_ids:
        wanted = set(window_ids)
        idxs = [i for i, adra_id in enumerate(ids) if adra_id in wanted]
        if not idxs:
            return []
        start = min(idxs)
        size = len(set(window_ids))
        prev_start = max(0, start - size)
        prev_ids = ids[prev_start:start]
        return prev_ids

    # Entire session: compare last N vs previous N
    total = len(ids)
    n = min(200, max(1, total // 2))
    if total < 2:
        return []
    prev_ids = ids[max(0, total - 2 * n) : max(0, total - n)]
    return prev_ids


@st.cache_data(show_spinner=False)
def _ledger_signature(ledger: List[Dict[str, Any]]) -> str:
    """Return a small, stable signature that changes when the live ledger changes.

    This is used only to invalidate Streamlit cache so KPIs refresh whenever new
    rows (ALLOW/DENY/other) are appended to the ledger.
    """
    if not isinstance(ledger, list) or not ledger:
        return "empty"

    last = ledger[-1]
    last_id = None
    last_ts = None

    if isinstance(last, dict):
        last_id = (
            last.get("ledger_id")
            or last.get("id")
            or last.get("event_id")
            or last.get("row_id")
            or _row_adra_id(last)
        )
        last_ts = (
            last.get("timestamp_utc")
            or last.get("logged_at_utc")
            or last.get("created_at_utc")
            or last.get("created_at")
            or last.get("timestamp")
            or last.get("ts")
            or last.get("time")
        )

    return f"n={len(ledger)}|last_id={last_id}|last_ts={last_ts}"


def _decision_counts_for_rows(
    rows: List[Dict[str, Any]],
    adra_store: Dict[str, Any],
) -> Dict[str, int]:
    """Count verdict categories for a set of ledger rows (ledger-coherent)."""
    allow = deny = veto = other = 0
    for r in (rows or []):
        adra = _adra_for_row(adra_store, r)
        dec, _sev = _extract_decision_severity(adra, r)
        dec = _safe_upper(dec) or "UNKNOWN"
        if dec == "ALLOW":
            allow += 1
        elif dec == "DENY":
            deny += 1
        elif dec == "VETO":
            veto += 1
        else:
            other += 1
    return {"allow": allow, "deny": deny, "veto": veto, "other": other, "total": len(rows or [])}

def _compute_exec_kpis(
    ledger: List[Dict[str, Any]],
    adra_store: Dict[str, Any],
    window_adra_ids: List[str],
    ledger_sig: str,
) -> Dict[str, Any]:
    """Compute KPI counts + rates for current window and previous window."""
    if window_adra_ids:
        wanted = set(window_adra_ids)
        curr_rows = [row for row in ledger if _row_adra_id(row) in wanted]
    else:
        curr_rows = ledger[:]

    prev_ids = _pick_prev_window_ids(ledger, window_adra_ids)
    if prev_ids:
        prev_set = set(prev_ids)
        prev_rows = [row for row in ledger if _row_adra_id(row) in prev_set]
    else:
        prev_rows = []

    def _calc(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        decisions: List[str] = []
        severities: List[str] = []

        veto_events = 0
        drift_alerts = 0
        oversight = 0
        safe_state = 0
        intervention = 0  # unique ADRAs requiring any intervention signal

        for r in rows:
            adra_id = _row_adra_id(r)
            adra = _adra_for_row(adra_store, r)

            # ✅ Source-of-truth: ADRA L1 verdict (ADRA is authoritative; ledger is only an index)
            dec, sev = _extract_decision_severity(adra, r)

            # Fallbacks for partially-populated ADRAs / older ledger rows
            if dec in {"", "N/A", "NA", "NONE", "UNKNOWN"} or dec is None:
                l1 = {}
                if isinstance(adra, dict):
                    l1 = (
                        adra.get("L1_the_verdict_and_constitutional_outcome")
                        or adra.get("L1")
                        or {}
                    )
                dec = (
                    l1.get("decision_outcome")
                    or l1.get("decision")
                    or _row_decision(r)
                    or "UNKNOWN"
                )

            if sev in {"", "N/A", "NA", "NONE", "UNKNOWN"} or sev is None:
                l1 = {}
                if isinstance(adra, dict):
                    l1 = (
                        adra.get("L1_the_verdict_and_constitutional_outcome")
                        or adra.get("L1")
                        or {}
                    )
                sev = (
                    l1.get("severity")
                    or _row_severity(r)
                    or "UNKNOWN"
                )

            dec = _safe_upper(dec) or "UNKNOWN"
            sev = _safe_upper(sev) or "UNKNOWN"

            decisions.append(dec)
            severities.append(sev)

            # ✅ Governance signals must come from ADRA/ledger helpers
            drift = _extract_drift(adra, r)
            veto_triggered, _ = _extract_veto(adra, r)

            # Source-of-truth: L1 flags (fallback to ledger columns for back-compat)
            l1_flags = {}
            if isinstance(adra, dict):
                l1_flags = (
                    adra.get("L1_the_verdict_and_constitutional_outcome")
                    or adra.get("L1")
                    or {}
                )

            has_oversight = (
                _as_bool(l1_flags.get("human_oversight_required")) is True
                or _as_bool(r.get("Human Oversight")) is True
            )
            has_safe_state = (
                _as_bool(l1_flags.get("safe_state_triggered")) is True
                or _as_bool(r.get("Safe State")) is True
            )

            if has_oversight:
                oversight += 1
            if has_safe_state:
                safe_state += 1
            if veto_triggered:
                veto_events += 1
            if drift == "DRIFT_ALERT":
                drift_alerts += 1

            if veto_triggered or drift == "DRIFT_ALERT" or has_oversight or has_safe_state:
                intervention += 1


        total = len(rows)

        # Decision outcomes (L1 verdict is authoritative)
        allow_count = sum(1 for d in decisions if d == "ALLOW")
        deny_count = sum(1 for d in decisions if d == "DENY")
        veto_verdict_count = sum(1 for d in decisions if d == "VETO")
        other_count = max(0, total - allow_count - deny_count - veto_verdict_count)

        allow_rate = _rate(allow_count, total)
        deny_rate = _rate(deny_count, total)
        veto_verdict_rate = _rate(veto_verdict_count, total)
        other_rate = _rate(other_count, total)

        # Governance signals (not the same as the L1 verdict)
        veto_rate = _rate(veto_events, total)
        drift_rate = _rate(drift_alerts, total)
        oversight_rate = _rate(oversight, total)
        safe_state_rate = _rate(safe_state, total)
        intervention_rate = _rate(intervention, total)


        avg_score = (
            sum(severity_to_score(s) for s in severities) / len(severities)
            if severities else 0.0
        )

        # 0–100: severity weighted + veto/drift as multipliers (executive-friendly)
        # severity_score in 0..4 -> normalize to 0..100
        severity_norm = (avg_score / 4.0) * 100.0 if avg_score else 0.0
        constitutional_risk_index = (
            (0.60 * severity_norm)
            + (0.25 * (100.0 * (veto_rate or 0.0)))
            + (0.15 * (100.0 * (drift_rate or 0.0)))
        )

        return {
            "total": total,
            "allow": allow_count,
            "deny": deny_count,
            "other": other_count,
            "veto_verdict": veto_verdict_count,
            "veto": veto_events,  # ✅ L7 veto events (this is what execs care about)
            "drift": drift_alerts,
            "oversight": oversight,
            "safe_state": safe_state,
            "intervention": intervention,
            "allow_rate": allow_rate,
            "deny_rate": deny_rate,
            "other_rate": other_rate,
            "veto_verdict_rate": veto_verdict_rate,
            "veto_rate": veto_rate,
            "drift_rate": drift_rate,
            "oversight_rate": oversight_rate,
            "safe_state_rate": safe_state_rate,
            "intervention_rate": intervention_rate,
            "avg_severity_score": avg_score,
            "constitutional_risk_index": constitutional_risk_index,
        }

    return {"curr": _calc(curr_rows), "prev": _calc(prev_rows)}

def render_executive_summary(
    ledger: List[Dict[str, Any]],
    adra_store: Dict[str, Any],
    window_adra_ids: List[str],
    window_label: str,
    key_prefix: str = "exec_summary",  # Add this parameter
) -> None:
    if not ledger:
        st.info("No ADRAs yet in this session.")
        return

    if window_adra_ids:
        filt = [row for row in ledger if _row_adra_id(row) in set(window_adra_ids)]
    else:
        filt = ledger

    if not filt:
        st.info("No ADRAs in the selected time window.")
        return

    # Use key_prefix for unique widget keys
    debug_key = f"{key_prefix}_debug"
    prev_len_key = f"{key_prefix}_prev_ledger_len"
    
    ledger_sig = _ledger_signature(ledger)
    k = _compute_exec_kpis(ledger, adra_store, window_adra_ids, ledger_sig)
    curr = k["curr"]
    prev = k["prev"]

    total = curr["total"]
    st.caption(f"Scope: {window_label} • ADRAs: {total}")
    denom = f"{total} ADRAs ({window_label})"

    # -----------------------
    # Hardening: invariants, debug signature, and "since last run" deltas
    # -----------------------
    # Invariant: totals must reconcile (including VETO verdicts as a distinct bucket).
    reconcile_total = int(curr.get("allow", 0)) + int(curr.get("deny", 0)) + int(curr.get("other", 0)) + int(curr.get("veto_verdict", 0))
    if reconcile_total != int(curr.get("total", 0)):
        st.warning(
            f"Ledger invariant failed: ALLOW({curr.get('allow', 0)}) + DENY({curr.get('deny', 0)}) + "
            f"OTHER({curr.get('other', 0)}) + VETO_VERDICT({curr.get('veto_verdict', 0)}) ≠ TOTAL({curr.get('total', 0)}). "
            "This indicates mixed schemas or malformed rows in the live feed."
        )
    # Since-last-run delta (session-level; survives reruns in this browser tab)
    prev_len = int(st.session_state.get(prev_len_key, 0) or 0)
    if prev_len < len(ledger):
        new_rows = ledger[prev_len:]
        d = _decision_counts_for_rows(new_rows, adra_store)
        if d.get("total", 0) > 0:
            with st.container():
                st.markdown("#### Since last run")
                dc1, dc2, dc3, dc4 = st.columns(4)
                dc1.metric("New ADRAs", d["total"])
                dc2.metric("New ALLOW", d["allow"])
                dc3.metric("New DENY", d["deny"])
                dc4.metric("New OTHER/VETO", d["other"] + d["veto"])
    st.session_state[prev_len_key] = len(ledger)

    # Debug mode (audit-friendly): expose ledger signature
    with st.expander("Debug / audit", expanded=False):
        # Use unique key with prefix
        st.toggle("Debug mode", value=bool(st.session_state.get(debug_key, False)), key=debug_key)
        if st.session_state.get(debug_key):
            st.code(f"ledger_signature = {ledger_sig}", language="text")

    # -----------------------
    # Decision outcomes
    # -----------------------
    st.markdown("#### Decision outcomes")

    # Semantic deltas
    allow_delta, allow_color = _semantic_delta_pp(curr["allow_rate"], prev["allow_rate"], higher_is_worse=False)
    deny_delta, deny_color = _semantic_delta_pp(curr["deny_rate"], prev["deny_rate"], higher_is_worse=True)

    c1, c2, c3 = st.columns(3)

    _metric_with_tooltip(
        c1,
        "Total ADRAs",
        total,
        tooltip=f"Total auditable decisions recorded in the selected window.\n\nScope: {denom}.",
    )

    _metric_with_tooltip(
        c2,
        "ALLOW",
        curr["allow"],
        delta=allow_delta,
        delta_color=allow_color,
        tooltip=(
            "Count of ADRAs whose L1 verdict is ALLOW.\n\n"
            "Percent shown in header = ALLOW / Total ADRAs.\n"
            f"Scope: {denom}.\n"
            f"Now: {curr['allow']} / {total} = {(curr['allow_rate'] or 0)*100:.1f}%."
        ),
    )

    _metric_with_tooltip(
        c3,
        "DENY",
        curr["deny"],
        delta=deny_delta,
        delta_color=deny_color,
        tooltip=(
            "Count of ADRAs whose L1 verdict is DENY.\n\n"
            "Percent shown in header = DENY / Total ADRAs.\n"
            f"Scope: {denom}.\n"
            f"Now: {curr['deny']} / {total} = {(curr['deny_rate'] or 0)*100:.1f}%."
        ),
    )

    if curr.get("other", 0) > 0 or curr.get("veto", 0) > 0:
        st.caption(f"Other verdicts: {curr.get('other', 0)} • VETO verdicts: {curr.get('veto_verdict', 0)} • Veto events: {curr.get('veto', 0)}")

    # -----------------------
    # Governance signals
    # -----------------------
    st.markdown("#### Governance signals")

    veto_delta, veto_color = _semantic_delta_pp(curr["veto_rate"], prev["veto_rate"], higher_is_worse=True)
    drift_delta, drift_color = _semantic_delta_pp(curr["drift_rate"], prev["drift_rate"], higher_is_worse=True)
    over_delta, over_color = _semantic_delta_pp(curr["oversight_rate"], prev["oversight_rate"], higher_is_worse=True)
    safe_delta, safe_color = _semantic_delta_pp(curr["safe_state_rate"], prev["safe_state_rate"], higher_is_worse=True)

    c4, c5, c6, c7 = st.columns(4)

    _metric_with_tooltip(
        c4,
        "Veto events",
        curr["veto"],
        delta=veto_delta,
        delta_color=veto_color,
        tooltip=(
            "Count of L7 veto-path activations (blocking, pre-execution).\n\n"
            "Rate = Veto events / Total ADRAs.\n"
            f"Scope: {denom}.\n"
            f"Now: {curr['veto']} / {total} = {(curr['veto_rate'] or 0)*100:.1f}%."
        ),
    )

    _metric_with_tooltip(
        c5,
        "Drift alerts",
        curr["drift"],
        delta=drift_delta,
        delta_color=drift_color,
        tooltip=(
            "Count of L6 DRIFT_ALERT events (non-blocking, monitoring).\n\n"
            "Rate = Drift alerts / Total ADRAs.\n"
            f"Scope: {denom}.\n"
            f"Now: {curr['drift']} / {total} = {(curr['drift_rate'] or 0)*100:.1f}%."
        ),
    )

    _metric_with_tooltip(
        c6,
        "Oversight required",
        curr["oversight"],
        delta=over_delta,
        delta_color=over_color,
        tooltip=(
            "Count of ADRAs flagged for human review/escalation.\n\n"
            "Rate = Oversight required / Total ADRAs.\n"
            f"Scope: {denom}.\n"
            f"Now: {curr['oversight']} / {total} = {(curr['oversight_rate'] or 0)*100:.1f}%."
        ),
    )

    _metric_with_tooltip(
        c7,
        "Safe-state activations",
        curr["safe_state"],
        delta=safe_delta,
        delta_color=safe_color,
        tooltip=(
            "Count of safe-state triggers (protective posture changes).\n\n"
            "Rate = Safe-state activations / Total ADRAs.\n"
            f"Scope: {denom}.\n"
            f"Now: {curr['safe_state']} / {total} = {(curr['safe_state_rate'] or 0)*100:.1f}%."
        ),
    )

# Intervention load (unique ADRAs requiring any intervention signal)
    int_delta, int_color = _semantic_delta_pp(curr["intervention_rate"], prev["intervention_rate"], higher_is_worse=True)
    _metric_with_tooltip(
        st,
        "Intervention load",
        curr["intervention"],
        delta=int_delta,
        delta_color=int_color,
        tooltip=(
            "Unique ADRAs that require any intervention: veto OR drift alert OR oversight OR safe-state.\n\n"
            "Rate = Intervention ADRAs / Total ADRAs.\n"
            f"Scope: {denom}."
        ),
    )

    # -----------------------
    # Risk
    # -----------------------
    st.markdown("#### Risk")
    st.caption(
        "Constitutional Risk Index blends **severity**, **veto rate**, and **drift rate** into a 0–100 score for exec monitoring."
    )

    avg_score = float(curr["avg_severity_score"] or 0.0)
    risk_index = float(curr["constitutional_risk_index"] or 0.0)

    # Risk band (simple and explainable)
    if risk_index <= 0.0:
        band = "NO DATA"
    elif risk_index < 25:
        band = "LOW"
    elif risk_index < 50:
        band = "MEDIUM"
    elif risk_index < 75:
        band = "HIGH"
    else:
        band = "CRITICAL"

    # Trend for risk index (higher worse)
    risk_delta_pp = None
    if curr.get("constitutional_risk_index") is not None and prev.get("constitutional_risk_index") is not None:
        risk_delta_pp = (risk_index - float(prev["constitutional_risk_index"] or 0.0))
    if risk_delta_pp is None:
        risk_delta, risk_color = "—", "off"
    elif abs(risk_delta_pp) < 0.05:
        risk_delta, risk_color = "→ 0.0 (stable)", "off"
    else:
        arrow = "↑" if risk_delta_pp > 0 else "↓"
        label = "improving" if risk_delta_pp < 0 else "worsening"
        risk_delta, risk_color = f"{arrow} {abs(risk_delta_pp):.1f} ({label})", "inverse"

    c8, c9, c10 = st.columns(3)
    _metric_with_tooltip(
        c8,
        "Avg severity score",
        f"{avg_score:.2f}",
        tooltip="Average severity band score across ADRAs (LOW→CRITICAL).",
    )

    _metric_with_tooltip(
        c9,
        "Constitutional Risk Index",
        f"{risk_index:.1f}",
        delta=risk_delta,
        delta_color="inverse",
        tooltip="0–100 executive score: 60% severity + 25% veto rate + 15% drift rate.",
    )

    _metric_with_tooltip(
        c10,
        "Risk band",
        band,
        tooltip="Human-friendly risk band derived from the risk index thresholds.",
    )

# Bottom ribbon: last ADRA snapshot + severity band label (kept from previous UX)
    last = filt[-1]
    last_ts = _extract_timestamp(_adra_for_id(adra_store, _row_adra_id(last)), last)
    last_dec, last_sev = _extract_decision_severity(_adra_for_id(adra_store, _row_adra_id(last)), last)

    st.markdown(
        f"""
        <div style="margin-top:0.4rem; font-size:0.9rem;">
            <strong>Last ADRA ({window_label}):</strong>
            <span style="margin-left:0.5rem; opacity:0.75;">
                <strong>{last_ts}</strong> · Decision <strong>{last_dec}</strong> · Severity <strong>{last_sev}</strong>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )