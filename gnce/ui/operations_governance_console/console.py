# gnce/ui/operations_governance_console/console.py
from __future__ import annotations

from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

import streamlit as st

from .utils.viz import redact_obj
from .utils.ledger_queries import (
    default_ledger_paths,
    discover_ledger_sources,
    load_ledger_entries,
    normalize_entry,
    session_constitution_hash,
    compute_session_fingerprint,
)

from .views.drift_loop import render_drift_loop
from .views.sovereign_loop import render_sovereign_loop
from .views.veto_loop import render_veto_loop


def _bootstrap_paths() -> Path:
    """
    Repo-safe bootstrap. Returns repo_root.
    """
    here = Path(__file__).resolve()
    repo_root = here.parents[3]  # .../<repo_root>
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    return repo_root


def _coerce_ops_entry(e: Dict[str, Any]) -> Dict[str, Any]:
    """
    Defensive coercion so Block M can operate across ledger shapes:
      - unwrap {"record": ...} envelopes
      - decision/verdict alignment
      - time/timestamp alignment
      - best-effort constitution_hash extraction from _envelope
    """
    if not isinstance(e, dict):
        return {}

    # Unwrap envelope patterns if they slip through
    if "record" in e and isinstance(e.get("record"), dict):
        e = e["record"]

    # Decision normalization
    if e.get("decision") is None and e.get("verdict") is not None:
        e["decision"] = e.get("verdict")
    if e.get("verdict") is None and e.get("decision") is not None:
        e["verdict"] = e.get("decision")

    # Timestamp normalization
    if e.get("timestamp_utc") is None and e.get("time") is not None:
        e["timestamp_utc"] = e.get("time")
    if e.get("time") is None and e.get("timestamp_utc") is not None:
        e["time"] = e.get("timestamp_utc")

    # Constitution hash extraction (optional)
    if e.get("constitution_hash") is None:
        env = e.get("_envelope") if isinstance(e.get("_envelope"), dict) else {}
        e["constitution_hash"] = (
            env.get("constitution_hash")
            or (env.get("L4_policy_lineage_and_constitution") or {}).get("constitution_hash")
            or (env.get("constitution") or {}).get("hash")
        )

    return e


def _load_disk_streams(repo_root: Path) -> tuple[list[dict[str, Any]], int, list[dict[str, Any]], dict[str, Any], list[Path]]:
    """
    Load sovereign evidence from disk, *without mixing streams*.

    Returns:
      - session_entries: ADRA-level decision evidence (sars_session_ledger.jsonl)
      - runs_observed: count of run events (run_events.jsonl)
      - article_rows: article-level rows (sars_article_ledger.jsonl)
      - meta: provenance dict
      - search_dirs: ledger search roots
    """
    search_dirs = default_ledger_paths(repo_root)
    sources = discover_ledger_sources(search_dirs)

    session_sources = [p for p in sources if p.name == "sars_session_ledger.jsonl"]
    run_sources = [p for p in sources if p.name == "run_events.jsonl"]
    article_sources = [p for p in sources if p.name == "sars_article_ledger.jsonl"]

    raw_session, meta_session = load_ledger_entries(session_sources)
    raw_runs, meta_runs = load_ledger_entries(run_sources)
    raw_articles, meta_articles = load_ledger_entries(article_sources)

    session_entries = [_coerce_ops_entry(normalize_entry(e)) for e in raw_session]
    article_rows = [_coerce_ops_entry(normalize_entry(e)) for e in raw_articles]

    runs_observed = len(raw_runs)

    meta = {
        "mode": "disk",
        "entries_loaded": len(session_entries),
        "runs_loaded": runs_observed,
        "articles_loaded": len(article_rows),
        "used_sources": (
            (meta_session.get("used_sources") or [])
            + (meta_runs.get("used_sources") or [])
            + (meta_articles.get("used_sources") or [])
        ),
        "discovered_count": len(sources),
        "errors_count": int(meta_session.get("errors_count", 0))
        + int(meta_runs.get("errors_count", 0))
        + int(meta_articles.get("errors_count", 0)),
    }
    return session_entries, runs_observed, article_rows, meta, search_dirs


def render_operations_governance_console(entries_param: Optional[List[Dict[str, Any]]] = None) -> None:
    repo_root = _bootstrap_paths()

    st.markdown("# 🧭 Governance Oversight Console (Block M)")
    st.caption("Sovereign, read-only constitutional observatory. No execution. No mutation. Evidence only.")

    # ---- Discover & load ledger entries (read-only)
    # Block M is sovereign: disk evidence first. Session-state only as fallback (Lab/dev convenience).
    try:
        entries, runs_observed, article_rows, meta, search_dirs = _load_disk_streams(repo_root)
    except Exception as e:
        entries, runs_observed, article_rows = [], 0, []
        search_dirs = []
        meta = {"mode": "disk_error", "entries_loaded": 0, "runs_loaded": 0, "articles_loaded": 0, "used_sources": [], "errors_count": 1, "error": str(e)}

    # Dev-only fallback: session_state (never preferred over disk)
    if not entries:
        ss_entries = st.session_state.get("sars_ledger", []) or st.session_state.get("gn_ledger", [])
        if ss_entries:
            entries = [_coerce_ops_entry(normalize_entry(e)) for e in ss_entries]
            meta = {
                "mode": "session_state_fallback",
                "entries_loaded": len(entries),
                "runs_loaded": 0,
                "articles_loaded": 0,
                "used_sources": ["session_state::sars_ledger (fallback)"],
                "errors_count": 0,
            }

    # Legacy fallback: caller-provided entries (last resort)
    if not entries and entries_param:
        entries = [_coerce_ops_entry(normalize_entry(e)) for e in entries_param]
        meta = {
            "mode": "caller_fallback",
            "entries_loaded": len(entries),
            "runs_loaded": 0,
            "articles_loaded": 0,
            "used_sources": ["caller::entries (fallback)"],
            "errors_count": 0,
        }

    # ---- Top ribbon
    constitution_hash = session_constitution_hash(entries)
    fingerprint = compute_session_fingerprint(entries)

    cols = st.columns(4)
    cols[0].metric("Entries Loaded", str(meta.get("entries_loaded", 0)))
    cols[1].metric("Sources Used", str(len(meta.get("used_sources", []) or [])))
    cols[2].metric("Dominant Constitution Hash", (constitution_hash[:10] + "…") if constitution_hash else "None")
    cols[3].metric("Session Fingerprint", fingerprint[:10] + "…")

    with st.expander("📌 Data provenance (read-only)", expanded=False):
        mode = str(meta.get("mode", ""))
        if mode.startswith("session_state"):
            st.write("**Mode:** session_state")
            st.write("**Used sources:**")
            for s in meta.get("used_sources", []):
                st.write(f"- `{s}`")
            st.write("**Discovery metadata:**")
            st.json(meta)
        else:
            st.write("**Search directories:**")
            for d in search_dirs:
                st.write(f"- `{d}`")
            st.write("**Used sources:**")
            for s in meta.get("used_sources", []):
                st.write(f"- `{s}`")
            st.write("**Discovery metadata:**")
            st.json(meta)

    st.divider()

    # ---- Governance Health Statement
    from .models.health import governance_health_statement

    st.markdown("## 🧾 Governance Health Statement (Regulator-grade)")
    hs = governance_health_statement(entries)

    # Override runs observed with run_events stream (so it stays coherent)
    if isinstance(hs, dict):
        hs["runs_observed"] = runs_observed

    # Consistent denominator across Block M: only ALLOW/DENY are counted as decisions.
    # This prevents UNKNOWN / telemetry rows from skewing the operational DENY rate.
    try:
        from .utils.viz import entries_to_df  # local import to avoid circulars
        _df_for_rate = entries_to_df(entries)
        _valid = _df_for_rate[_df_for_rate["verdict"].isin(["ALLOW", "DENY"])] if not _df_for_rate.empty else _df_for_rate
        _denom = int(len(_valid))
        _deny_n = int((_valid["verdict"] == "DENY").sum()) if _denom else 0
        deny_rate_pct_calc = round((_deny_n / _denom) * 100.0, 2) if _denom else 0.0
    except Exception:
        deny_rate_pct_calc = hs.get("deny_rate_pct", 0) or 0

    # Prefer the calculated value for UI consistency
    hs["deny_rate_pct"] = deny_rate_pct_calc

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Risk Band", hs.get("risk_band", "—"))
    c2.metric("Runs Observed", hs.get("runs_observed", 0))
    c3.metric("DENY Rate", f"{deny_rate_pct_calc}%")
    c4.metric(
        "Evidence Completeness",
        f"TS {hs.get('timestamp_coverage_pct', 0)}% · CONST {hs.get('constitution_hash_coverage_pct', 0)}%",
    )

    with st.expander("📌 Attestation", expanded=True):
        st.write(hs.get("attestation", ""))

    notes = hs.get("notes") or []
    if notes:
        st.markdown("**Notes / Findings:**")
        for n in notes:
            st.write(f"- {n}")

    st.divider()

    depth_choice = st.radio(
        "Explainability Depth",
        ["Summary", "Standard", "Deep"],
        index=1,
        horizontal=True,
        key="blockm_depth",
    )

    # ---- The 3 governance loops (sovereign, read-only)
    render_drift_loop(entries, depth=depth_choice)
    render_sovereign_loop(
        entries,
        session_fingerprint=fingerprint,
        constitution_hash=constitution_hash,
        depth=depth_choice,
    )
    render_veto_loop(entries, depth=depth_choice)

    regulator_view = st.toggle("👁️ Regulator View (Redact PII)", value=True)
    st.caption("🔒 READ-ONLY SOVEREIGN OBSERVATORY — This console does not execute, mutate, or override any GNCE decisions.")

    safe_entries = [redact_obj(e) for e in entries] if regulator_view else entries
    with st.expander("🔍 Raw entries (read-only)", expanded=False):
        st.json(safe_entries[:50])


def main() -> None:
    st.set_page_config(page_title="GNCE • Block M", layout="wide")
    render_operations_governance_console()


if __name__ == "__main__":
    main()