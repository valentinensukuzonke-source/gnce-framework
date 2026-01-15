
"""ADRA Browser (GNCE)

Enhanced UI for browsing ADRAs produced during a session.
- Supports in-memory ADRAs (st.session_state['adra_store']) and disk ADRA logs (./adra_logs).
- Filters (decision, severity, regime, time, id search)
- Structured views (Summary / Layers / Violations / Raw)
- Downloads (selected JSON, session ZIP, summary CSV)

This file is intended to be imported as:
  from gnce.ui.components.adra_browser import render_adra_browser_panel
and called with no args.
"""

from __future__ import annotations

import io
import json
import os
import zipfile
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st


# -----------------------------
# Helpers
# -----------------------------

def _safe_get(d: Any, path: List[str], default=None):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def _parse_ts(ts: Any) -> Optional[datetime]:
    if not ts or not isinstance(ts, str):
        return None
    try:
        # Handles "...Z" and "+00:00" forms
        s = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except Exception:
        return None


def _pretty_json(obj: Any) -> str:
    try:
        return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=False)
    except Exception:
        return str(obj)


def _find_layer_key(adra: Dict[str, Any], layer_prefix: str) -> Optional[str]:
    # e.g. layer_prefix='L1' should match keys like 'L1_the_verdict_and_constitutional_outcome'
    for k in adra.keys():
        if isinstance(k, str) and k.startswith(layer_prefix + "_"):
            return k
    return None


def _extract_verdict(adra: Dict[str, Any]) -> Tuple[str, str]:
    l1k = _find_layer_key(adra, "L1")
    l1 = adra.get(l1k, {}) if l1k else {}
    decision = (
        _safe_get(l1, ["decision_gate", "decision_outcome"], None)
        or l1.get("decision_outcome")
        or _safe_get(adra, ["verdict_snapshot", "decision_outcome"], None)
        or "UNKNOWN"
    )
    severity = (
        _safe_get(l1, ["decision_gate", "severity"], None)
        or l1.get("severity")
        or _safe_get(adra, ["verdict_snapshot", "severity"], None)
        or "UNKNOWN"
    )
    return str(decision).upper(), str(severity).upper()


def _extract_drift(adra: Dict[str, Any]) -> str:
    l6k = _find_layer_key(adra, "L6")
    l6 = adra.get(l6k, {}) if l6k else {}
    drift = (
        l6.get("drift_outcome")
        or l6.get("drift_status")
        or adra.get("drift_outcome")
        or _safe_get(adra, ["verdict_snapshot", "drift_outcome"], None)
        or "UNKNOWN"
    )
    return str(drift)


def _extract_created_at(adra: Dict[str, Any]) -> Optional[datetime]:
    return _parse_ts(adra.get("created_at_utc") or adra.get("timestamp_utc") or _safe_get(adra, ["verdict_snapshot", "timestamp_utc"], None))


def _extract_regimes(adra: Dict[str, Any]) -> List[str]:
    regimes = (
        adra.get("domains_triggered")
        or _safe_get(adra, ["governance_context", "scope_enabled_regimes"], None)
        or _safe_get(adra, ["L3_rule_level_trace", "enabled_regimes"], None)
        or []
    )
    if isinstance(regimes, list):
        return [str(x) for x in regimes]
    return []


def _extract_violations_count(adra: Dict[str, Any]) -> int:
    # Prefer L1 summary violated count when available
    l1k = _find_layer_key(adra, "L1")
    l1 = adra.get(l1k, {}) if l1k else {}
    v = _safe_get(l1, ["summary", "violated"], None)
    if isinstance(v, int):
        return v

    # Fallback: L7 corrective_signal violations list
    l7k = _find_layer_key(adra, "L7")
    l7 = adra.get(l7k, {}) if l7k else {}
    vs = _safe_get(l7, ["corrective_signal", "violations"], None)
    if isinstance(vs, list):
        return len(vs)

    return 0


def _extract_allowed_count(adra: Dict[str, Any]) -> int:
    l1k = _find_layer_key(adra, "L1")
    l1 = adra.get(l1k, {}) if l1k else {}
    satisfied = _safe_get(l1, ["summary", "satisfied"], None)
    if isinstance(satisfied, int):
        return satisfied

    # Fallback: count SATISFIED in L4 policy_lineage
    l4k = _find_layer_key(adra, "L4")
    l4 = adra.get(l4k, {}) if l4k else {}
    lineage = l4.get("policy_lineage")
    if isinstance(lineage, list):
        return sum(1 for x in lineage if isinstance(x, dict) and str(x.get("status", "")).upper() == "SATISFIED")

    return 0


def _extract_violated_articles(adra: Dict[str, Any]) -> List[str]:
    # Try L1 because[] which often includes article strings
    l1k = _find_layer_key(adra, "L1")
    l1 = adra.get(l1k, {}) if l1k else {}
    because = l1.get("because")
    arts: List[str] = []
    if isinstance(because, list):
        for item in because:
            if isinstance(item, str):
                # Keep only prefix before ':' or '—'
                arts.append(item.split(":")[0].strip())

    # Try L7 corrective signal violations articles
    l7k = _find_layer_key(adra, "L7")
    l7 = adra.get(l7k, {}) if l7k else {}
    vs = _safe_get(l7, ["corrective_signal", "violations"], None)
    if isinstance(vs, list):
        for v in vs:
            if isinstance(v, dict) and v.get("article"):
                arts.append(str(v.get("article")))

    # Dedup, keep order
    seen = set()
    out = []
    for a in arts:
        if a and a not in seen:
            out.append(a)
            seen.add(a)
    return out


def _load_adras_from_disk(log_dir: str = "adra_logs") -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    if not os.path.isdir(log_dir):
        return out

    # Support both adra_*.json and *.adra.json (be forgiving)
    patterns = [
        os.path.join(log_dir, "adra_*.json"),
        os.path.join(log_dir, "*adra*.json"),
    ]
    files: List[str] = []
    for p in patterns:
        try:
            import glob

            files.extend(glob.glob(p))
        except Exception:
            pass

    for fp in sorted(set(files)):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
            adra_id = data.get("adra_id") or os.path.basename(fp).replace(".json", "")
            if isinstance(adra_id, str):
                out[adra_id] = data
        except Exception:
            continue
    return out


@dataclass
class ADRARecord:
    adra_id: str
    created_at: Optional[datetime]
    decision: str
    severity: str
    drift: str
    regimes: List[str]
    violated_count: int
    allowed_count: int

    def label(self) -> str:
        ts = self.created_at.isoformat(timespec="seconds") if self.created_at else "(no time)"
        reg = ",".join(self.regimes[:3]) + ("…" if len(self.regimes) > 3 else "")
        return f"{ts} | {self.adra_id} | {self.decision}/{self.severity} | {reg}"


def _build_records(adras: Dict[str, Dict[str, Any]]) -> List[ADRARecord]:
    recs: List[ADRARecord] = []
    for adra_id, adra in adras.items():
        decision, severity = _extract_verdict(adra)
        recs.append(
            ADRARecord(
                adra_id=adra_id,
                created_at=_extract_created_at(adra),
                decision=decision,
                severity=severity,
                drift=_extract_drift(adra),
                regimes=_extract_regimes(adra),
                violated_count=_extract_violations_count(adra),
                allowed_count=_extract_allowed_count(adra),
            )
        )
    # Sort newest first
    recs.sort(key=lambda r: (r.created_at or datetime.min), reverse=True)
    return recs


def _records_to_rows(recs: List[ADRARecord]) -> List[Dict[str, Any]]:
    rows = []
    for r in recs:
        rows.append(
            {
                "created_at_utc": r.created_at.isoformat(timespec="seconds") if r.created_at else "",
                "adra_id": r.adra_id,
                "decision": r.decision,
                "severity": r.severity,
                "drift": r.drift,
                "violated": r.violated_count,
                "allowed": r.allowed_count,
                "regimes": ", ".join(r.regimes),
            }
        )
    return rows


def _zip_all_adras(adras: Dict[str, Dict[str, Any]]) -> bytes:
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, mode="w", compression=zipfile.ZIP_DEFLATED) as z:
        for adra_id, adra in adras.items():
            z.writestr(f"{adra_id}.json", _pretty_json(adra))
    return bio.getvalue()


def _csv_summary(rows: List[Dict[str, Any]]) -> bytes:
    # Avoid pandas dependency; generate simple CSV
    import csv

    bio = io.StringIO()
    if not rows:
        return b""
    fieldnames = list(rows[0].keys())
    w = csv.DictWriter(bio, fieldnames=fieldnames)
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return bio.getvalue().encode("utf-8")


# -----------------------------
# UI
# -----------------------------

def render_adra_browser_panel() -> None:
    st.markdown("## 🧩 ADRA Browser")
    st.caption("Browse ADRAs and export evidence artifacts (session + disk).")

    # Sources
    # Collect ADRAs from multiple possible in-memory stores to avoid stale views across reruns.
    in_mem: Dict[str, dict] = {}

    def _merge_store(obj: object) -> None:
        """Merge ADRAs into in_mem from a variety of container shapes."""
        if obj is None:
            return
        # Common case: mapping of adra_id -> adra_payload
        if isinstance(obj, dict):
            for _k, _v in obj.items():
                if isinstance(_v, dict):
                    _adra_id = _v.get("adra_id") or _v.get("adra", {}).get("adra_id") or _k
                    if _adra_id:
                        in_mem[str(_adra_id)] = _v
            return
        # Some callers may store a list of ADRA dicts
        if isinstance(obj, (list, tuple)):
            for _v in obj:
                if isinstance(_v, dict):
                    _adra_id = _v.get("adra_id") or _v.get("adra", {}).get("adra_id")
                    if _adra_id:
                        in_mem[str(_adra_id)] = _v
            return
    # Common session keys used by gn_app / prior versions
    for _key in ("gn_adra_store", "adra_store", "gnce_adra_store", "adra_store_session"):
        _merge_store(st.session_state.get(_key))

    # Also capture the most recent ADRA payload if the engine stashes it directly
    for _key in ("last_adra", "current_adra", "latest_adra", "adra_envelope"):
        _v = st.session_state.get(_key)
        if isinstance(_v, dict):
            _adra_id = _v.get("adra_id") or _v.get("adra", {}).get("adra_id")
            if _adra_id:
                in_mem[str(_adra_id)] = _v

    disk_dir = st.session_state.get("adra_log_dir", "adra_logs")
    disk_adras = _load_adras_from_disk(disk_dir)

    # Merge, in-memory wins
    adras: Dict[str, Dict[str, Any]] = dict(disk_adras)
    adras.update(in_mem)

    total = len(adras)

    # Sidebar filters
    with st.expander("🔎 Filters", expanded=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            q = st.text_input("Search ADRA ID", value="", placeholder="type part of an ADRA id…")
        with col2:
            source_mode = st.selectbox(
                "Sources",
                options=["Session + Disk", "Session only", "Disk only"],
                index=0,
                help="Session uses in-memory ADRAs captured during execution; Disk reads ./adra_logs.",
            )
        with col3:
            st.text_input("Log dir", value=str(disk_dir), key="adra_log_dir", help="Disk ADRAs are read from this folder.")

        # Recompute sources after possible dir change
        disk_dir2 = st.session_state.get("adra_log_dir", "adra_logs")
        if disk_dir2 != disk_dir:
            disk_adras = _load_adras_from_disk(disk_dir2)
            adras = dict(disk_adras)
            adras.update(in_mem)
            total = len(adras)

        if source_mode == "Session only":
            adras = dict(in_mem)
        elif source_mode == "Disk only":
            adras = dict(disk_adras)

        recs = _build_records(adras)
        decisions = sorted({r.decision for r in recs})
        severities = sorted({r.severity for r in recs})
        regimes_all = sorted({rg for r in recs for rg in r.regimes})

        c1, c2, c3, c4 = st.columns([1, 1, 2, 2])
        with c1:
            decision_f = st.multiselect("Decision", decisions, default=decisions)
        with c2:
            severity_f = st.multiselect("Severity", severities, default=severities)
        with c3:
            regime_f = st.multiselect("Regime", regimes_all, default=regimes_all)
        with c4:
            # Date range from available timestamps
            ts = [r.created_at for r in recs if r.created_at]
            if ts:
                min_d = min(ts).date()
                max_d = max(ts).date()
                _date_val = st.date_input("Date range (UTC)", value=(min_d, max_d))
                # Streamlit may return either a single date or a (start, end) range
                if isinstance(_date_val, (tuple, list)) and len(_date_val) == 2:
                    d1, d2 = _date_val[0], _date_val[1]
                else:
                    d1 = _date_val
                    d2 = _date_val
            else:
                d1 = d2 = None

    # Apply filters
    filtered: List[ADRARecord] = []
    qn = q.strip().lower()
    for r in recs:
        if qn and qn not in r.adra_id.lower():
            continue
        if r.decision not in decision_f:
            continue
        if r.severity not in severity_f:
            continue
        if regime_f:
            if not any(rg in regime_f for rg in r.regimes):
                continue
        if d1 and d2 and r.created_at:
            if not (d1 <= r.created_at.date() <= d2):
                continue
        filtered.append(r)

    # Top metrics
    deny = sum(1 for r in filtered if r.decision == "DENY")
    allow = sum(1 for r in filtered if r.decision == "ALLOW")
    denom = max(1, allow + deny)
    deny_rate = (deny / denom) * 100.0

    m1, m2, m3, m4 = st.columns([1, 1, 1, 1])
    m1.metric("ADRAs (filtered)", len(filtered), delta=f"of {total}")
    m2.metric("ALLOW", allow)
    m3.metric("DENY", deny)
    m4.metric("DENY rate", f"{deny_rate:.1f}%")

    # Downloads
    rows = _records_to_rows(filtered)
    dl1, dl2, dl3 = st.columns([1, 1, 1])
    with dl1:
        st.download_button(
            "⬇️ Download summary (CSV)",
            data=_csv_summary(rows),
            file_name="adra_summary.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with dl2:
        st.download_button(
            "⬇️ Download ADRAs (ZIP)",
            data=_zip_all_adras({r.adra_id: adras[r.adra_id] for r in filtered if r.adra_id in adras}),
            file_name="adras_session.zip",
            mime="application/zip",
            use_container_width=True,
        )
    with dl3:
        st.caption("Tip: use filters before exporting to limit the ZIP size.")

    st.markdown("---")

    # Overview table
    st.markdown("### Session index")
    st.dataframe(rows, use_container_width=True, hide_index=True)

    if not filtered:
        st.info("No ADRAs match the current filters.")
        return

    # Select ADRA
    options = {r.label(): r.adra_id for r in filtered}
    default_label = next(iter(options.keys()))
    # Coherence: by default, automatically focus the newest ADRA so a fresh run is reflected immediately.
    auto_focus = st.checkbox("Auto-select newest ADRA", value=True, key="adra_browser_autofocus")
    if auto_focus:
        st.session_state["adra_browser_selected_label"] = default_label

    chosen_label = st.selectbox(
        "Select ADRA",
        options=list(options.keys()),
        key="adra_browser_selected_label",
    )
    adra_id = options.get(chosen_label, filtered[0].adra_id)
    adra = adras.get(adra_id)
    if not isinstance(adra, dict):
        st.error("Selected ADRA is not available in the current sources.")
        return

    st.download_button(
        "⬇️ Download selected ADRA (JSON)",
        data=_pretty_json(adra).encode("utf-8"),
        file_name=f"{adra_id}.json",
        mime="application/json",
        use_container_width=False,
    )

    # Detail views
    tab_summary, tab_layers, tab_violations, tab_raw = st.tabs(["Summary", "Layers (L0–L7)", "Violations", "Raw JSON"])

    with tab_summary:
        decision, severity = _extract_verdict(adra)
        drift = _extract_drift(adra)
        created = _extract_created_at(adra)
        regimes = _extract_regimes(adra)

        c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
        c1.metric("Decision", decision)
        c2.metric("Severity", severity)
        c3.metric("Drift", drift)
        c4.metric("Created (UTC)", created.isoformat(timespec="seconds") if created else "—")

        st.markdown("**Regimes / domains triggered**")
        if regimes:
            st.write(", ".join(regimes))
        else:
            st.write("—")

        st.markdown("**Counts**")
        c5, c6 = st.columns([1, 1])
        c5.metric("Violated (count)", _extract_violations_count(adra))
        c6.metric("Allowed (count)", _extract_allowed_count(adra))

        arts = _extract_violated_articles(adra)
        st.markdown("**Violated articles (deduped)**")
        if arts:
            st.write(", ".join(arts))
        else:
            st.write("—")

    with tab_layers:
        for layer in ["L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7"]:
            k = _find_layer_key(adra, layer)
            if not k:
                continue
            with st.expander(f"{layer} — {k.replace(layer + '_', '').replace('_', ' ')}", expanded=(layer in ("L1", "L5", "L7"))):
                st.json(adra.get(k, {}))

        # Also show governance context if present
        gc = adra.get("governance_context")
        if isinstance(gc, dict):
            with st.expander("Governance context", expanded=False):
                st.json(gc)

    with tab_violations:
        st.markdown("### Violations / blocking basis")
        arts = _extract_violated_articles(adra)
        if arts:
            st.write("**Articles:**", ", ".join(arts))
        else:
            st.write("No explicit articles found in L1/L7.")

        # L7 details
        l7k = _find_layer_key(adra, "L7")
        l7 = adra.get(l7k, {}) if l7k else {}
        vs = _safe_get(l7, ["corrective_signal", "violations"], None)
        if isinstance(vs, list) and vs:
            rows_v = []
            for v in vs:
                if not isinstance(v, dict):
                    continue
                rows_v.append(
                    {
                        "article": v.get("article", ""),
                        "severity": v.get("severity", ""),
                        "explanation": v.get("explanation", ""),
                        "clause": v.get("constitutional_clause", ""),
                    }
                )
            st.dataframe(rows_v, use_container_width=True, hide_index=True)
        else:
            st.info("No L7 corrective violations list present.")

        # L1 because
        l1k = _find_layer_key(adra, "L1")
        l1 = adra.get(l1k, {}) if l1k else {}
        because = l1.get("because")
        if isinstance(because, list) and because:
            st.markdown("### L1 because[]")
            for b in because:
                st.write(f"• {b}")

    with tab_raw:
        st.code(_pretty_json(adra), language="json")


# Backwards compatible alias (some code may import render_adra_browser)

def render_adra_browser() -> None:
    render_adra_browser_panel()
