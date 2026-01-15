# gnce/ui/components/sars_ledger_view.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import json
import io
import zipfile

import pandas as pd
import html
import streamlit as st

# imports
import streamlit as st
from typing import List, Dict, Any
from gnce.ui.components.domain_catalog import GNCE_DOMAIN_TAXONOMY, _normalize_domain_id


# -------------------------------------------------------
# Breadcrumb (SARS Ledger → Main Console / ADRA)
# -------------------------------------------------------
# -------------------------------------------------------
# Breadcrumb (SARS Ledger → Main Console / ADRA)
# -------------------------------------------------------
def _flatten_domain_taxonomy(nodes):
    out = {}
    for n in nodes or []:
        if isinstance(n, dict):
            _id = n.get("id")
            _label = n.get("label") or n.get("name")
            if _id and _label:
                out[str(_id)] = str(_label)
            for ch in n.get("children") or []:
                out.update(_flatten_domain_taxonomy([ch]))
    return out

DOMAIN_LABELS = _flatten_domain_taxonomy(GNCE_DOMAIN_TAXONOMY)


def render_breadcrumb():
    adra_id = st.session_state.get("sars_filter_adra")

    if adra_id:
        cols = st.columns([1, 6, 2])

        with cols[0]:
            if st.button("⬅️ Back", use_container_width=True):
                st.session_state["gn_jump_tab"] = "🏛 Main Console"
                st.session_state["main_console_target_adra"] = adra_id
                st.toast("🏛 Ready — click the 🏛 Main Console tab above.", icon="🏛")
                st.rerun()

        with cols[1]:
            st.caption(f"Main Console → SARS Ledger → ADRA `{adra_id}`")

        with cols[2]:
            if st.button("📄 Open ADRA", use_container_width=True):
                st.session_state["gn_jump_tab"] = "📚 ADRA Browser"
                st.session_state["adara_browser_target"] = adra_id
                st.toast("📚 Ready — click the 📚 ADRA Browser tab above.", icon="📚")
                st.rerun()

    st.markdown("---")

# ===============================================================
# Helpers
# ===============================================================
_EMPTY_TOKENS = {"", "—", "-", "N/A", "NA", "NONE", "NULL", "UNKNOWN", "NAN"}

# -----------------------------
# SARS Ledger Emoji Encoders
# -----------------------------

def _oversight_emoji(entry: Dict[str, Any]) -> str:
    """
    Indicates whether this ADRA is subject to external oversight.
    """
    if entry.get("regulatory_triggered"):
        return "🏛️ Oversight"
    return "🧭 Internal"

# -----------------------------
# Decision & Severity Emojis
# -----------------------------

def _decision_emoji(decision: str) -> str:
    if not decision:
        return "—"
    d = decision.upper()
    if d == "ALLOW":
        return "🟢 ALLOW"
    if d == "DENY":
        return "🔴 DENY"
    if d == "BLOCK":
        return "⛔ BLOCK"
    return f"⚪ {decision}"


def _severity_emoji(severity: str) -> str:
    if not severity:
        return "—"
    s = severity.upper()
    if s == "LOW":
        return "🟢 LOW"
    if s == "MEDIUM":
        return "🟡 MEDIUM"
    if s == "HIGH":
        return "🟠 HIGH"
    if s == "CRITICAL":
        return "🔴 CRITICAL"
    return f"⚪ {severity}"


def _safe_state_emoji(entry: Dict[str, Any]) -> str:
    """
    Indicates whether the system entered or maintained a safe state.
    """
    verdict = entry.get("final_verdict")
    veto = entry.get("veto", False)

    if veto or verdict == "DENY":
        return "🛑 Safe-Blocked"
    if verdict == "ALLOW":
        return "✅ Safe-Proceed"
    return "⚠️ Indeterminate"


def _adra_hash_short(adra: Dict[str, Any]) -> str:
    """
    Stable short hash of the ADRA content.
    """
    import hashlib, json
    raw = json.dumps(adra, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:12]


def _norm_str(x: Any) -> str:
    if x is None:
        return "—"
    s = str(x).strip()
    return s if s and s.upper() not in _EMPTY_TOKENS else "—"


def _as_list(x: Any) -> List[str]:
    """Normalize list-like values into a clean list of strings (ignores empty tokens)."""
    if x is None:
        return []
    if isinstance(x, list):
        out: List[str] = []
        for i in x:
            s = str(i).strip()
            if s and s.upper() not in _EMPTY_TOKENS:
                out.append(s)
        return out
    if isinstance(x, str):
        s = x.strip()
        if not s or s.upper() in _EMPTY_TOKENS:
            return []
        parts = [p.strip() for p in s.split(",")]
        return [p for p in parts if p and p.upper() not in _EMPTY_TOKENS]
    return []


def _safe_get(d: Any, *path: str, default=None):
    cur = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


def _dedupe(xs: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _looks_like_envelope(d: Any) -> bool:
    if not isinstance(d, dict):
        return False
    # treat as envelope if it has any of the L0..L7 keys
    return any(str(k).startswith("L") for k in d.keys())


def _resolve_full_adra(adra_id: str, entries: List[Dict[str, Any]], store: Dict[str, Any]) -> Optional[dict]:
    """Prefer store; fallback to embedded envelope on entries."""
    if isinstance(store, dict):
        cand = store.get(adra_id)
        if isinstance(cand, dict):
            return cand

    for e in entries or []:
        if not isinstance(e, dict):
            continue
        if str(e.get("adra_id")) != str(adra_id):
            continue
        env = e.get("_envelope")
        if _looks_like_envelope(env):
            return env
    return None


def _collect_rule_ids_from_adra(adra: dict) -> List[str]:
    """Collect rule ids from L3 + L4 (deduped)."""
    ids: List[str] = []

    # L3
    for row in (_safe_get(adra, "L3_rule_level_trace", "causal_trace", default=[]) or []):
        if isinstance(row, dict):
            ids += [str(x) for x in (row.get("rule_ids") or []) if str(x).strip()]

    # L4 policies_triggered
    for pol in (_safe_get(adra, "L4_policy_lineage_and_constitution", "policies_triggered", default=[]) or []):
        if isinstance(pol, dict):
            ids += [str(x) for x in (pol.get("rule_ids") or []) if str(x).strip()]

    # L4 policy_lineage explainability chains (if present)
    for pol in (_safe_get(adra, "L4_policy_lineage_and_constitution", "policy_lineage", default=[]) or []):
        if isinstance(pol, dict):
            chain = _safe_get(pol, "explainability", "rule_chain", default=[]) or []
            ids += [str(x) for x in chain if str(x).strip()]

    return _dedupe(ids)


# ===============================================================
# Main renderer
# ===============================================================
def render_sars_ledger(entries: List[Dict[str, Any]], adra_store: Dict[str, Any]) -> None:
    render_breadcrumb()
    st.caption("Session-scoped, read-only evidence index derived from the SARS ledger row model.")

    if not entries:
        st.info("Ledger rows are empty. Run GNCE to generate SARS entries.")
        return

    rows: List[Dict[str, Any]] = []

    # ===========================================================
    # BUILD ROWS — AUTHORITATIVE FROM ADRA STORE (MULTI-REGIME)
    # ===========================================================
    for entry in entries:
        if not isinstance(entry, dict):
            continue

        adra_id = _norm_str(entry.get("adra_id"))
        if adra_id == "—":
            continue

        adra = adra_store.get(adra_id)
        if not isinstance(adra, dict):
            # fallback: try resolve from entry envelope
            adra = _resolve_full_adra(adra_id, entries, adra_store) or {}
        if not isinstance(adra, dict) or not adra:
            continue

        # ---------------------------
        # L1 — Verdict (truth source)
        # ---------------------------
        l1 = adra.get("L1_the_verdict_and_constitutional_outcome", {}) if isinstance(adra, dict) else {}
        decision = _norm_str(l1.get("decision_outcome") or l1.get("verdict")).upper()
        severity = _norm_str(l1.get("severity")).upper()
        ts = _norm_str(adra.get("created_at_utc") or l1.get("timestamp_utc") or adra.get("timestamp_utc"))
        bundle_id = _norm_str(adra.get("decision_bundle_id"))


        # ---------------------------
        # L4 — Violations + Regime/Domain (truth)
        # ---------------------------
        l4 = adra.get("L4_policy_lineage_and_constitution", {}) if isinstance(adra, dict) else {}
        policies = (l4.get("policies_triggered", []) or []) if isinstance(l4, dict) else []

        violated: List[str] = []
        all_articles: List[str] = []

        for p in policies:
            if not isinstance(p, dict):
                continue
            art = p.get("article") or p.get("Article")
            if art:
                all_articles.append(str(art).strip())
            if str(p.get("status", "")).upper().strip() == "VIOLATED" and art:
                violated.append(str(art).strip())

        violated = _dedupe([x for x in violated if x and x.upper() not in _EMPTY_TOKENS])
        all_articles = _dedupe([x for x in all_articles if x and x.upper() not in _EMPTY_TOKENS])

        # MULTI-REGIME extraction (explode rows)
        regime_domain_pairs: List[Tuple[str, str]] = []
        for p in policies:
            if not isinstance(p, dict):
                continue
            r = _norm_str(p.get("regime"))
            d = _norm_str(p.get("domain"))
            if r != "—" or d != "—":
                regime_domain_pairs.append((r, d))
        if not regime_domain_pairs:
            regime_domain_pairs = [("—", "—")]
        # dedupe pairs
        regime_domain_pairs = list(dict.fromkeys(regime_domain_pairs))

        # ---------------------------
        # L6 / L7
        # ---------------------------
        drift = _norm_str(_safe_get(adra, "L6_behavioral_drift_and_monitoring", "drift_outcome", default=None)).upper()
        veto_triggered = bool(_safe_get(adra, "L7_veto_and_execution_feedback", "veto_triggered", default=False))
        execution_authorized = _safe_get(adra, "L7_veto_and_execution_feedback", "execution_authorized", default=None)

        # normalize execution_authorized -> True/False/None
        if execution_authorized is None:
            execution_authorized = None
        else:
            execution_authorized = bool(execution_authorized)


        # ---------------------------
        # EXPLODE ROWS (policy-level, correct attribution)
        # One row per evaluated policy (multi-regime accurate)
        # ---------------------------

                # ---------------------------
        # EXPLODE ROWS (REGIME-LEVEL, 1 ADRA x Regime)
        # ---------------------------
        # Goal:
        #   One row per regime per ADRA, with violated articles/domains aggregated inside that regime.
        #
        # This prevents the repeated regime spam you’re seeing.

        # Scope filter (if kernel provided it)
        enabled_scope = (
            (adra.get("governance_context") or {}).get("scope_enabled_regimes")
            or adra.get("scope_enabled_regimes")
        )
        enabled_scope_canon = set()
        if isinstance(enabled_scope, (list, tuple, set)):
            enabled_scope_canon = {
                str(x or "").strip().upper().replace(" ", "_").replace("-", "_")
                for x in enabled_scope
                if x
            }


        regime_acc = {}  # regime_display -> {"domains": set(), "violated": set()}

        for p in policies:
            # --------------------------------------------------
            # HARD TYPE GATE
            # --------------------------------------------------
            if not isinstance(p, dict):
                continue

            # --------------------------------------------------
            # HARD SCOPE GATE (FIRST, NON-NEGOTIABLE)
            # --------------------------------------------------
            if enabled_scope_canon:
                r_id = (
                    str(p.get("regime") or "")
                    .strip()
                    .upper()
                    .replace(" ", "_")
                    .replace("-", "_")
                )
                if r_id and r_id not in enabled_scope_canon:
                    continue

            # --------------------------------------------------
            # REGIME DISPLAY (DOMAIN NAME)
            # --------------------------------------------------
            regime_display = _norm_str(p.get("domain"))
            if regime_display == "—":
                continue

            bucket = regime_acc.setdefault(
                regime_display,
                {"domains": set(), "violated": set()}
            )

            # --------------------------------------------------
            # DOMAIN (GNCE taxonomy)
            # --------------------------------------------------
            raw_domain_id = (
                p.get("domain_id")
                or p.get("domainId")
                or p.get("constitutional_domain_id")
            )
            dom_id = _normalize_domain_id(raw_domain_id) if raw_domain_id else None
            domain_label = DOMAIN_LABELS.get(dom_id) if dom_id else None

            if domain_label:
                bucket["domains"].add(domain_label)

            # --------------------------------------------------
            # VIOLATIONS ONLY (NO STUB NOISE)
            # --------------------------------------------------
            if str(p.get("status", "")).upper() == "VIOLATED":
                art = _norm_str(p.get("article"))
                if art != "—":
                    bucket["violated"].add(art)

        # Emit exactly one row per regime
        for regime_display, bucket in regime_acc.items():
            domains_joined = ", ".join(sorted(bucket["domains"])) if bucket["domains"] else "—"
            violated_joined = ", ".join(sorted(bucket["violated"])) if bucket["violated"] else "—"

            rows.append({
                "Evidence Row ID": f"{adra_id}::{regime_display}",
                "ADRA ID": adra_id,
                "Decision Bundle": bundle_id,
                "decision_bundle_id": None if bundle_id == "—" else bundle_id,
                "Timestamp (UTC)": ts,

                "Decision": _decision_emoji(decision),
                "Severity": _severity_emoji(severity),

                "_decision_raw": decision,
                "_severity_raw": severity,
                "_envelope": adra,
                "_articles_all": all_articles,

                # ── Core Outcome ─────────────────────────────
                "Drift": drift,
                "Veto": "🚫 YES" if veto_triggered else "🟢 NO",
                "execution_authorized": execution_authorized,

                # ── v1 COLUMNS ───────────────────────────────
                "Oversight": _oversight_emoji(entry),
                "Safe State": _safe_state_emoji(entry),
                "ADRA Hash": _adra_hash_short(adra_store.get(adra_id, {})),

                # ── Regulatory Context (correct) ─────────────
                "Regime": regime_display,
                "Domain": domains_joined,              # GNCE Constitutional Domain(s)
                "Violated Articles": violated_joined,  # Violated articles within THIS regime only
            })


    # ===========================================================
    # MATERIALIZE DATAFRAME (AUTHORITATIVE)
    # ===========================================================
    df = pd.DataFrame(rows)

    if df.empty:
        st.info("No usable evidence rows could be derived from this session.")
        return

    # ===========================================================
    # METRICS (switchable: per-regime vs per-decision)
    # ===========================================================
    basis = st.radio(
        "Metrics basis",
        ["Per-regime (ADRA×Regime rows)", "Per-decision (unique ADRA)"],
        horizontal=True,
        key="sars_metrics_basis",
    )

    if basis.startswith("Per-decision"):
        # collapse to one row per ADRA (decision artifact)
        group_key = "Decision Bundle" if "Decision Bundle" in df.columns else "ADRA ID"
        g = df.groupby(group_key, dropna=False)

        def _is_blocked(grp: pd.DataFrame) -> bool:
            if "execution_authorized" in grp.columns and (grp["execution_authorized"] == False).any():
                return True
            if "_decision_raw" in grp.columns and (grp["_decision_raw"].astype(str).str.upper() == "DENY").any():
                return True
            if "Decision" in grp.columns and grp["Decision"].astype(str).str.upper().str.contains("DENY").any():
                return True
            return False

        total = int(g.ngroups)
        blocked = int(sum(_is_blocked(grp) for _, grp in g))
        allowed = total - blocked
    else:
        # per-regime rows (current table granularity)
        total = int(len(df))
        if "execution_authorized" in df.columns:
            blocked = int((df["execution_authorized"] == False).sum())
        elif "_decision_raw" in df.columns:
            blocked = int((df["_decision_raw"].astype(str).str.upper() == "DENY").sum())
        else:
            blocked = int(df["Decision"].astype(str).str.upper().str.contains("DENY").sum())
        allowed = total - blocked

    rate = (blocked / total * 100.0) if total else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows (total)", total)
    c2.metric("Allowed Executions", allowed)
    c3.metric("Blocked Executions", blocked)
    c4.metric("Blocked Rate", f"{rate:.1f}%")
    # ===========================================================
    # DISPLAY DF (reorder/hide internal columns *after* metrics)
    # ===========================================================
    df_full = df.copy() 

    preferred_order = [
        "Decision Bundle",
        "ADRA ID",
        "ADRA Hash",
        "Timestamp (UTC)",
        "Decision",
        "Severity",
        "Safe State",
        "Veto",
        "Drift",
        "Oversight",
        "Regime",
        "Domain",
        "Violated Articles",
    ]
    df = df_full[[c for c in preferred_order if c in df_full.columns]]

    # ===========================================================
    # VIEW SETTINGS + FILTERS
    # ===========================================================
    with st.expander("⚙️ View settings", expanded=False):
        limit = st.slider(
            "Rows (most recent)",
            min_value=10,
            max_value=500,
            value=50,
            step=10,
            key="sars_limit",
        )

    # ---------------------------
    # Filter options
    # ---------------------------
    decisions = sorted({
        "ALLOW" if "ALLOW" in d else "DENY" if "DENY" in d else None
        for d in df["Decision"].astype(str).str.upper().tolist()
    } - {None})
    severities = sorted({s for s in df["Severity"].astype(str).str.upper().tolist() if _norm_str(s) != "—"})
    regimes = sorted({r for r in df["Regime"].astype(str).tolist() if _norm_str(r) != "—"})
    domains = sorted({d for d in df["Domain"].astype(str).tolist() if _norm_str(d) != "—"})

    article_set = set()
    for _, r in df.iterrows():
        for a in (r.get("_articles_all", []) or []):
            if a and str(a).strip():
                article_set.add(str(a).strip())

    # ---------------------------
    # Filters UI
    # ---------------------------
    c1, c2, c3, c4, c5, c6 = st.columns([1.1, 1.1, 1.4, 1.4, 1.8, 2.2])

    sel_decision = c1.selectbox("Decision", ["All"] + decisions)
    sel_severity = c2.multiselect("Severity", severities)

    sel_regime = c3.selectbox("Regime", ["(Any)"] + regimes)
    sel_domain = c4.selectbox("Domain", ["(Any)"] + domains)

    sel_article = c5.selectbox("Article", ["(Any)"] + sorted(article_set))
    search_id = c6.text_input("Search ADRA ID", placeholder="Partial ADRA ID…").strip()

    # ---------------------------
    # Apply filters (SAFE COPY)
    # ---------------------------
    fdf = df.copy()

    if sel_regime != "(Any)":
        fdf = fdf[fdf["Regime"] == sel_regime]

    if sel_domain != "(Any)":
        fdf = fdf[fdf["Domain"] == sel_domain]

    if sel_decision != "All":
        fdf = fdf[fdf["Decision"].astype(str).str.upper() == sel_decision]

    if sel_severity:
        fdf = fdf[fdf["Severity"].astype(str).str.upper().isin([s.upper() for s in sel_severity])]

    if sel_article != "(Any)":
        fdf = fdf[
            fdf["Violated Articles"].astype(str).str.contains(sel_article, na=False)
            | fdf["_articles_all"].apply(lambda xs: sel_article in (xs or []))
        ]

    if search_id:
        fdf = fdf[fdf["ADRA ID"].astype(str).str.contains(search_id, na=False)]

    fdf = fdf.sort_values(by="Timestamp (UTC)", ascending=False)
    fdf = fdf.head(limit).reset_index(drop=True)

    # ===========================================================
    # TABLE
    # ===========================================================
    if basis.startswith("Per-decision"):
        group_key = "Decision Bundle" if "Decision Bundle" in fdf.columns else "ADRA ID"
        # keep the most recent row per bundle
        fdf = (
            fdf.sort_values(by="Timestamp (UTC)", ascending=False)
            .groupby(group_key, dropna=False)
            .head(1)
            .reset_index(drop=True)
        )

    display_df_raw = fdf.drop(
        columns=["__article_map", "_decision_raw", "_safe_state_raw", "_veto_raw", "_drift_raw", "_oversight_raw"],
        errors="ignore",
    )

    # If the user selected Per-bundle metrics, show ONE row per Decision Bundle (clean grouping).
    _basis_txt = str(basis or "")
    _per_bundle = ("bundle" in _basis_txt.lower()) or ("decision bundle" in _basis_txt.lower())

    if _per_bundle:
        # Prefer the raw bundle id for grouping, but keep a pretty "Decision Bundle" column for display.
        if "decision_bundle_id" in display_df_raw.columns:
            _bundle_key = "decision_bundle_id"
        elif "Decision Bundle" in display_df_raw.columns:
            _bundle_key = "Decision Bundle"
        else:
            _bundle_key = "ADRA ID"  # last-resort fallback

        _sev_rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

        def _sev_max(values) -> str:
            vals = [str(v).upper() for v in values if pd.notna(v)]
            if not vals:
                return "LOW"
            return max(vals, key=lambda s: _sev_rank.get(s, 0))

        def _collapse_bundle(grp: pd.DataFrame) -> Dict[str, Any]:
            # Decision (worst-case)
            if "Decision" in grp.columns:
                any_deny = grp["Decision"].astype(str).str.upper().str.contains("DENY").any()
                decision = "DENY" if any_deny else grp["Decision"].astype(str).iloc[0]
            else:
                any_deny = False
                decision = "N/A"

            # Severity (max)
            severity = _sev_max(grp["Severity"]) if "Severity" in grp.columns else "LOW"

            # Execution authorized / veto / safe state / drift (worst-case)
            veto = "YES" if ("Veto" in grp.columns and grp["Veto"].astype(str).str.upper().eq("YES").any()) else "NO"
            safe_state = (
                "YES"
                if ("Safe State" in grp.columns and grp["Safe State"].astype(str).str.upper().str.contains("YES|TRUE").any())
                else "NO"
            )
            drift = None
            if "Drift" in grp.columns:
                # Prefer the "worst" drift outcome if present
                drift_vals = [str(v).upper() for v in grp["Drift"].dropna().tolist()]
                if "DRIFT_ALERT" in drift_vals:
                    drift = "DRIFT_ALERT"
                elif "DRIFT_WARN" in drift_vals:
                    drift = "DRIFT_WARN"
                elif drift_vals:
                    drift = drift_vals[0]
                else:
                    drift = "NO_DRIFT"

            # Aggregations
            regimes = ", ".join(sorted({str(x) for x in grp.get("Regime", pd.Series([])).dropna().tolist()}))
            domains = ", ".join(sorted({str(x) for x in grp.get("Domain", pd.Series([])).dropna().tolist()}))
            violated = ", ".join(sorted({str(x) for x in grp.get("Violated Articles", pd.Series([])).dropna().tolist()}))

            ts = None
            if "Timestamp (UTC)" in grp.columns:
                try:
                    ts = pd.to_datetime(grp["Timestamp (UTC)"], errors="coerce").min()
                    ts = ts.isoformat() if pd.notna(ts) else None
                except Exception:
                    ts = str(grp["Timestamp (UTC)"].iloc[0])

            out: Dict[str, Any] = {
                "Decision Bundle": str(grp[_bundle_key].iloc[0]) if _bundle_key in grp.columns else "—",
                "Timestamp (UTC)": ts,
                "Decision": "DENY" if any_deny else "ALLOW",
                "Severity": severity,
                "Safe State": safe_state,
                "Veto": veto,
                "Drift": drift,
                "Regimes": regimes,
                "Domains": domains,
                "Violated Articles": violated,
                "ADRA Count": int(len(grp)),
            }
            return out

        # Build collapsed table (one row per bundle)
        collapsed_rows = []
        for _, grp in display_df_raw.groupby(_bundle_key, dropna=False):
            collapsed_rows.append(_collapse_bundle(grp))

        display_df = pd.DataFrame(collapsed_rows)
    else:
        display_df = display_df_raw

    preferred = [
        "Evidence Row ID",
        "Decision Bundle",
        "decision_bundle_id",
        "ADRA ID",
        "ADRA Hash",
        "Timestamp (UTC)",
        "Decision",
        "Severity",
        "Safe State",
        "Veto",
        "Drift",
        "Oversight",
        "Regime",
        "Regimes",
        "Domain",
        "Domains",
        "Violated Articles",
        "ADRA Count",
    ]
    cols = [c for c in preferred if c in display_df.columns] + [c for c in display_df.columns if c not in preferred]
    display_df = display_df[cols]

    # -----------------------------------------------------------
    # 📋 SARS Ledger Rows (always render; never "disappear")
    # If there are no rows for the current view/filters, Streamlit
    # can render an empty/no-column dataframe as "nothing".
    # Force stable columns + show a clear hint instead.
    # -----------------------------------------------------------
    st.markdown("### 📋 SARS Ledger Rows")

    if display_df.empty or len(display_df.columns) == 0:
        # Use the preferred column order as a stable schema for the empty table.
        stable_cols = [c for c in preferred if c not in ("Regimes", "Domains")]
        display_df = pd.DataFrame(columns=stable_cols)
        st.info("No SARS ledger rows match the current Metrics basis + filters. The table will populate when matching rows exist.")

    st.dataframe(display_df, use_container_width=True, hide_index=True, height=320)

    # ===========================================================
    # HEATMAP (Domain x Regime)
    # ===========================================================
    st.markdown("### 🗺️ Domain → Regime Heatmap")

    heat_df = fdf.groupby(["Domain", "Regime"], dropna=False).size().reset_index(name="Count")
    if heat_df.empty:
        st.info("No regime/domain combinations available for heatmap.")
    else:
        pivot = heat_df.pivot(index="Domain", columns="Regime", values="Count").fillna(0).astype(int)
        st.dataframe(pivot, use_container_width=True)

    # ===========================================================
    # TIME-SERIES — DENY DRIFT (PER REGIME)  ✅ (drift-only!)
    # ===========================================================
    st.markdown("### 📈 DENY Drift Over Time (per Regime)")

    ts_df = fdf.copy()
    ts_df["Timestamp (UTC)"] = pd.to_datetime(ts_df["Timestamp (UTC)"], errors="coerce")
    ts_df = ts_df.dropna(subset=["Timestamp (UTC)"])

    if ts_df.empty:
        st.info("No valid timestamps available for time-series analysis.")
    else:
        ts_df["date"] = ts_df["Timestamp (UTC)"].dt.date

        drift_df = (
            ts_df.groupby(["date", "Regime"], dropna=False)
            .agg(
                total=("Decision", "count"),
                deny=("Decision", lambda s: (s == "DENY").sum()
),
            )
            .reset_index()
        )

        drift_df["DENY rate %"] = drift_df.apply(
            lambda r: (r["deny"] / r["total"] * 100.0) if r["total"] else 0.0,
            axis=1,
        )

        drift_df = drift_df.sort_values(["date", "Regime"], ascending=[True, True])
        st.dataframe(drift_df, use_container_width=True, hide_index=True)

    # ===========================================================
    # DENY RATE BY REGIME (truth from filtered fdf)
    # ===========================================================
    st.markdown("### 📊 DENY Rate by Regime")

    grp = (
        fdf.groupby("Regime", dropna=False)
        .agg(
            total=("Decision", "count"),
            deny=("Decision", lambda s: (s == "DENY").sum()),
        )
        .reset_index()
    )

    grp["DENY rate %"] = grp.apply(
        lambda r: (r["deny"] / r["total"] * 100.0) if r["total"] else 0.0,
        axis=1,
    )

    grp = grp.sort_values(by="DENY rate %", ascending=False)
    st.dataframe(grp, use_container_width=True, hide_index=True)

    # ===========================================================
    # 📦 REGULATOR EVIDENCE PACK (ZIP)  ✅ (CORRECT PLACE)
    # ===========================================================
    st.markdown("### 📦 Regulator Evidence Pack")

    # Article density by regime (safe per-row list extraction)
    art_density = fdf.copy()
    art_density["_viol"] = (
        art_density["Violated Articles"].apply(_as_list)
        if "Violated Articles" in art_density.columns
        else [[] for _ in range(len(art_density))]
    )

    art_density = art_density.explode("_viol")

    if not art_density.empty:
        art_density["_viol"] = art_density["_viol"].astype(str).str.strip()
        art_density = art_density[art_density["_viol"].ne("") & art_density["_viol"].ne("—")]

    if art_density.empty:
        art_density = pd.DataFrame(columns=["Regime", "Article", "count"])
    else:
        art_density = (
            art_density.groupby(["Regime", "_viol"], dropna=False)
            .size()
            .reset_index(name="count")
            .rename(columns={"_viol": "Article"})
            .sort_values(["Regime", "count"], ascending=[True, False])
        )

      
    # Rule-id → regime trace (for pack + UI)
    trace_rows: List[Dict[str, Any]] = []
    for _, rr in fdf.iterrows():
        env = rr.get("_envelope") if isinstance(rr.get("_envelope"), dict) else {}
        rule_ids = _collect_rule_ids_from_adra(env)
        for rid in rule_ids or []:
            trace_rows.append(
                {
                    "Regime": rr.get("Regime"),
                    "Domain": rr.get("Domain"),
                    "ADRA ID": rr.get("ADRA ID"),
                    "Rule ID": rid,
                }
            )
    trace_df = pd.DataFrame(trace_rows)
    if not trace_df.empty:
        trace_df = trace_df.sort_values(["Regime", "Rule ID", "ADRA ID"])

    # Build ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
        # ledger (filtered scope)
        z.writestr(
            "ledger.csv",
            fdf.drop(columns=["_articles_all", "_envelope"], errors="ignore").to_csv(index=False),
        )
        # deny by regime
        z.writestr("deny_by_regime.csv", grp.to_csv(index=False))

        # risk score (computed below; include if available later)
        # We write it after risk_df is computed (see below) — keep placeholder here.

        # article density
        z.writestr("article_density.csv", art_density.to_csv(index=False))

        # rule trace
        if not trace_df.empty:
            z.writestr("rule_trace.csv", trace_df.to_csv(index=False))

        # README
        z.writestr(
            "README.txt",
            "GNCE SARS Regulator Evidence Pack\n"
            "- ledger.csv: filtered evidence ledger (regime/domain scoped)\n"
            "- deny_by_regime.csv: enforcement intensity per regime\n"
            "- article_density.csv: violated article density by regime\n"
            "- rule_trace.csv: Rule-ID → Regime traceability (L3+L4)\n",
        )

    zip_buffer.seek(0)
    st.download_button(
        "⬇️ Download Evidence Pack (ZIP)",
        data=zip_buffer,
        file_name="gnce_sars_evidence_pack.zip",
        mime="application/zip",
    )

    # Optional: show density + trace tables in UI (not required, but useful)
    with st.expander("📜 Article Density by Regime", expanded=False):
        if art_density.empty:
            st.info("No violated articles to aggregate under current filters.")
        else:
            st.dataframe(art_density, use_container_width=True, hide_index=True)

    with st.expander("🧩 Rule-ID → Regime Traceability", expanded=False):
        if trace_df.empty:
            st.info("No rule-id traceability detected under current filters.")
        else:
            st.dataframe(trace_df, use_container_width=True, hide_index=True)

    # ===========================================================
    # REGIME-WEIGHTED RISK SCORE
    # ===========================================================
    st.markdown("### ⚠️ Regime-Weighted Risk Score")

    risk_df = grp.copy()

    risk_df["violations"] = (
        fdf.groupby("Regime")["Violated Articles"]
        .apply(lambda s: sum(1 for x in s.astype(str).tolist() if str(x).strip() != "—"))
        .reindex(risk_df["Regime"])
        .fillna(0)
        .astype(int)
        .values
    )

    risk_df["risk_score"] = risk_df.apply(
        lambda r: r["DENY rate %"] * ((r["violations"] + 1) ** 0.5),
        axis=1,
    )

    risk_df = risk_df.sort_values("risk_score", ascending=False)
    st.dataframe(risk_df, use_container_width=True, hide_index=True)

    # ===========================================================
    # AUTO-GENERATED COMPLIANCE NARRATIVE (clean formatting)
    # ===========================================================
    st.markdown("### 📝 Auto-Generated Compliance Narrative")

    if not risk_df.empty:
        top = risk_df.iloc[0]
        narrative = (
            f"During the evaluated session, GNCE processed {len(df)} autonomous decisions.\n\n"
            f"The highest regulatory exposure was observed under the {top['Regime']} regime, "
            f"with a DENY rate of {top['DENY rate %']:.1f}% and a composite risk score of "
            f"{top['risk_score']:.2f}.\n\n"
            "This exposure is driven by repeated violations of specific regulatory articles, "
            "indicating concentrated compliance pressure rather than systemic failure.\n\n"
            "GNCE maintained full traceability across L1–L7 layers, enabling regulator-grade "
            "auditability and post-hoc review."
        )
    else:
        narrative = "No regulatory risk detected in the current filtered dataset."

    st.text_area("Compliance Narrative", narrative, height=220)

    # ===========================================================
    # EXTERNAL REGULATOR EXPORT (EU DSA / AI ACT) — L3 + L4 rule trace
    # ===========================================================
    st.markdown("### 🏛 External Regulator Export (EU DSA / AI Act)")

    export_rows: List[Dict[str, Any]] = []
    for _, r in fdf.iterrows():
        env = r.get("_envelope") if isinstance(r.get("_envelope"), dict) else {}
        export_rows.append(
            {
                "evidence_row_id": r.get("Evidence Row ID"),
                "decision_id": r.get("ADRA ID"),
                "timestamp": r.get("Timestamp (UTC)"),
                "decision": r.get("Decision"),
                "severity": r.get("Severity"),
                "regime": r.get("Regime"),
                "domain": r.get("Domain"),
                "violated_articles": _as_list(r.get("Violated Articles")),
                "traceability": {
                    "rule_ids": _collect_rule_ids_from_adra(env),
                },
            }
        )

    export_payload = json.dumps(
        {
            "framework": "EU_DSA_AI_ACT",
            "generated_at": pd.Timestamp.utcnow().isoformat(),
            "decisions": export_rows,
        },
        indent=2,
    )

    st.download_button(
        "⬇️ Download EU Regulator JSON",
        data=export_payload,
        file_name="gnce_eu_regulator_export.json",
        mime="application/json",
    )

    # Regime-scoped CSV (filtered)
    csv_df = fdf.drop(columns=["_articles_all", "_envelope"], errors="ignore")
    st.download_button(
        "⬇️ Download Regime-Scoped CSV",
        data=csv_df.to_csv(index=False).encode("utf-8"),
        file_name="sars_ledger_regime_scoped.csv",
        mime="text/csv",
    )

    # ===========================================================
    # DRILL DOWN (use filtered fdf + dedupe IDs)
    # ===========================================================
    st.markdown("### 🔍 Selected ADRA")

    adra_choices = _dedupe([str(x) for x in fdf["ADRA ID"].tolist() if _norm_str(x) != "—"])
    selected = st.selectbox("Choose ADRA ID", adra_choices)

    full_adra = adra_store.get(selected)
    if not isinstance(full_adra, dict):
        # fallback resolve
        full_adra = _resolve_full_adra(selected, entries, adra_store)

    if not isinstance(full_adra, dict):
        st.error("ADRA not found in store/ledger.")
        return

    col1, col2 = st.columns([1, 3])
    with col1:
        st.download_button(
            "⬇️ Download JSON",
            data=json.dumps(full_adra, indent=2),
            file_name=f"{selected}.json",
            mime="application/json",
        )
    with col2:
        st.caption("Full regulator-grade ADRA envelope (L0–L7).")

    with st.expander("🧾 Evidence (L0–L7)", expanded=True):
        st.json(full_adra)

