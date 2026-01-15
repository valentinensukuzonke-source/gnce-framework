from __future__ import annotations

from typing import Any, Dict, List, Tuple

import streamlit as st
import pandas as pd

# Registry order source of truth (insertion order preserved in Python 3.7+)
from gnce.gn_kernel.regimes.register import REGIME_REGISTRY, init_registry

# Ensure registry is populated in the UI process
init_registry()



def _layer(adra: Dict[str, Any], *candidates: str) -> Dict[str, Any]:
    for k in candidates:
        v = (adra or {}).get(k)
        if isinstance(v, dict):
            return v
    return {}


def _get_regimes_block(l4: Dict[str, Any]) -> Dict[str, Any]:
    regimes = (l4 or {}).get("regimes") or {}
    return regimes if isinstance(regimes, dict) else {}

def _build_regimes_from_policies_triggered(l4: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback adapter:
    New ADRA schema often stores regime execution as L4.policies_triggered (list of policy/article records),
    not L4.regimes (dict). This converts policies_triggered into the regimes{rid: {results:[...]}} shape
    expected by the drill-down UI.
    """
    policies = (l4 or {}).get("policies_triggered") or []
    if not isinstance(policies, list) or not policies:
        return {}

    regimes: Dict[str, Dict[str, Any]] = {}

    for p in policies:
        if not isinstance(p, dict):
            continue

        raw = (
            p.get("verdict")
            or p.get("outcome")
            or p.get("status")
            or p.get("result")
            or p.get("decision")
            or p.get("disposition")
        )
        status = str(raw or "UNKNOWN").strip().upper()

        if status in {"NOT_APPLICABLE", "N/A", "NA"}:
            status = "NOT_APPLICABLE"
        elif status in {"VIOLATION", "VIOLATED", "FAIL", "FAILED", "BLOCK"}:
            status = "VIOLATED"
        elif status in {"PASS", "PASSED", "OK", "SATISFIED", "COMPLIANT"}:
            status = "SATISFIED"
        elif status in {"UNKNOWN", ""}:
            status = "UNKNOWN"

        rid = str(p.get("regime") or p.get("domain") or "UNKNOWN").strip() or "UNKNOWN"

        # ✅ Legacy compatibility: split merged EU_AI_ACT_ISO_42001 into two regimes
        if rid == "EU_AI_ACT_ISO_42001":
            rids = ["EU_AI_ACT", "ISO_42001"]
        else:
            rids = [rid]

        domain = str(p.get("domain") or "").strip()
        framework = str(p.get("framework") or p.get("policy_family") or "").strip()
        severity = p.get("severity") or p.get("severity_level") or p.get("severity_score") or p.get("criticality")
        rationale = p.get("rationale") or p.get("notes") or p.get("reason") or ""
        ref = p.get("id") or p.get("article") or p.get("ref") or p.get("policy_id") or p.get("policy_key") or ""

        for rrid in rids:
            if rrid == "EU_AI_ACT":
                regimes.setdefault(rrid, {"domain": "EU AI Act", "framework": framework, "results": []})
            elif rrid == "ISO_42001":
                regimes.setdefault(rrid, {"domain": "ISO/IEC 42001", "framework": framework, "results": []})
            else:
                regimes.setdefault(rrid, {"domain": domain or rrid, "framework": framework, "results": []})

            regimes[rrid]["results"].append(
                {
                    "id": ref,
                    "article": p.get("article") or p.get("article_id") or "",
                    "verdict": status,
                    "status": status,
                    "severity": severity,
                    "rationale": rationale,
                }
            )

    return regimes

def _count_verdicts(results: List[Dict[str, Any]]) -> Dict[str, int]:
    c = {"VIOLATED": 0, "SATISFIED": 0, "NOT_APPLICABLE": 0, "UNKNOWN": 0, "OTHER": 0}
    for r in results or []:
        v = str(r.get("verdict") or r.get("status") or "OTHER").upper()
        if v in c:
            c[v] += 1
        else:
            c["OTHER"] += 1
    return c


def _highest_severity(results: List[Dict[str, Any]]) -> Tuple[str, int]:
    order = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}
    best = 1
    for r in results or []:
        raw = r.get("severity")
        try:
            s = int(raw)
        except Exception:
            txt = str(raw or "").upper()
            s = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}.get(txt, 1)
        if s > best:
            best = s
    return order.get(best, "LOW"), best

def _is_l4_executable_regime(rid: str) -> bool:
    spec = (REGIME_REGISTRY or {}).get(rid) or {}
    return bool(spec.get("l4_executable", False))



def _registry_order(regimes: Dict[str, Any]) -> List[str]:
    present = set(regimes.keys())
    ordered: List[str] = []



    for rid in (REGIME_REGISTRY or {}).keys():
        if rid in present:
            ordered.append(rid)

    extras = [rid for rid in regimes.keys() if rid not in ordered]
    return ordered + sorted(extras)


def _regime_label(rid: str, regime: Dict[str, Any]) -> str:
    domain = str(regime.get("domain") or "").strip()
    framework = str(regime.get("framework") or "").strip()
    if domain and framework:
        return f"{rid} — {domain} / {framework}"
    if domain:
        return f"{rid} — {domain}"
    return rid


def render_l4_regimes(adra: Dict[str, Any]) -> None:
    st.subheader("📜 L4 — Regime Execution (Executable Law & Governance)")
    st.caption(f"DEBUG: l4_regimes loaded from: {__file__}")


    l4 = _layer(adra, "L4", "L4_policy_lineage_and_constitution")
    regimes = _get_regimes_block(l4)

    # ✅ Fallback for new ADRA schema: build regimes from policies_triggered
    if not regimes:
        regimes = _build_regimes_from_policies_triggered(l4)

    if not regimes:
        st.info("No regimes executed for this input (none applicable).")
        return

    # ✅ UI filter: executable regimes only by default
    show_all = st.toggle(
        "Show non-executable regimes (standards/frameworks)",
        value=False,
        help="Off = show only regimes marked l4_executable=True in the registry.",
    )

    ordered_ids = _registry_order(regimes)

    # Optional: show every regime in the registry even if it didn't run for this ADRA
    show_registered = st.toggle(
        "Show all registered regimes (even if not triggered)",
        value=False,
        help="Adds registry regimes with 0 results so you can see everything installed."
    )

    if show_registered:
        for rid, spec in (REGIME_REGISTRY or {}).items():
            regimes.setdefault(
                rid,
                {
                    "domain": spec.get("domain") or spec.get("display_name") or rid,
                    "framework": spec.get("framework") or "",
                    "results": [],
                },
            )
        ordered_ids = _registry_order(regimes)


    if not show_all:
        ordered_ids = [rid for rid in ordered_ids if _is_l4_executable_regime(rid)]

    if not ordered_ids:
        st.info("No executable regimes for this input.")
        return

    rows: List[Dict[str, Any]] = []
    for rid in ordered_ids:
        r = regimes.get(rid) or {}
        results = r.get("results") or []
        if not isinstance(results, list):
            results = []

        counts = _count_verdicts(results)
        hi_label, _ = _highest_severity(results)

        spec = (REGIME_REGISTRY or {}).get(rid, {}) or {}
        enf = bool(spec.get("enforceable", False))
        exe = bool(spec.get("l4_executable", False))

        rows.append(
            {
                "Regime": rid,
                "Domain": r.get("domain", ""),
                "Framework": r.get("framework", ""),
                "VIOLATED": counts["VIOLATED"],
                "SATISFIED": counts["SATISFIED"],
                "N/A": counts["NOT_APPLICABLE"],
                "UNKNOWN": counts["UNKNOWN"],
                "Other": counts["OTHER"],
                "Highest Severity": hi_label,
                "Total": len(results),
                "Enforceable": "⚖️" if enf else "📘",
                "L4 Executable": "🔒" if exe else "🧪",
            }
        )

    st.markdown("#### Regimes executed (ordered by registry)")
    st.caption("Legend: ⚖️ enforceable law • 📘 standard/framework • 🔒 L4 executable • 🧪 non-executable")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("#### 🔎 Regime Drill-Down")

    options: List[str] = []
    label_to_id: Dict[str, str] = {}
    for rid in ordered_ids:
        label = _regime_label(rid, regimes.get(rid) or {})
        options.append(label)
        label_to_id[label] = rid

    selected_label = st.selectbox("Select a regime", options=options, key="l4_regime_drilldown")
    selected_id = label_to_id.get(selected_label)
    if not selected_id:
        return

    regime = regimes.get(selected_id) or {}
    results = regime.get("results") or []
    if not isinstance(results, list) or not results:
        st.warning("This regime returned no results.")
        return

    c1, c2 = st.columns(2)
    with c1:
        verdict_filter = st.multiselect(
            "Verdict filter",
            options=["VIOLATED", "SATISFIED", "NOT_APPLICABLE", "UNKNOWN", "OTHER"],
            default=["VIOLATED", "SATISFIED", "NOT_APPLICABLE", "UNKNOWN"],
            key=f"l4_verdict_filter_{selected_id}",
        )
    with c2:
        min_sev = st.selectbox(
            "Minimum severity",
            options=[1, 2, 3, 4],
            index=0,
            key=f"l4_min_sev_{selected_id}",
            help="1=LOW, 2=MEDIUM, 3=HIGH, 4=CRITICAL",
        )

    normed: List[Dict[str, Any]] = []
    for x in results:
        if not isinstance(x, dict):
            continue

        verdict = str(x.get("verdict") or x.get("status") or "OTHER").upper()
        if verdict not in {"VIOLATED", "SATISFIED", "NOT_APPLICABLE", "UNKNOWN"}:
            verdict = "OTHER"

        raw = x.get("severity")
        try:
            sev = int(raw)
        except Exception:
            sev = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}.get(str(raw or "").upper(), 1)

        if verdict not in set(verdict_filter):
            continue
        if sev < int(min_sev):
            continue

        normed.append(
            {
                "Reference": x.get("id") or x.get("article") or x.get("ref") or "",
                "Verdict": verdict,
                "Severity": sev,
                "Rationale": x.get("rationale") or x.get("notes") or "",
            }
        )

    st.markdown(f"**{selected_id}** — {regime.get('domain','')} / {regime.get('framework','')}")
    st.caption(f"Showing {len(normed)} of {len(results)} result(s) after filters.")
    st.dataframe(pd.DataFrame(normed), use_container_width=True, hide_index=True)

