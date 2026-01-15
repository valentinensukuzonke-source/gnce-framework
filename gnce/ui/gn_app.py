from __future__ import annotations

import json
from datetime import datetime, timezone
import streamlit as st

# Clear execution state at startup
for k in [
    "exec_prev_len",
    "exec_prev_sig",
    "exec_prev_allow",
    "exec_prev_deny",
]:
    st.session_state.pop(k, None)

# ===============================================================
# Standard library
# ===============================================================
from pathlib import Path
import sys
import uuid
from typing import Any, Dict, List, Optional, Tuple

# Auto-routing import (at top level)
try:
    from gnce.auto_routing.router import AutoRouter
    AUTO_ROUTING_AVAILABLE = True
except ImportError as e:
    AUTO_ROUTING_AVAILABLE = False
    print(f"Auto-routing module not found: {e}. Manual selection only.", file=sys.stderr)

# ===============================================================
# Path bootstrap (repo-safe)
# ===============================================================
REPO_ROOT = Path(__file__).resolve().parents[2]
GNCE_ROOT = Path(__file__).resolve().parents[1]
for p in (REPO_ROOT, GNCE_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# ===============================================================
# Directories
# ===============================================================
BASE_DIR = GNCE_ROOT
CONFIG_DIR = BASE_DIR / "configs"
PROFILE_DIR = BASE_DIR / "profiles"
ADRA_LOG_DIR = REPO_ROOT / "adra_logs"
CONFIG_DIR.mkdir(exist_ok=True)
PROFILE_DIR.mkdir(parents=True, exist_ok=True)
ADRA_LOG_DIR.mkdir(exist_ok=True)

# ===============================================================
# Kernel imports (brain)
# ===============================================================
from gn_kernel.kernel import run_gn_kernel
from gnce.ledger.ledger import read_session_ledger as load_session_ledger
from gn_kernel.execution.executor import build_run_event, append_jsonl

# Optional imports
try:
    from gn_kernel.redaction import redact_adra_for_regulator
except Exception:
    redact_adra_for_regulator = None

try:
    from gn_kernel.federation.config_loader import load_federation_config
    from gn_kernel.federation.federation_gateway import emit_adra_if_enabled
except Exception:
    load_federation_config = None
    emit_adra_if_enabled = None

# ===============================================================
# Theme (GNCE look & feel)
# ===============================================================
try:
    from gnce.ui.theme.css import apply_gnce_theme
except Exception:
    try:
        from css import apply_gnce_theme
    except Exception:
        apply_gnce_theme = None

# ===============================================================
# Optional Kafka KPI consumer
# ===============================================================
try:
    from gn_kernel.integrations.kafka import KafkaKpiConsumer
except Exception:
    KafkaKpiConsumer = None

# ===============================================================
# Ensure regime registry is populated
# ===============================================================
from gnce.gn_kernel.regimes.register import init_registry
init_registry()

# ===============================================================
# UI components (panels)
# ===============================================================
from gnce.gn_kernel.industry.registry import INDUSTRY_REGISTRY
from gnce.ui.components.header import render_header
from gnce.ui.components.input_editor import input_editor
from gnce.ui.components.decision_summary import render_decision_summary
from gnce.ui.components.l_layers import render_constitutional_layers
from gnce.ui.components.l4_regimes import render_l4_regimes
from gnce.ui.components.autonomous_execution_loop import render_autonomous_execution_loop
from gnce.ui.components.execution_path_visualizer import render_execution_path_visualizer
from gnce.ui.components.execution_flow_graph import render_execution_flow_graph
from gnce.ui.components.adra_browser import render_adra_browser_panel
from gnce.ui.components.domain_catalog import render_domain_catalog
from gnce.ui.components.domain_explorer import render_domain_explorer
from gnce.ui.components.governance_catalog import render_governance_catalog_v05
from gnce.ui.components.governance_stewardship import render_governance_stewardship
from gnce.ui.components.regime_outcome_vector import render_regime_outcome_vector
from gnce.ui.components.sars_ledger_view import render_sars_ledger
from gnce.ui.components.forensic_inspector import render_forensic_inspector
from gnce.ui.components.severity_legend import inject_severity_css
from gnce.ui.components.executive_summary import render_executive_summary

# Milestone console (Block M)
from gnce.ui.operations_governance_console.console import render_operations_governance_console

# Telemetry dashboards (optional)
try:
    from gnce.ui.components.telemetry_dashboard import (
        render_time_window_selector,
        render_operations_console,
        render_gnce_telemetry_v07,
    )
    from gnce.ui.components.executive_summary import render_executive_summary
except Exception:
    render_time_window_selector = None
    render_executive_summary = None
    render_operations_console = None
    render_gnce_telemetry_v07 = None

# ===============================================================
# Helper Functions
# ===============================================================
def _severity_to_weight(sev: str) -> int:
    s = str(sev or "").upper()
    return {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}.get(s, 0)


def _canon_id(x: object) -> str:
    return str(x or "").strip().upper().replace(" ", "_").replace("-", "_")


def ui_resolve_industry_profile(current_input: dict) -> tuple[str | None, str | None]:
    """Resolve required kernel routing keys from existing UI state."""
    if not isinstance(current_input, dict):
        return None, None

    # 1) If UI/editor already has them, trust them
    industry_id = current_input.get("industry_id")
    profile_id = current_input.get("profile_id") or current_input.get("industry_profile_id")
    if industry_id and profile_id:
        return _canon_id(industry_id), _canon_id(profile_id)

    # 2) Try loaded customer_profile
    prof = st.session_state.get("customer_profile")
    if isinstance(prof, dict):
        pid = prof.get("profile_id") or prof.get("id") or prof.get("name")
        ind = prof.get("industry_id") or prof.get("industry")
        if pid and ind:
            return _canon_id(ind), _canon_id(pid)
        
    # 3) Last resort: sidebar selection
    sidebar_industry = st.session_state.get("industry_id")
    sidebar_profile = st.session_state.get("profile_id")
    if sidebar_industry and sidebar_profile:
        return _canon_id(sidebar_industry), _canon_id(sidebar_profile)


def preflight_route_payload_or_raise(current_input: dict) -> dict:
    """UI-side contract enforcement for routing."""
    industry_id, profile_id = ui_resolve_industry_profile(current_input)

    if not industry_id or not profile_id:
        raise ValueError("Missing routing: select an Industry and Profile before running GNCE.")

    industry = INDUSTRY_REGISTRY.get(industry_id)
    if not isinstance(industry, dict):
        raise ValueError(f"Unknown industry_id: {industry_id}")

    profiles = industry.get("profiles") or {}
    if not isinstance(profiles, dict) or profile_id not in profiles:
        raise ValueError(f"Unknown profile_id '{profile_id}' for industry '{industry_id}'")

    # Stamp required keys
    current_input["industry_id"] = industry_id
    current_input["profile_id"] = profile_id

    return current_input


def _first_present(*vals):
    """Return first value that is not None and not empty-string."""
    for v in vals:
        if v is None:
            continue
        if isinstance(v, str) and v.strip() == "":
            continue
        return v
    return None


def _extract_decision_and_severity(row: Dict[str, Any]) -> Tuple[str, str]:
    """Extract decision and severity from ledger row."""
    raw = row.get("_raw")
    if not isinstance(raw, dict):
        raw = {}

    l1 = raw.get("L1_the_verdict_and_constitutional_outcome") or {}
    if not isinstance(l1, dict):
        l1 = {}

    decision = _first_present(
        row.get("Decision"),
        row.get("decision"),
        raw.get("Decision"),
        raw.get("decision"),
        l1.get("decision_outcome"),
        l1.get("decision"),
        l1.get("verdict"),
    )
    severity = _first_present(
        row.get("Severity"),
        row.get("severity"),
        raw.get("Severity"),
        raw.get("severity"),
        l1.get("severity"),
        l1.get("risk_severity"),
    )

    d = str(decision or "").upper().strip() or "—"
    s = str(severity or "").upper().strip() or "—"
    return d, s


def recompute_session_stats(ledger: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Compute session statistics from normalized ledger rows."""
    if ledger is None:
        ledger = st.session_state.get("gn_ledger", []) or []

    # Bucket by run id
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for r in ledger or []:
        if not isinstance(r, dict):
            continue
        raw = r.get("_raw") if isinstance(r.get("_raw"), dict) else {}
        run_id = (
            r.get("decision_bundle_id")
            or raw.get("decision_bundle_id")
            or raw.get("decision_bundle")
            or r.get("adra_id")
            or raw.get("adra_id")
        )
        if not run_id:
            continue
        buckets.setdefault(str(run_id), []).append(r)

    total_runs = len(buckets)
    allow_runs = 0
    deny_runs = 0

    # Severity weights
    weights: List[int] = []
    for r in ledger or []:
        raw = r.get("_raw") if isinstance(r.get("_raw"), dict) else {}
        weights.append(_severity_to_weight(r.get("severity") or raw.get("severity")))

    avg_w = (sum(weights) / len(weights)) if weights else 0.0

    for grp in buckets.values():
        blocked = False
        for rr in grp:
            raw = rr.get("_raw") if isinstance(rr.get("_raw"), dict) else {}

            verdict = rr.get("verdict") or raw.get("verdict") or raw.get("decision") or ""
            verdict = str(verdict).upper().strip()

            exec_auth = rr.get("execution_authorized")
            if exec_auth is None:
                exec_auth = raw.get("execution_authorized")

            if verdict == "DENY" or exec_auth is False:
                blocked = True
                break

        if blocked:
            deny_runs += 1
        else:
            allow_runs += 1

    allow_pct = (allow_runs / total_runs * 100.0) if total_runs else 0.0
    deny_pct = (deny_runs / total_runs * 100.0) if total_runs else 0.0

    if total_runs == 0:
        band = "N/A"
    elif avg_w >= 3.5:
        band = "CRITICAL"
    elif avg_w >= 2.5:
        band = "HIGH"
    elif avg_w >= 1.5:
        band = "MEDIUM"
    else:
        band = "LOW"

    last = ledger[-1] if ledger else {}
    last_raw = last.get("_raw") if isinstance(last.get("_raw"), dict) else {}

    return {
        "total_runs": total_runs,
        "allow_count": allow_runs,
        "deny_count": deny_runs,
        "allow_pct": allow_pct,
        "deny_pct": deny_pct,
        "session_risk_band": band,
        "avg_severity_score": avg_w,
        "last_decision": last.get("verdict") or last_raw.get("verdict"),
        "last_severity": last.get("severity") or last_raw.get("severity"),
        "last_ts": last.get("time") or last_raw.get("time"),
    }


def clear_runtime_ledgers() -> None:
    """Clear session-scoped ledgers so UI counters reset to zero."""
    REPO_ROOT = Path(__file__).resolve().parents[2]
    LEDGER_DIR = REPO_ROOT / "adra_logs"

    run_events = LEDGER_DIR / "run_events.jsonl"
    sars_session = LEDGER_DIR / "sars_session_ledger.jsonl"
    sars_article = LEDGER_DIR / "sars_article_ledger.jsonl"
    legacy_session = LEDGER_DIR / "session_ledger.jsonl"

    LEDGER_DIR.mkdir(parents=True, exist_ok=True)

    # Truncate the files that drive counters
    for p in (run_events, sars_session, sars_article):
        try:
            p.write_text("", encoding="utf-8")
        except Exception:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("", encoding="utf-8")

    # Remove legacy
    if legacy_session.exists():
        try:
            legacy_session.unlink()
        except Exception:
            legacy_session.write_text("", encoding="utf-8")

    # Clear Streamlit caches
    try:
        st.cache_data.clear()
    except Exception:
        pass

    for k in [
        "exec_prev_len",
        "exec_prev_sig",
        "exec_prev_allow",
        "exec_prev_deny",
    ]:
        st.session_state.pop(k, None)


def _unwrap_row(r: dict) -> Tuple[dict, dict]:
    env = r if isinstance(r, dict) else {}
    rec = env.get("record") if isinstance(env, dict) else None
    if isinstance(rec, dict):
        return rec, env
    return (env if isinstance(env, dict) else {}), env


def _pick(d: dict, *keys, default=None):
    for k in keys:
        v = d.get(k)
        if v is not None and v != "":
            return v
    return default


def _normalize(rec: dict, env: dict) -> dict:
    def _pick(d: dict, *keys):
        for k in keys:
            if not k:
                continue
            v = d.get(k)
            if v is None:
                continue
            if isinstance(v, str) and v.strip() == "":
                continue
            if str(v).strip() in {"—", "-", "N/A", "NA", "NONE", "NULL", "UNKNOWN"}:
                continue
            return v
        return None

    l1 = rec.get("L1_the_verdict_and_constitutional_outcome") or rec.get("L1") or {}
    if not isinstance(l1, dict):
        l1 = {}

    adra_id = _pick(rec, "ADRA ID", "adra_id", "id") or _pick(env, "adra_id")
    ts = (
        _pick(rec, "Timestamp (UTC)", "timestamp_utc", "created_at_utc", "time")
        or _pick(env, "written_at_utc")
        or _pick(env, "ts_utc")
    )

    decision = _pick(
        rec,
        "Decision",
        "decision",
        "verdict",
        "decision_outcome",
        "decisionOutcome",
    ) or _pick(l1, "decision_outcome", "decision", "verdict")

    severity = _pick(
        rec,
        "Severity",
        "severity",
        "risk_severity",
    ) or _pick(l1, "severity", "risk_severity")

    drift = _pick(
        rec,
        "Drift",
        "drift",
        "drift_outcome",
        "drift_status",
    ) or _pick(rec.get("L6_behavioral_drift_and_monitoring") or {}, "drift_outcome", "drift_status")

    veto_triggered = _pick(
        rec,
        "Veto Triggered",
        "veto_triggered",
        "veto",
    ) or _pick(rec.get("L7_veto_and_execution_feedback") or {}, "veto_path_triggered", "veto_triggered")

    violated_articles = _pick(rec, "Violated Articles", "violated_articles")
    articles_all = _pick(rec, "Articles (all)", "articles_all")
    adra_hash = _pick(rec, "ADRA Hash", "adra_hash")

    full_env = rec.get("_envelope") if isinstance(rec.get("_envelope"), dict) else env

    return {
        "adra_id": adra_id,
        "time": ts,
        "verdict": decision,
        "severity": severity,
        "adra_hash": adra_hash,
        "drift": drift,
        "veto_triggered": veto_triggered,
        "violated_articles": violated_articles,
        "articles_all": articles_all,
        "_raw": rec,
        "_envelope": full_env,
    }


def _get_active_adra(adra: Dict[str, Any], regulator_mode: bool) -> Dict[str, Any]:
    if not regulator_mode or not isinstance(adra, dict):
        return adra
    if redact_adra_for_regulator is None:
        return adra
    try:
        return redact_adra_for_regulator(adra)
    except Exception as e:
        st.warning(f"Redaction failed; showing full ADRA. Error: {e}")
        return adra


def portal_header(title: str, subtitle: str = "") -> None:
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)


def build_pitch_snapshot_html(
    adra: Dict[str, Any],
    stats: Dict[str, Any],
    engine_mode: str,
) -> str:
    """Single-slide pitch snapshot suitable for download as HTML."""
    adra_id = str(adra.get("adra_id") or adra.get("ADRA ID") or "—")
    decision = str(
        adra.get("decision")
        or adra.get("Decision")
        or adra.get("L1_the_verdict_and_constitutional_outcome", {}).get("decision_outcome")
        or "—"
    )
    severity = str(adra.get("severity") or adra.get("Severity") or "—")
    drift = str(adra.get("drift_outcome") or adra.get("Drift") or "—")
    veto = str(
        bool(adra.get("L7_veto_and_execution_feedback", {}).get("veto_path_triggered", False))
    )

    cet = (
        adra.get("cet")
        or adra.get("CET")
        or adra.get("L5_integrity_and_tokenization", {}).get("CET")
        or {}
    )
    content_hash = ""
    if isinstance(cet, dict):
        content_hash = str(cet.get("content_hash") or cet.get("hash") or "")

    def esc(x: Any) -> str:
        return (
            str(x)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    html = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>GNCE Pitch Snapshot — {esc(adra_id)}</title>
<style>
  body {{ margin:0; font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial; background:#0b1220; color:#e2e8f0; }}
  .slide {{ width: 1200px; height: 675px; margin: 0 auto; padding: 34px; box-sizing:border-box; }}
  .top {{ display:flex; justify-content:space-between; align-items:flex-start; gap:18px; }}
  .brand h1 {{ margin:0; font-size: 34px; letter-spacing:-0.4px; }}
  .brand .sub {{ margin-top:6px; opacity:0.85; }}
  .pillrow {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:14px; }}
  .pill {{ padding:6px 10px; border-radius:999px; border:1px solid rgba(148,163,184,0.22); background:rgba(2,6,23,0.55); font-weight:800; }}
  .grid {{ display:grid; grid-template-columns: 1.2fr 1fr; gap:16px; margin-top:18px; }}
  .card {{ background:#020617; border:1px solid rgba(148,163,184,0.18); border-radius:18px; padding:16px; }}
  .kpi {{ display:grid; grid-template-columns: repeat(4, 1fr); gap:10px; }}
  .k {{ opacity:0.75; font-size:12px; }}
  .v {{ font-size:22px; font-weight:900; margin-top:4px; }}
  .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 12px; opacity:0.92; overflow-wrap:anywhere; }}
  .footer {{ margin-top:14px; opacity:0.75; font-size:12px; display:flex; justify-content:space-between; }}
</style>
</head>
<body>
  <div class="slide">
    <div class="top">
      <div class="brand">
        <h1>Gordian Nexus Constitutional Engine (GNCE)</h1>
        <div class="sub">Deterministic governance runtime • Evidence-first • Regulator-grade ADRAs</div>
        <div class="pillrow">
          <div class="pill">Mode: {esc(engine_mode)}</div>
          <div class="pill">ADRA: {esc(adra_id)}</div>
          <div class="pill">Decision: {esc(decision)} • {esc(severity)}</div>
          <div class="pill">Drift: {esc(drift)}</div>
        </div>
      </div>
      <div class="card" style="min-width:360px;">
        <div style="font-weight:900; font-size:16px;">Sovereign Session KPIs</div>
        <div class="kpi" style="margin-top:12px;">
          <div><div class="k">Total runs</div><div class="v">{esc(stats.get("total_runs","—"))}</div></div>
          <div><div class="k">ALLOW %</div><div class="v">{esc(round(float(stats.get("allow_pct",0.0)),1))}</div></div>
          <div><div class="k">DENY %</div><div class="v">{esc(round(float(stats.get("deny_pct",0.0)),1))}</div></div>
          <div><div class="k">Risk band</div><div class="v">{esc(stats.get("session_risk_band","—"))}</div></div>
        </div>
      </div>
    </div>

    <div class="grid">
      <div class="card">
        <div style="font-weight:900; font-size:16px;">End-to-end governance narrative</div>
        <ol style="margin-top:10px; opacity:0.9; line-height:1.45;">
          <li><b>Requester</b> submits an action request (content, API, deployment, etc.).</li>
          <li><b>GNCE</b> evaluates L0–L7 constitutional layers deterministically.</li>
          <li><b>ADRA</b> is produced as a sealed decision artifact (evidence + trace + lineage).</li>
          <li><b>Actuator</b> executes only if authorized; outcomes feed back into L6/L7.</li>
          <li><b>SARS Ledger</b> records immutable evidence index for audits/regulators.</li>
        </ol>
        <div style="margin-top:10px; font-weight:900;">Veto triggered:</div>
        <div style="margin-top:6px; font-size:18px; font-weight:900;">{esc(veto)}</div>
      </div>

      <div class="card">
        <div style="font-weight:900; font-size:16px;">Cryptographic binding (CET)</div>
        <div style="margin-top:8px; opacity:0.85;">
          CET binds L1/L3/L4 evidence to an immutable hash so counterparties can verify integrity independently.
        </div>
        <div style="margin-top:10px;" class="mono">{esc(content_hash) if content_hash else "CET hash not present on this ADRA build."}</div>

        <div style="margin-top:16px; font-weight:900; font-size:16px;">Regulator posture</div>
        <div style="margin-top:8px; opacity:0.9;">
          Evidence is exportable, redaction-aware, and structured for repeatable review.
        </div>
      </div>
    </div>

    <div class="footer">
      <div>Generated by GNCE Console • {esc(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))}</div>
      <div class="mono">Pitch snapshot (single-slide HTML)</div>
    </div>
  </div>
</body>
</html>
"""
    return html


def export_adra_if_enabled(adra: Dict[str, Any], export_dir: Path) -> Optional[Path]:
    """Persist an ADRA JSON to disk only when export is enabled."""
    enabled = bool(
        st.session_state.get("export_intent", st.session_state.get("enable_export_adra", False))
    )
    if not enabled or not isinstance(adra, dict):
        return None

    export_dir.mkdir(parents=True, exist_ok=True)

    operator = (st.session_state.get("export_operator") or "unknown").strip()
    engine_mode = st.session_state.get("engine_mode") or "unknown"
    regulator_mode = bool(st.session_state.get("regulator_mode", False))
    federation_enabled = bool(st.session_state.get("federation_enabled", False))

    adra_id = str(adra.get("adra_id") or adra.get("ADRA ID") or "unknown")
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = export_dir / f"{ts}_{adra_id}.json"

    adra_copy = dict(adra)
    adra_copy["_export"] = {
        "exported_at_utc": ts,
        "operator": operator,
        "engine_mode": engine_mode,
        "regulator_mode": regulator_mode,
        "federation_enabled": federation_enabled,
        "export_path": str(out),
        "format": "GNCE_ADRA_JSON",
    }

    try:
        payload_bytes = json.dumps(adra_copy, ensure_ascii=False, indent=2, default=str).encode("utf-8")
        out.write_bytes(payload_bytes)

        import hashlib
        digest = hashlib.sha256(out.read_bytes()).hexdigest()
        (export_dir / f"{out.name}.sha256").write_text(f"sha256:{digest}  {out.name}\n", encoding="utf-8")

        verify = hashlib.sha256(out.read_bytes()).hexdigest()
        if verify != digest:
            st.sidebar.warning("ADRA export checksum mismatch (post-write verification failed).")
        return out
    except Exception as e:
        st.sidebar.warning(f"ADRA export failed: {e}")
        return None


def main() -> None:
    st.set_page_config(page_title="GNCE Console", layout="wide")
    
    # Theme + severity styles
    if apply_gnce_theme is not None:
        apply_gnce_theme()
    inject_severity_css()
    
    # Session state initialization
    st.session_state.setdefault("current_adra", None)
    st.session_state.setdefault("gn_adra_store", {})
    st.session_state.setdefault("sars_ledger", [])
    st.session_state.setdefault(
        "gn_stats",
        {
            "total_runs": 0,
            "allow_pct": 0.0,
            "deny_pct": 0.0,
            "session_risk_band": "N/A",
            "last_decision": None,
            "last_severity": None,
            "last_ts": None,
        },
    )
    
    # Auto-routing defaults
    st.session_state.setdefault("auto_select_enabled", False)
    st.session_state.setdefault("auto_select_profile", None)
    st.session_state.setdefault("auto_select_customer_profile", None)
    st.session_state.setdefault("current_input_used", {})
    st.session_state.setdefault("last_routing_suggestion", None)
    st.session_state.setdefault("export_intent", False)

    # ===============================================================
    # Sidebar: execution controls
    # ===============================================================
    st.sidebar.header("⚙️ Execution Controls")

    # Initialize AutoRouter if available
    auto_router = None
    if AUTO_ROUTING_AVAILABLE:
        try:
            auto_router = AutoRouter(
                profiles_dir=str(PROFILE_DIR), 
                configs_dir=str(CONFIG_DIR)
            )
        except Exception as e:
            st.sidebar.warning(f"Auto-router initialization failed: {e}")
            auto_router = None

    # Use columns for better layout of mode controls
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.radio("Engine Mode", ["Lab Mode", "Production Mode"], key="engine_mode", index=0)
    with col2:
        st.checkbox("Regulator View", key="regulator_mode", value=False)

    st.checkbox("Edit input JSON before running", key="edit_before_run", value=False)

    # Read values from session state (Streamlit manages these via key parameter)
    engine_mode = st.session_state.get("engine_mode", "Lab Mode")
    regulator_mode = st.session_state.get("regulator_mode", False)
    edit_before_run = st.session_state.get("edit_before_run", False)

    # ADRA export toggle - Use key parameter, Streamlit manages session state
    st.sidebar.toggle(
        "🧾 Enable ADRA export",
        key="enable_export_adra",
        help="When enabled, GNCE writes ADRAs to gnce/adra_logs so the ADRA Browser can render them.",
    )

    # Export operator
    st.sidebar.text_input(
        "👤 Export operator (optional)",
        key="export_operator",
    )

    # Read values from session state (Streamlit manages these via key parameter)
    enable_export_adra = st.session_state.get("enable_export_adra", False)
    export_operator = st.session_state.get("export_operator", "")

    # Federation config
    fed_cfg = None
    federation_enabled = False
    if load_federation_config is not None:
        try:
            fed_cfg = load_federation_config(CONFIG_DIR / "federation_config.json")
            default_fed = bool(getattr(fed_cfg, "enabled", False))
            st.sidebar.toggle(
                "🌐 Enable Federation",
                key="federation_enabled",
                value=default_fed
            )
            federation_enabled = st.session_state.get("federation_enabled", default_fed)
        except Exception:
            federation_enabled = False
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📄 Input Configuration")
    
    cfg_files = sorted(CONFIG_DIR.glob("*.json"))
    cfg_names = [p.name for p in cfg_files]
    selected_path = None
    
    if not cfg_names:
        st.sidebar.warning("No JSON files found in configs/ directory")
    else:
        selected_name = st.sidebar.selectbox("Select Input Payload", cfg_names, index=0)
        selected_path = CONFIG_DIR / selected_name
        
        # Jurisdiction filter
        jurisdiction_choice = st.sidebar.selectbox(
            "Jurisdiction",
            ["AUTO", "ALL", "EU", "US", "US-NY", "GLOBAL"],
            index=0,
            help="Controls which regimes are surfaced in the Outcome Vector. AUTO uses payload/meta if available."
        )
        st.session_state["jurisdiction_choice"] = jurisdiction_choice
        
        # ---------------------------
        # Industry / Customer Profile (scope)
        # ---------------------------
        st.sidebar.markdown("### 🧩 Industry Scope (Kernel Routing)")
        
        # Simple filename-based auto-detection
        filename_lower = selected_name.lower() if selected_name else ""
        
        # Map filename patterns to industry/profile
        if "vlop" in filename_lower or "social" in filename_lower or "vlog" in filename_lower:
            auto_industry = "SOCIAL_MEDIA"
            auto_profile = "VLOG_SOCIAL_META"
        elif "ecom" in filename_lower or "purchase" in filename_lower or "shop" in filename_lower:
            auto_industry = "ECOMMERCE"
            auto_profile = "ECOMMERCE_MARKETPLACE_EU"
        elif "health" in filename_lower or "phi" in filename_lower or "patient" in filename_lower:
            auto_industry = "HEALTHCARE"
            auto_profile = "HEALTHCARE_PROVIDER_US"
        elif "fin" in filename_lower or "payment" in filename_lower or "transaction" in filename_lower:
            auto_industry = "FINTECH"
            auto_profile = "FINTECH_PAYMENTS_EU"
        elif "saas" in filename_lower:
            auto_industry = "SAAS"
            auto_profile = "SAAS_ENTERPRISE_GLOBAL"
        else:
            auto_industry = None
            auto_profile = None
        
        # Show auto-detection status
        if auto_industry:
            st.sidebar.success(f"✅ Auto-detected: {auto_industry}")
            if auto_profile:
                st.sidebar.info(f"💡 Suggested profile: {auto_profile}")
        
        # Get industry IDs from registry
        industry_ids = sorted(list((INDUSTRY_REGISTRY or {}).keys()))
        
        if industry_ids:
            def _industry_label(ind_id: str) -> str:
                spec = (INDUSTRY_REGISTRY or {}).get(ind_id) or {}
                dn = spec.get("display_name") or ind_id
                return f"{dn} ({ind_id})"
            
            # Industry dropdown
            default_industry_index = 0
            if auto_industry and auto_industry in industry_ids:
                default_industry_index = industry_ids.index(auto_industry)
            
            selected_industry_id = st.sidebar.selectbox(
                "Industry",
                industry_ids,
                index=default_industry_index,
                format_func=_industry_label,
                help="Authoritative kernel routing. Auto-selected based on filename pattern."
            )
            st.session_state["industry_id"] = selected_industry_id
            
            # Profile dropdown
            profiles_dict = ((INDUSTRY_REGISTRY or {}).get(selected_industry_id) or {}).get("profiles") or {}
            profile_ids = sorted(list(profiles_dict.keys()))
            
            if profile_ids:
                def _profile_label(pid: str) -> str:
                    ps = profiles_dict.get(pid) or {}
                    dn = ps.get("display_name") or pid
                    return f"{dn} ({pid})"
                
                default_profile_index = 0
                if auto_profile and auto_profile in profile_ids:
                    default_profile_index = profile_ids.index(auto_profile)
                
                selected_profile_id = st.sidebar.selectbox(
                    "Profile",
                    profile_ids,
                    index=default_profile_index if profile_ids else 0,
                    format_func=_profile_label,
                    help="Authoritative kernel routing profile. Auto-selected based on filename pattern."
                )
                st.session_state["profile_id"] = selected_profile_id
                
                # Show enabled regimes
                enabled = (profiles_dict.get(selected_profile_id) or {}).get("enabled_regimes") or []
                if enabled:
                    st.sidebar.caption(f"Enabled regimes: {', '.join(enabled)}")
            else:
                st.sidebar.warning(f"No profiles found for industry: {selected_industry_id}")
        else:
            st.sidebar.error("No industries found in registry")
        
        # Customer Profile Selection
        st.sidebar.markdown("---")
        st.sidebar.subheader("👤 Customer Profile")
        
        profile_files = sorted(PROFILE_DIR.glob("*.json"))
        profile_names = [p.name for p in profile_files]
        
        if profile_names:
            # Auto-select customer profile
            default_profile_index = 0
            selected_profile_id = st.session_state.get("profile_id")
            if selected_profile_id:
                for i, profile_name in enumerate(profile_names):
                    if selected_profile_id.lower() in profile_name.lower():
                        default_profile_index = i
                        break
            
            profile_name = st.sidebar.selectbox(
                "Customer Profile",
                profile_names,
                index=default_profile_index,
                help="Loads a customer profile JSON that scopes regimes and provides domain context."
            )
            selected_profile_path = PROFILE_DIR / profile_name
            
            # Load customer profile
            try:
                if selected_profile_path.exists():
                    with open(selected_profile_path, 'r', encoding='utf-8') as f:
                        customer_profile = json.load(f)
                    st.session_state["customer_profile"] = customer_profile
                    st.session_state["customer_profile_path"] = str(selected_profile_path)
                    st.sidebar.success(f"✓ Loaded: {profile_name}")
            except Exception as e:
                st.sidebar.error(f"Failed to load profile: {e}")
        else:
            st.sidebar.info("No customer profiles found in profiles/ directory")
    
    # -----------------------------------------------------------
    # Action buttons
    # -----------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.subheader("🚀 Actions")
    
    run_clicked = st.sidebar.button("▶️ Run GNCE", type="primary", use_container_width=True)
    
    # Clear Session is LAB-ONLY
    clear_clicked = False
    if engine_mode == "Lab Mode":
        clear_clicked = st.sidebar.button("🗑️ Clear Session", use_container_width=True)
    
    # ===========================================================
    # Global header (supports streaming KPIs)
    # ===========================================================
    if KafkaKpiConsumer is not None and "kpi_consumer" not in st.session_state:
        st.session_state["kpi_consumer"] = KafkaKpiConsumer(
            bootstrap_servers=st.secrets.get("KAFKA_BOOTSTRAP", "localhost:9092"),
            topic=st.secrets.get("KAFKA_TOPIC", "gnce.run_events"),
            group_id=st.secrets.get("KAFKA_GROUP", "gnce-ui-kpis"),
            enabled=bool(st.secrets.get("KAFKA_ENABLED", False)),
        )
        st.session_state["kpi_consumer"].start()
    
    stats = st.session_state.get("gn_stats", {}) or {}
    
    # If Kafka is enabled, let streaming KPIs drive header
    consumer = st.session_state.get("kpi_consumer")
    if consumer is not None and getattr(consumer, "enabled", False):
        stats = consumer.snapshot() or stats
    
    render_header(stats=stats, mode=engine_mode, base_dir=BASE_DIR)
    
    # ===========================================================
    # 📜 Constitutional values — GLOBAL (always above portals)
    # ===========================================================
    with st.expander("📜 Constitutional values of the GNCE", expanded=True):
        st.caption("Foundational values — constrain all decisions and all portals (L0–L7).")
        st.info("Wire your v0.5 constitutional values cards here (S-Loop / values grid).")
    
    # ===========================================================
    # Clear session (LAB-ONLY, AUTHORITATIVE)
    # ===========================================================
    if clear_clicked:
        if engine_mode != "Lab Mode":
            st.error("Clear Session is disabled in Production Mode.")
            st.stop()
        
        # Clear on-disk ledgers
        clear_runtime_ledgers()
        
        # Clear in-memory session
        st.session_state["current_adra"] = None
        st.session_state["gn_adra_store"] = {}
        st.session_state["sars_ledger"] = []
        st.session_state["gn_stats"] = recompute_session_stats([])
        
        st.rerun()
    
    # ===========================================================
    # Input editor
    # ===========================================================
    if selected_path:
        # Call input_editor once and handle return values flexibly
        result = input_editor(
            selected_path, engine_mode, regulator_mode, edit_before_run
        )
        
        # Handle both 2-value and 3-value returns
        if isinstance(result, tuple):
            if len(result) == 3:
                current_input, valid_json, routing_suggestion = result
            elif len(result) == 2:
                current_input, valid_json = result
                routing_suggestion = None
            else:
                current_input, valid_json = {}, False
                routing_suggestion = None
        else:
            current_input, valid_json = {}, False
            routing_suggestion = None
        
        # Store current input for auto-routing analysis
        if valid_json and current_input:
            st.session_state["current_input_used"] = current_input.copy()
            
            # Store routing suggestion if available
            if routing_suggestion:
                st.session_state["last_routing_suggestion"] = routing_suggestion
    else:
        current_input, valid_json = {}, False
    
    # ===========================================================
    # Run pipeline (kernel call) — one place only
    # ===========================================================
    if run_clicked:
        # Freeze ADRA export intent at execution time
        st.session_state["export_intent"] = bool(st.session_state.get("enable_export_adra", False))
        
        if not valid_json:
            st.error("Input JSON invalid — fix before running.")
        else:
            # Ensure we always have a session id available
            if "session_id" not in st.session_state:
                st.session_state["session_id"] = f"sess-{uuid.uuid4().hex}"
            session_id = st.session_state["session_id"]
            
            payload_name = selected_name if "selected_name" in locals() else None
            
            with st.spinner("Running GNCE..."):
                # Attach jurisdiction hint into payload
                jc = (st.session_state.get("jurisdiction_choice") or "AUTO").upper()
                if jc != "AUTO":
                    current_input.setdefault("meta", {})["jurisdiction"] = jc
                
                # Attach routing keys
                current_input["industry_id"] = st.session_state.get("industry_id") or current_input.get("industry_id")
                current_input["profile_id"] = st.session_state.get("profile_id") or current_input.get("profile_id") or current_input.get("industry_profile_id")
                
                # Store the input for autonomous_loop.py to use
                st.session_state["current_input_used"] = current_input.copy()
                
                if not current_input["industry_id"] or not current_input["profile_id"]:
                    st.error("Missing Industry/Profile routing. Select an Industry and Profile in the sidebar.")
                    st.stop()
                
                # Attach customer profile JSON as OPTIONAL meta
                prof = st.session_state.get("customer_profile")
                if isinstance(prof, dict):
                    meta = current_input.setdefault("meta", {})
                    meta["customer_profile_id"] = prof.get("profile_id") or prof.get("id") or prof.get("name")
                    
                    # Emit a stable reference
                    _cpp = st.session_state.get("customer_profile_path")
                    try:
                        from pathlib import Path as _Path
                        _ref = f"profiles/{_Path(_cpp).name}" if _cpp else None
                    except Exception:
                        _ref = None
                    meta["customer_profile_ref"] = _ref or meta["customer_profile_id"]
                    
                    try:
                        import hashlib as _hashlib
                        meta["customer_profile_hash_sha256"] = "sha256:" + _hashlib.sha256(
                            json.dumps(prof, sort_keys=True, separators=(",", ":")).encode("utf-8")
                        ).hexdigest()
                    except Exception:
                        meta["customer_profile_hash_sha256"] = None
                
                # Preflight route validation
                try:
                    current_input = preflight_route_payload_or_raise(current_input)
                except ValueError as e:
                    st.error(str(e))
                    st.stop()
                
                # Run the kernel
                adra = run_gn_kernel(current_input)
                
                # Export (OPTIONAL)
                export_path_obj = export_adra_if_enabled(adra, ADRA_LOG_DIR)
                if export_path_obj:
                    st.sidebar.success(f"ADRA exported: {export_path_obj.name}")
                    st.toast(f"🧾 ADRA exported to adra_logs/{export_path_obj.name}")
                
                exported = export_path_obj is not None
                export_path = str(export_path_obj) if export_path_obj else None
                export_enabled = bool(st.session_state.get("export_intent", False))
                
                # Build run-event
                evt = build_run_event(
                    adra=adra,
                    session_id=session_id,
                    engine_mode=engine_mode,
                    regulator_view=bool(regulator_mode),
                    federation_enabled=bool(federation_enabled),
                    payload_name=payload_name,
                    export_enabled=export_enabled,
                    exported=exported,
                    export_path=export_path,
                )
                
                # Always append JSONL (local run-event stream)
                append_jsonl(ADRA_LOG_DIR / "run_events.jsonl", evt)
                
                # Optional: publish to Kafka
                kafka_publisher = st.session_state.get("kafka_publisher")
                if kafka_publisher is not None and getattr(kafka_publisher, "enabled", False):
                    try:
                        kafka_publisher.publish(evt.to_dict(), key=evt.adra_id)
                    except Exception as e:
                        st.sidebar.warning(f"Kafka publish failed: {e}")
            
            # Refresh session artifacts
            sovereign_rows = load_session_ledger() or []
            normalized: List[Dict[str, Any]] = []
            for r in sovereign_rows:
                if not isinstance(r, dict):
                    continue
                rec, env = _unwrap_row(r)
                if not isinstance(rec, dict) or not rec:
                    continue
                normalized.append(_normalize(rec, env))
            
            st.session_state["sars_ledger"] = normalized
            st.session_state["current_adra"] = adra
            
            # Store by ADRA ID
            if isinstance(adra, dict):
                adra_id = adra.get("adra_id") or adra.get("ADRA ID")
                if adra_id:
                    st.session_state["gn_adra_store"][str(adra_id)] = adra
            
            # Recompute header stats
            st.session_state["gn_stats"] = recompute_session_stats(normalized)
            
            # Optional federation emit
            if (federation_enabled and emit_adra_if_enabled is not None and 
                fed_cfg is not None and isinstance(adra, dict)):
                try:
                    emit_adra_if_enabled(adra, fed_cfg, True)
                except Exception as e:
                    st.sidebar.warning(f"Federation emit failed: {e}")
            
            st.rerun()
    
    # ===========================================================
    # Data handles for portals
    # ===========================================================
    adra: Dict[str, Any] = st.session_state.get("current_adra") or {}
    active_adra = _get_active_adra(adra, regulator_mode) if isinstance(adra, dict) else {}
    adra_store: Dict[str, Any] = st.session_state.get("gn_adra_store") or {}
    entries: List[Dict[str, Any]] = st.session_state.get("sars_ledger") or []
    
    # ===========================================================
    # Navigation: scalable layout
    # ===========================================================
    st.markdown("""
    <style>
    div[data-baseweb="tab-list"]{
        overflow-x:auto !important;
        overflow-y:hidden !important;
        white-space:nowrap !important;
        scrollbar-width: thin;
    }
    div[data-baseweb="tab-list"] button{
        flex: 0 0 auto !important;
    }
    div[data-baseweb="tab-list"]::-webkit-scrollbar{
        height:6px;
    }
    div[data-baseweb="tab-list"]::-webkit-scrollbar-thumb{
        border-radius:999px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Top-level portals
    engine_portal, admin_portal = st.tabs(["🏛 Engine", "⚙️ Admin Console"])
    
    # -----------------------------
    # Engine tabs
    # -----------------------------
    with engine_portal:
        primary_labels = [
            "🏛 Main Console",
            "🧾 Decision Summary",
            "🏛 Governance Stewardship",
            "🎭 Execution Loop",
            "📊 Executive Summary",
            "⚙️ Governance Oversight Console",
            "📒 SARS Ledger",
            "📚 ADRA Browser",
            "📊 Telemetry",
            "🔬 Forensics",
            "📚 GNCE Constitutional Layers",
            "📚 L4 Explorer",
            "🏛 Domain Catalog",
            "🏛 Governance Catalog",
            "➕ More",
        ]
        
        primary_tabs = st.tabs(primary_labels)
        
        (
            tab_main,
            tab_decision,
            tab_governance_stewardship,
            tab_exec_loop,
            tab_exec_summary,
            tab_ops,
            tab_sars,
            tab_adra,
            tab_telemetry,
            tab_forensics,
            tab_layers,
            tab_l4,
            tab_domain,
            tab_gov_catalog,
            tab_more,
        ) = primary_tabs
        
        # Secondary tabs live UNDER "➕ More"
        with tab_more:
            secondary_labels = [
                "🧭 Regime Vector",
                "📈 Regime KPI Explorer",
                "🔐 CET",
            ]
            secondary_tabs = st.tabs(secondary_labels)
            
            (
                tab_regime_vector,
                tab_regime_kpis,
                tab_cet,
            ) = secondary_tabs
    
    # -----------------------------
    # Admin area (separate)
    # -----------------------------
    with admin_portal:
        admin_labels = [
            "⚙️ Platform Config",
            "🔌 Integrations (Kafka/Webhooks)",
            "🧪 Diagnostics",
        ]
        admin_tabs = st.tabs(admin_labels)
        
        (
            tab_admin_config,
            tab_admin_integrations,
            tab_admin_diag,
        ) = admin_tabs
    
    # ===========================================================
    # 🏛 Main Console
    # ===========================================================
    with tab_main:
        portal_header("🏛 Gordian Nexus Console", "End-to-end surface — request → L0–L7 → verdict → execution eligibility → CET + SARS evidence.")
        if not active_adra:
            st.info("Run GNCE to generate an ADRA. The Main Console will populate with an end-to-end governance snapshot.")
        else:
            # Top KPIs
            c1, c2, c3, c4, c5, c6 = st.columns([1.1, 1.1, 1.3, 1.1, 1.2, 1.9], gap="large")
            
            l1 = active_adra.get("L1_the_verdict_and_constitutional_outcome") or {}
            
            decision = str(
                active_adra.get("decision")
                or active_adra.get("Decision")
                or l1.get("decision_outcome")
                or "—"
            )
            
            severity = str(
                active_adra.get("severity")
                or active_adra.get("Severity")
                or l1.get("severity")
                or "—"
            )
            
            drift = str(
                active_adra.get("drift")
                or active_adra.get("Drift")
                or active_adra.get("drift_outcome")
                or "—"
            )
            
            l7 = active_adra.get("L7_veto_and_execution_feedback") or {}
            
            # Execution eligible
            exec_val = _first_present(
                active_adra.get("execution_authorized"),
                active_adra.get("execution_eligible"),
                active_adra.get("execution_eligible_flag"),
                l7.get("execution_authorized"),
                l7.get("execution_eligible"),
                l7.get("execution_eligible_flag"),
            )
            exec_ok = "—" if exec_val is None else str(bool(exec_val))
            
            # Violations
            l4 = active_adra.get("L4_policy_lineage_and_constitution") or {}
            policies = l4.get("policies_triggered")
            viol_count = None
            if isinstance(policies, list):
                viol_count = sum(1 for p in policies if isinstance(p, dict) and p.get("status") == "VIOLATED")
            
            violations = _first_present(
                viol_count,
                active_adra.get("violations"),
                active_adra.get("Violations"),
                0,
            )
            
            adra_id = str(active_adra.get("adra_id") or active_adra.get("ADRA ID") or "—")
            violated = active_adra.get("violated_articles") or active_adra.get("Violated Articles") or []
            if isinstance(violated, str):
                violated_count = len([x for x in violated.split(",") if x.strip()])
            elif isinstance(violated, list):
                violated_count = len(violated)
            else:
                violated_count = 0
            violated_total = max(int(violations or 0), int(violated_count or 0))
            
            c1.metric("Decision", decision)
            c2.metric("Severity", severity)
            c3.metric("Execution Eligible", exec_ok)
            c4.metric("Drift", drift)
            c5.metric("Violations", str(violated_total))
            c6.metric("ADRA ID", adra_id)
            
            # Pitch-mode export
            pitch_html = build_pitch_snapshot_html(
                active_adra,
                st.session_state.get("gn_stats", {}),
                engine_mode,
            )
            st.download_button(
                "📜 Pitch-mode export (single-slide HTML)",
                data=pitch_html,
                file_name=f"GNCE_pitch_{adra_id}.html",
                mime="text/html",
                use_container_width=True,
                key="pitch_export_main",
            )
            
            st.markdown("---")
            
            # End-to-end GNCE "story"
            left, mid, right = st.columns([1.15, 1.55, 1.3], gap="large")
            
            with left:
                st.markdown("### 🧭 Request → Verdict")
                st.caption("What GNCE observed and concluded at a glance.")
                
                def _extract_reason(adra: dict) -> str:
                    if not isinstance(adra, dict):
                        return ""
                    why = adra.get("why") or adra.get("Why")
                    exp = adra.get("explainability") or {}
                    if not why and isinstance(exp, dict):
                        why = exp.get("summary") or exp.get("headline")
                    l1 = adra.get("L1_the_verdict_and_constitutional_outcome") or adra.get("L1") or {}
                    if not why and isinstance(l1, dict):
                        why = l1.get("rationale") or l1.get("human_readable_outcome") or l1.get("regulator_summary")
                        if not why:
                            because = l1.get("because")
                            if isinstance(because, list) and because:
                                why = "; ".join(str(x) for x in because[:3])
                    l7 = adra.get("L7_veto_and_execution_feedback") or adra.get("L7") or {}
                    if not why and isinstance(l7, dict):
                        cs = l7.get("corrective_signal") or {}
                        if isinstance(cs, dict):
                            why = cs.get("instruction") or cs.get("action_required")
                    return str(why).strip() if why else ""
                
                # CSS for visual semantics
                st.markdown("""
                <style>
                .gnce-kv{margin:0.15rem 0 0.35rem 0; font-size:0.98rem;}
                .gnce-k{color:rgba(255,255,255,0.85); font-weight:600; margin-right:0.35rem;}
                .gnce-pill{display:inline-block; padding:0.12rem 0.5rem; border-radius:999px; font-weight:700;
                           letter-spacing:0.02em; font-size:0.78rem; border:1px solid rgba(255,255,255,0.16);}
                .gnce-pill-good{background:rgba(34,197,94,0.12); color:rgba(134,239,172,0.98); border-color:rgba(34,197,94,0.25);}
                .gnce-pill-bad{background:rgba(239,68,68,0.10); color:rgba(252,165,165,0.98); border-color:rgba(239,68,68,0.25);}
                .gnce-pill-warn{background:rgba(245,158,11,0.10); color:rgba(253,230,138,0.98); border-color:rgba(245,158,11,0.25);}
                .gnce-pill-neutral{background:rgba(148,163,184,0.10); color:rgba(226,232,240,0.92); border-color:rgba(148,163,184,0.22);}
                .gnce-reason{margin:0.25rem 0 0.9rem 0; padding:0.65rem 0.75rem; border-radius:0.75rem;
                             border:1px solid rgba(255,255,255,0.14); font-size:0.92rem; line-height:1.35;}
                .gnce-reason-good{background:rgba(34,197,94,0.08); border-color:rgba(34,197,94,0.20); color:rgba(226,232,240,0.95);}
                .gnce-reason-bad{background:rgba(239,68,68,0.06); border-color:rgba(239,68,68,0.18); color:rgba(226,232,240,0.95);}
                .gnce-reason-warn{background:rgba(245,158,11,0.06); border-color:rgba(245,158,11,0.18); color:rgba(226,232,240,0.95);}
                .gnce-reason-neutral{background:rgba(148,163,184,0.06); border-color:rgba(148,163,184,0.14); color:rgba(226,232,240,0.95);}
                </style>
                """, unsafe_allow_html=True)
                
                def _pill(text, tone="neutral"):
                    tone = (tone or "neutral").lower()
                    cls = {
                        "good": "gnce-pill gnce-pill-good",
                        "bad": "gnce-pill gnce-pill-bad",
                        "warn": "gnce-pill gnce-pill-warn",
                        "neutral": "gnce-pill gnce-pill-neutral",
                    }.get(tone, "gnce-pill gnce-pill-neutral")
                    return f"<span class='{cls}'>{text}</span>"
                
                def _semantic_line(label, value, kind="neutral"):
                    v = str(value) if value is not None else "—"
                    tone = "neutral"
                    if kind == "decision":
                        if v.upper() == "ALLOW":
                            tone = "good"
                        elif v.upper() == "DENY":
                            tone = "bad"
                    elif kind == "severity":
                        if v.upper() in ("LOW", "INFO"):
                            tone = "good"
                        elif v.upper() in ("MEDIUM", "WARNING"):
                            tone = "warn"
                        elif v.upper() in ("HIGH", "CRITICAL"):
                            tone = "bad"
                    elif kind == "bool":
                        tone = "good" if v.lower() in ("true", "yes", "1") else "neutral"
                    return f"<div class='gnce-kv'><span class='gnce-k'>{label}:</span> {_pill(v, tone)}</div>"
                
                def _semantic_reason(reason_text, decision, severity):
                    d = (str(decision or "")).upper()
                    s = (str(severity or "")).upper()
                    tone = "neutral"
                    if d == "ALLOW":
                        tone = "good"
                    elif d == "DENY":
                        tone = "bad"
                    elif s in ("HIGH", "CRITICAL"):
                        tone = "bad"
                    elif s in ("MEDIUM", "WARNING"):
                        tone = "warn"
                    safe = str(reason_text or "").strip()
                    return f"""<div class='gnce-kv'><span class='gnce-k'>Reason:</span></div>
<div class='gnce-reason gnce-reason-{tone}'>{safe}</div>"""
                
                why = _extract_reason(active_adra)
                if not why:
                    why = "Reason not available in this ADRA evidence."
                
                st.markdown(_semantic_line("Verdict", decision or "—", kind="decision"), unsafe_allow_html=True)
                st.markdown(_semantic_line("Severity", severity or "—", kind="severity"), unsafe_allow_html=True)
                st.markdown(_semantic_reason(why, decision, severity), unsafe_allow_html=True)
                
                st.markdown("### 🛡️ Oversight & Veto")
                human_oversight = active_adra.get("human_oversight_required") or active_adra.get("human_oversight") or active_adra.get("Human oversight required")
                if human_oversight is None:
                    human_oversight = False
                veto = active_adra.get("veto_triggered") or active_adra.get("Veto Triggered")
                if veto is None:
                    veto = False
                st.markdown(_semantic_line("Human oversight required", str(human_oversight), kind="bool"), unsafe_allow_html=True)
                st.markdown(_semantic_line("Constitutional veto raised", str(veto), kind="bool"), unsafe_allow_html=True)
            
            with mid:
                st.markdown("### 🧬 Execution Path (Animated)")
                st.caption("L0→L7 runtime trace — visual story of how the verdict was constructed.")
                if active_adra:
                    try:
                        render_execution_flow_graph(active_adra)
                    except Exception as e:
                        st.info("Execution flow graph not available for this ADRA/build.")
                        st.caption(str(e))
                else:
                    st.info("Run GNCE to render the execution path.")
                st.markdown('<div class="gn-card" style="margin-top:10px;">Open <b>Execution Loop</b> for the interactive path visualizer + deeper flow details.</div>', unsafe_allow_html=True)
            
            with right:
                st.markdown("### 🧾 L1 Decision Snapshot")
                st.caption("Compact L1 view (no embedded widgets to avoid key collisions).")
                snapshot_rows = [
                    {"Field": "Decision", "Value": decision or "—"},
                    {"Field": "Severity", "Value": severity or "—"},
                    {"Field": "Execution eligible", "Value": exec_ok or "—"},
                    {"Field": "Drift", "Value": drift or "—"},
                ]
                
                # SARS-ledger synced counts for this ADRA / bundle
                def _as_list(x):
                    if x is None:
                        return []
                    if isinstance(x, list):
                        return [str(i).strip() for i in x if i not in (None, "", "—")]
                    if isinstance(x, str):
                        parts = [p.strip() for p in x.split(",")]
                        return [p for p in parts if p and p != "—"]
                    return [str(x).strip()]
                
                def _get_bundle_id(adra_obj):
                    if not isinstance(adra_obj, dict):
                        return None
                    for k in ("decision_bundle_id", "bundle_id", "decisionBundleId"):
                        v = adra_obj.get(k)
                        if v:
                            return v
                    gc = adra_obj.get("governance_context")
                    if isinstance(gc, dict) and gc.get("decision_bundle_id"):
                        return gc.get("decision_bundle_id")
                    l7 = adra_obj.get("L7_veto_and_execution_feedback") or {}
                    gc2 = l7.get("governance_context") if isinstance(l7, dict) else None
                    if isinstance(gc2, dict) and gc2.get("decision_bundle_id"):
                        return gc2.get("decision_bundle_id")
                    return None
                
                current_bundle_id = _get_bundle_id(adra) if isinstance(adra, dict) else None
                current_adra_id = adra.get("adra_id") if isinstance(adra, dict) else None
                
                def _row_bundle_id(row):
                    if not isinstance(row, dict):
                        return None
                    if row.get("decision_bundle_id"):
                        return row.get("decision_bundle_id")
                    raw = row.get("_raw")
                    if isinstance(raw, dict) and raw.get("decision_bundle_id"):
                        return raw.get("decision_bundle_id")
                    return None
                
                def _rows_for_snapshot(all_rows):
                    if not isinstance(all_rows, list):
                        return []
                    out = []
                    for r in all_rows:
                        if not isinstance(r, dict):
                            continue
                        if current_bundle_id and _row_bundle_id(r) == current_bundle_id:
                            out.append(r)
                            continue
                        if current_adra_id and r.get("adra_id") == current_adra_id:
                            out.append(r)
                            continue
                        raw = r.get("_raw")
                        if current_adra_id and isinstance(raw, dict) and raw.get("adra_id") == current_adra_id:
                            out.append(r)
                    return out
                
                snap_ledger_rows = _rows_for_snapshot(entries)
                
                violated_articles = set()
                all_obligations = set()
                
                for r in snap_ledger_rows:
                    violated_articles.update(_as_list(r.get("violated_articles")))
                    all_obligations.update(_as_list(r.get("articles_all")))
                    
                    raw = r.get("_raw") if isinstance(r, dict) else None
                    if isinstance(raw, dict):
                        violated_articles.update(_as_list(raw.get("violated_articles")))
                        all_obligations.update(_as_list(raw.get("articles_all")))
                        
                        env = raw.get("_envelope")
                        if isinstance(env, dict):
                            violated_articles.update(_as_list(env.get("violated_articles")))
                            all_obligations.update(_as_list(env.get("articles_all")))
                
                violated_count = len(violated_articles)
                if all_obligations:
                    allowed_count = max(len(all_obligations - violated_articles), 0)
                else:
                    l1 = adra.get("L1_the_verdict_and_constitutional_outcome") if isinstance(adra, dict) else None
                    summ = l1.get("summary") if isinstance(l1, dict) else {}
                    allowed_count = int(summ.get("satisfied") or 0)
                
                violated_list_disp = ", ".join(sorted(violated_articles)) if violated_articles else "—"
                
                snapshot_rows.extend([
                    {"Field": "Violated articles (count)", "Value": violated_count},
                    {"Field": "Allowed obligations (count)", "Value": allowed_count},
                    {"Field": "Violated articles", "Value": violated_list_disp},
                ])
                
                st.dataframe(snapshot_rows, use_container_width=True, hide_index=True)
                
                st.markdown("### 🔐 CET + SARS Evidence")
                st.caption("Proof artifacts bound to this decision.")
                
                def _extract_cet(adra: dict):
                    if not isinstance(adra, dict):
                        return None
                    
                    for k in ("cet", "CET"):
                        v = adra.get(k)
                        if isinstance(v, dict) and v:
                            return v
                    
                    for k in ("L5_integrity_and_tokenization", "L5"):
                        v = adra.get(k)
                        if isinstance(v, dict) and v:
                            nested = v.get("CET")
                            if isinstance(nested, dict) and nested:
                                return nested
                            
                            if any(v.get(x) for x in ("content_hash_sha256", "pseudo_signature_sha256", "nonce", "signing_strategy", "content_hash")):
                                return v
                    
                    return None
                
                cet_obj = _extract_cet(active_adra)
                has_cet = bool(cet_obj)
                
                st.markdown(f"• **CET:** `{'PRESENT' if has_cet else 'MISSING'}`")
                if has_cet:
                    ch = cet_obj.get("content_hash_sha256") or cet_obj.get("content_hash") or "—"
                    sig = cet_obj.get("pseudo_signature_sha256") or cet_obj.get("signature_sha256") or "—"
                    st.caption(f"content_hash={str(ch)[:32]}… | signature={str(sig)[:32]}…")
                
                st.markdown(f"• **SARS entries (session):** `{len(entries)}`")
            
            # 🔎 Next steps — ACTIVE deep links
            st.markdown("### 🔎 ")
            st.caption("Jump directly into regulator-grade evidence and governance views.")
            
            col1, col2, col3, col4 = st.columns(4, gap="large")
            
            with col1:
                if st.button("📚 Layers (L0–L7)\nEvidence & traceability", use_container_width=True):
                    st.session_state["return_to"] = "Main Console"
                    st.session_state["return_adra_id"] = adra_id
                    st.session_state["layers_target_adra"] = adra_id
                    st.session_state["layers_focus"] = "full_trace"
                    st.session_state["gn_jump_tab"] = "📚 ADRA Browser"
                    st.toast("📚 Jump set — open the **📚 ADRA Browser** tab above.")
                    st.rerun()
            
            with col2:
                if st.button("📒 SARS Ledger\nSovereign evidence index", use_container_width=True):
                    st.session_state["return_to"] = "Main Console"
                    st.session_state["return_adra_id"] = adra_id
                    st.session_state["sars_filter_adra"] = adra_id
                    st.session_state["sars_auto_expand"] = True
                    st.session_state["gn_jump_tab"] = "📒 SARS Ledger"
                    st.toast("🏛 Jump set — open the **📒 SARS Ledger** tab above.")
                    st.rerun()
            
            with col3:
                if st.button("⚙️ Governance Oversight Console \nRegulator-grade health view", use_container_width=True):
                    st.session_state["return_to"] = "Main Console"
                    st.session_state["return_adra_id"] = adra_id
                    st.session_state["ops_focus_adra"] = adra_id
                    st.session_state["ops_view"] = "decision_health"
                    st.session_state["gn_jump_tab"] = "⚙️ Governance Oversight Console "
                    st.toast("⚙️ Jump set — open the **⚙️ Governance Oversight Console ** tab above.")
                    st.rerun()
            
            with col4:
                if st.button("🔬 Forensics\nIntegrity & verification checks", use_container_width=True):
                    st.session_state["return_to"] = "Main Console"
                    st.session_state["return_adra_id"] = adra_id
                    st.session_state["forensics_target_adra"] = adra_id
                    st.session_state["forensics_mode"] = "verify"
                    st.session_state["gn_jump_tab"] = "🔬 Forensics"
                    st.toast("🔬 Jump set — open the **🔬 Forensics** tab above.")
                    st.rerun()
    
    # ===========================================================
    # 🧾 Decision Summary
    # ===========================================================
    with tab_decision:
        portal_header("🧾 Decision Summary", "L1 verdict surface — concise and regulator-readable.")
        if active_adra:
            render_decision_summary(active_adra, key_prefix="decision_tab")
        else:
            st.info("Run GNCE to generate an ADRA.")
    
    # ===========================================================
    # 🏛 GNCE Governance (Stewardship)
    # ===========================================================
    with tab_governance_stewardship:
        portal_header("🏛 Governance Stewardship", "Owners, custodians, chain-of-custody, exports.")
        if active_adra:
            render_governance_stewardship(active_adra, key_prefix="gov_stewardship")
        else:
            st.info("No active ADRA. Run GNCE first.")
    
    # ===========================================================
    # 🎭 Execution Loop
    # ===========================================================
    with tab_exec_loop:
        portal_header("🎭 Autonomous Execution Loop", "Requester → GNCE → Actuator")
        if adra:
            render_autonomous_execution_loop(adra)
            st.markdown("---")
            render_execution_path_visualizer(active_adra)
            render_execution_flow_graph(active_adra)
        else:
            st.info("Run GNCE to generate an ADRA.")
    
    # ===========================================================
    # 📊 Executive Summary
    # ===========================================================
    with tab_exec_summary:
        portal_header("📊 GNCE Executive summary", "Windowed session summary and governance KPIs.")
        
        if render_executive_summary is None:
            st.warning("Executive summary dashboard component not available in this build.")
        elif render_time_window_selector is None:
            st.warning("Time window selector not available for executive summary.")
        else:
            if entries:
                window_ledger, window_ids, window_label = render_time_window_selector(entries)
                render_executive_summary(
                    ledger=entries,
                    adra_store=adra_store,
                    window_adra_ids=window_ids,
                    window_label=window_label,
                    key_prefix="exec_summary_tab"
                )
            else:
                st.info("No ledger entries. Run GNCE first.")
    
    # ===========================================================
    # ⚙️ Governance Oversight Console (Block M)
    # ===========================================================
    with tab_ops:
        portal_header("⚙️ GNCE Governance Oversight Console", "Block M — sovereign read-only observatory.")
        render_operations_governance_console(load_session_ledger() or [])
    
    # ===========================================================
    # 📒 SARS Ledger
    # ===========================================================
    with tab_sars:
        if st.session_state.get("gn_jump_tab") == "📒 SARS Ledger":
            st.session_state["gn_jump_tab"] = None
            st.toast("📒 SARS Ledger opened.", icon="✅")
        portal_header("📒 SARS Ledger", "Sovereign evidence ledger (read-only).")
        render_sars_ledger(entries, adra_store)
    
    # ===========================================================
    # 📚 ADRA Browser
    # ===========================================================
    with tab_adra:
        portal_header("📚 ADRA Browser", "Browse ADRAs and export evidence artifacts.")
        render_adra_browser_panel()
    
    # ===========================================================
    # 📊 Telemetry
    # ===========================================================
    with tab_telemetry:
        portal_header("📊 GNCE Telemetry Dashboards", "Telemetry, drift surveillance, and session analytics.")
        
        if render_gnce_telemetry_v07 is not None:
            if entries:
                render_gnce_telemetry_v07(entries)
            else:
                st.info("No ledger entries. Run GNCE first.")
        elif render_time_window_selector is not None and render_operations_console is not None:
            if entries:
                default_ids = [
                    (r.get("ADRA ID") or r.get("adra_id") or r.get("adraId"))
                    for r in entries
                    if (r.get("ADRA ID") or r.get("adra_id") or r.get("adraId"))
                ]
                
                window_ledger, window_ids, window_label = st.session_state.get(
                    "gn_window_selection",
                    (entries, default_ids, "Entire session")
                )
                render_operations_console(window_ledger, window_label)
            else:
                st.info("No ledger entries. Run GNCE first.")
        else:
            st.warning("Telemetry dashboard component not available in this build.")
    
    # ===========================================================
    # 🔬 Forensics
    # ===========================================================
    with tab_forensics:
        portal_header("🔬 GNCE Forensic Inspector", "Integrity, hash-chain, and evidence validation.")
        if adra:
            render_forensic_inspector(active_adra, adra_store)
        else:
            st.info("Run GNCE to generate an ADRA.")
    
    # ===========================================================
    # 📚 GNCE Constitutional Layers (L0–L7)
    # ===========================================================
    with tab_layers:
        portal_header("📚 GNCE Constitutional Layers", "Deep dive into L0–L7 evidence.")
        
        if active_adra:
            try:
                render_constitutional_layers(active_adra, regulator_mode=regulator_mode, focus_layer="L1")
            except TypeError:
                render_constitutional_layers(active_adra)
        else:
            st.info("Run GNCE to generate an ADRA.")
    
    # ===========================================================
    # 📚 L4 Explorer
    # ===========================================================
    with tab_l4:
        portal_header("📚 L4 domain compliance explorer", "Explore compliance findings by domain (L4).")
        if active_adra:
            render_domain_explorer(active_adra)
        else:
            st.info("Run GNCE to generate an ADRA.")
    
    # ===========================================================
    # 🏛 Domain Catalog
    # ===========================================================
    with tab_domain:
        portal_header("🏛 Constitutional Domain Catalog", "Domains and constitutional scope mapping.")
        if active_adra:
            render_domain_catalog(
                active_adra,
                adra_store=st.session_state.get("gn_adra_store", {}) or {},
                sars_ledger=st.session_state.get("sars_ledger", []) or [],
            )
        else:
            st.info("Run GNCE to load domain context.")
    
    # ===========================================================
    # 🏛 Governance Catalog
    # ===========================================================
    with tab_gov_catalog:
        portal_header("🏛 Unified Governance Catalog", "Unified view of governance objects and authorities.")
        render_governance_catalog_v05()
    
    # ===========================================================
    # ⚙️ Admin Config
    # ===========================================================
    with tab_admin_config:
        portal_header("⚙️ Admin Console", "Configs, payload editor, and environment toggles.")
        st.info("Payload selection and edit controls are on the left sidebar. Add constitution/regime refresh actions here.")
    
    # ===========================================================
    # 🧭 Regime Vector
    # ===========================================================
    with tab_regime_vector:
        portal_header("🧭 Regime Vector and Articles Coverage", "Coverage and outcome vector across triggered regimes.")
        if active_adra:
            render_regime_outcome_vector(active_adra)
            st.markdown("---")
            try:
                render_l4_regimes(adra)
            except Exception:
                pass
        else:
            st.info("Run GNCE to generate an ADRA.")
    
    # ===========================================================
    # 📈 Regime KPI Explorer
    # ===========================================================
    with tab_regime_kpis:
        portal_header("📈 Regime KPI Explorer", "Per-regime run KPIs (ALLOW/DENY/violations) from run-events stream.")
        try:
            from gnce.ui.components.regime_kpi_explorer import render_regime_kpi_explorer
            render_regime_kpi_explorer(run_events_path=(ADRA_LOG_DIR / "run_events.jsonl"))
        except Exception as e:
            st.warning(f"Regime KPI Explorer component not available: {e}")
    
    # ===========================================================
    # 🔐 CET
    # ===========================================================
    with tab_cet:
        portal_header("🔐 GNCE Cryptographic Execution Token (CET)", "Immutable cryptographic evidence token bound to the selected ADRA.")
        if not active_adra:
            st.info("Run GNCE to generate an ADRA, then view the CET.")
        else:
            try:
                from gnce.ui.components.cet_panel import render_cet_panel
                render_cet_panel(active_adra)
            except Exception:
                cet = None
                if isinstance(active_adra, dict):
                    cet = active_adra.get("cet") or active_adra.get("CET") or active_adra.get("L5_integrity_and_tokenization", {}).get("CET")
                if cet:
                    st.json(cet)
                else:
                    st.warning("CET panel/component not found, and no CET object present on this ADRA.")
    
    # ===========================================================
    # 🔌 Integrations
    # ===========================================================
    with tab_admin_integrations:
        portal_header("🔌 Integrations (Kafka/Webhooks)", "Configure external system integrations.")
        st.info("Integration configuration panel")
    
    # ===========================================================
    # 🧪 Diagnostics
    # ===========================================================
    with tab_admin_diag:
        portal_header("🧪 Diagnostics", "System health checks and diagnostic tools.")
        st.info("Diagnostic tools panel")


if __name__ == "__main__":
    main()