# gnce/ledger/ledger.py
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
import os
import hashlib

# ===============================================================
# Paths (authoritative, kernel-safe)
# ===============================================================

REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER_DIR = REPO_ROOT / "adra_logs"
LEDGER_DIR.mkdir(exist_ok=True)

SESSION_LEDGER_PATH = LEDGER_DIR / "sars_session_ledger.jsonl"
ARTICLE_LEDGER_PATH = LEDGER_DIR / "sars_article_ledger.jsonl"

# ===============================================================
# Utilities
# ===============================================================

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _write_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, default=str) + "\n")

def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows

def _sha256_canonical_adra(adra: Dict[str, Any]) -> str:
    """Defensive fallback: compute canonical ADRA hash if kernel did not provide one.

    Excludes the `adra_hash` field itself.
    """
    canon = dict(adra or {})
    canon.pop("adra_hash", None)
    data = json.dumps(canon, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def load_session_ledger(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Public UI/kernel-safe reader for the SARS session ledger (JSONL).
    """
    return _read_jsonl(path or SESSION_LEDGER_PATH)


def load_article_ledger(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Public UI/kernel-safe reader for the SARS article ledger (JSONL).
    """
    return _read_jsonl(path or ARTICLE_LEDGER_PATH)


def _get(adra: Dict[str, Any], *keys: str) -> Dict[str, Any]:
    """Return first dict-like match for any of the keys."""
    for k in keys:
        v = adra.get(k)
        if isinstance(v, dict):
            return v
    return {}

def _ledger_strict_mode() -> bool:
    """
    Strict mode (production): fail fast when compliance fields are missing.
    Non-strict mode (lab/dev): write entry but mark NON_COMPLIANT with errors.
    Toggle with env var:
      GNCE_LEDGER_STRICT=1  (default)  -> raise ValueError
      GNCE_LEDGER_STRICT=0            -> do not raise, mark non-compliant
    """
    return os.getenv("GNCE_LEDGER_STRICT", "1").strip() != "0"


def _enforce_session_row_contract(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enforce regulator-grade session ledger contract.

    Requires:
      - constitution_hash (always)
      - If verdict == DENY:
          - veto_layer required
          - veto_clause required OR explicitly set to "UNSPECIFIED"

    Behavior:
      - strict mode: raise ValueError on missing fields
      - non-strict: annotate row with compliance info and continue
    """
    strict = _ledger_strict_mode()

    verdict = str(row.get("verdict") or "UNKNOWN").upper().strip()
    errors: List[str] = []

    # 1) constitution_hash is mandatory
    if not row.get("constitution_hash"):
        errors.append("missing:constitution_hash")

    # 2) DENY requires veto attribution
    if verdict == "DENY":
        if not row.get("veto_layer"):
            errors.append("missing:veto_layer_on_deny")

        # clause must exist, or must be explicitly UNSPECIFIED
        clause = row.get("veto_clause")
        if clause is None or str(clause).strip() == "":
            # You said: "Require clause or explicit clause='UNSPECIFIED'"
            # So: in non-strict we auto-set UNSPECIFIED but still flag it.
            row["veto_clause"] = "UNSPECIFIED"
            errors.append("missing:veto_clause_set_unspecified")

    if errors:
        row["compliance_status"] = "NON_COMPLIANT"
        row["compliance_errors"] = errors

        if strict:
            raise ValueError(f"Session ledger contract violation: {errors}")
    else:
        row["compliance_status"] = "COMPLIANT"
        row["compliance_errors"] = []

    return row


# ===============================================================
# ADRA → SESSION LEDGER ROW (GNCE v0.7.0)
#   IMPORTANT: this must match kernel v0.7.0 output keys.
# ===============================================================

def build_adra_ledger_row(adra: Dict[str, Any]) -> Dict[str, Any]:
    """
    Authoritative SARS ADRA-level ledger row.

    This row MUST satisfy the Layer-1 "Evidence Index" contract:
      - adra_id
      - time (UTC)
      - verdict (ALLOW/DENY)
      - severity
      - drift
      - veto_triggered
      - articles_count
      - adra_hash
      - articles_all
      - violated_articles

    And it MUST carry the full envelope for Layer-2 drill-down:
      - _envelope (full ADRA)
    """
    # ----------------------------
    # Bundle support (per-regime)
    # ----------------------------
    # Kernel may pass a bundle dict with `regime_adrAs` (one ADRA envelope per regime).
    # If so, expand into one session row per regime envelope.
    if isinstance(adra, dict) and isinstance(adra.get("regime_adrAs"), list):
        rows: List[Dict[str, Any]] = []
        for item in adra.get("regime_adrAs") or []:
            if isinstance(item, dict):
                rows.append(build_adra_ledger_row(item))  # type: ignore[arg-type]
        return rows  # type: ignore[return-value]

    # --- Correct canonical layer keys (match kernel.py) ---
    l0 = _get(adra, "L0_pre_execution_validation") or {}
    l1 = _get(adra, "L1_the_verdict_and_constitutional_outcome") or {}
    l3 = _get(adra, "L3_rule_level_trace") or {}
    l4 = _get(adra, "L4_policy_lineage_and_constitution") or {}
    l6 = _get(adra, "L6_behavioral_drift_and_monitoring") or {}
    l7 = _get(adra, "L7_veto_and_execution_feedback") or {}
    
    # --- Constitution hash (authoritative anchor for Block M) ---
    # Your ADRA currently does NOT emit a dedicated constitution_hash,
    # but it DOES emit a stable integrity hash in L5. We promote it.
    l5 = _get(adra, "L5", "L5_integrity_and_tokenization", "L5_constitutional_materialization") or {}
    constitution_hash = (
        adra.get("constitution_hash")
        or l4.get("constitution_hash")
        or l5.get("content_hash_sha256")
        or (l5.get("evidence", {}) or {}).get("content_hash_sha256")
    )

    # --- Canonical timestamp (single source of truth) ---
    ts = (
        adra.get("timestamp_utc")
        or l1.get("timestamp_utc")
        or (adra.get("provenance", {}) or {}).get("received_at_utc")
        or _utc_now_iso()
    )
    if hasattr(ts, "isoformat"):
        ts = ts.isoformat()

    # --- Verdict + severity (canonical) ---
    verdict = str(l1.get("decision_outcome") or "UNKNOWN").upper().strip()
    if verdict not in {"ALLOW", "DENY"}:
        verdict = "UNKNOWN"

    severity = str(l1.get("severity") or "UNKNOWN").upper().strip() or "UNKNOWN"

    # --- Drift + veto (canonical) ---
    drift = str(l6.get("drift_outcome") or "NO_DRIFT").upper().strip()
    veto_triggered = bool(l7.get("veto_path_triggered") or l7.get("veto_triggered"))
    execution_authorized = bool(l7.get("execution_authorized"))

    # --- Veto attribution (Loop 5.3) ---
    # ✅ EXTRACT FROM L7 FIRST (authoritative source)
    veto_layer = l7.get("veto_layer") or l7.get("origin_layer") or l7.get("trigger_layer")
    veto_clause = l7.get("clause") or l7.get("constitutional_clause")
    veto_article = None

    # Fallback to veto_basis if L7 doesn't have them
    veto_basis = l7.get("veto_basis") or []
    if not isinstance(veto_basis, list):
        veto_basis = []

    if veto_basis and isinstance(veto_basis[0], dict):
        vb0 = veto_basis[0]
        if not veto_layer:
            veto_layer = vb0.get("origin_layer") or vb0.get("layer") or "L7"
        if not veto_clause:
            veto_article = vb0.get("article")
            veto_clause = vb0.get("constitutional_clause") or veto_article

    # ✅ ENSURE DEFAULTS FOR DENY
    if veto_triggered:
        if not veto_layer:
            veto_layer = "L7"
        if not veto_clause:
            veto_clause = "UNSPECIFIED"

    # --- Policies → articles (canonical) ---
    policies = l4.get("policies_triggered") or []
    if not isinstance(policies, list):
        policies = []

    articles_all = [p.get("article") for p in policies if isinstance(p, dict) and p.get("article")]
    violated_articles = [
        p.get("article")
        for p in policies
        if isinstance(p, dict)
        and p.get("article")
        and str(p.get("status", "")).upper().strip() == "VIOLATED"
    ]

    # de-dupe while preserving order
    seen = set()
    articles_all_deduped = []
    for a in articles_all:
        if a and a not in seen:
            seen.add(a)
            articles_all_deduped.append(a)

    articles_count = len(articles_all_deduped)

    # --- Regime (canonical) ---
    governance_context = adra.get("governance_context") if isinstance(adra, dict) else {}
    if not isinstance(governance_context, dict):
        governance_context = {}
    derived_regime = (
        adra.get("regime")
        or governance_context.get("regime_id")
        or governance_context.get("regime")
        or (governance_context.get("scope_enabled_regimes") or [None])[0]
        or ""
    )

    # --- Hash (canonical) ---
    adra_hash = adra.get("adra_hash") or _sha256_canonical_adra(adra)

    # ✅ Minimal stable keys (what sars_ledger_view MUST read)
    row = {
        "adra_id": adra.get("adra_id"),
        "decision_bundle_id": adra.get("decision_bundle_id"),
        "regime": derived_regime,
        "time": ts,
        "verdict": verdict,
        "constitution_hash": constitution_hash,
        "veto_layer": veto_layer,
        "veto_clause": veto_clause,
        "veto_article": veto_article,
        "severity": severity,
        "drift": drift,
        "veto_triggered": veto_triggered,
        "execution_authorized": execution_authorized,
        "articles_count": articles_count,
        "adra_hash": adra_hash,
        "articles_all": articles_all_deduped,
        "violated_articles": violated_articles,
        # ✅ Full envelope for Layer-2/3 drill-down
        "_envelope": dict(adra),
    }

    # (Optional) Keep UI-friendly aliases if you still want them elsewhere:
    row.update(
        {
            "ADRA ID": row["adra_id"],
            "Timestamp (UTC)": ts,
            "Decision": verdict,
            "Severity": severity,
            "Drift": drift,
            "Veto Triggered": "YES" if veto_triggered else "NO",
            "Articles (all)": articles_all_deduped,
            "Violated Articles": violated_articles,
            "ADRA Hash": adra_hash,
        }
    )

    return row

# ===============================================================
# ARTICLE SUB-LEDGER (per policy/article)
# ===============================================================

def build_article_ledger_rows(adra: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    One row per policy obligation (preferred: L4.policies_triggered),
    fallback to L3.causal_trace if needed.
    """
    l1 = _get(adra, "L1_the_verdict_and_constitutional_outcome")
    l3 = _get(adra, "L3_rule_level_trace", "L3_rule_evaluation_trace", "L3")
    l4 = _get(adra, "L4_policy_lineage_and_constitution", "L4")

    ts = (
        adra.get("timestamp_utc")
        or l1.get("timestamp_utc")
        or (adra.get("provenance", {}) or {}).get("received_at_utc")
        or _utc_now_iso()
    )

    adra_id = adra.get("adra_id") or "UNKNOWN"
    adra_hash = adra.get("adra_hash")

    rows: List[Dict[str, Any]] = []

    policies = l4.get("policies_triggered") or []
    if isinstance(policies, list) and policies:
        for p in policies:
            if not isinstance(p, dict):
                continue
            rows.append(
                {
                    "timestamp_utc": ts,
                    "adra_id": adra_id,
                    "adra_hash": adra_hash,
                    "regime": p.get("regime") or p.get("domain") or "",
                    "article": p.get("article") or "",
                    "article_status": p.get("status") or "UNKNOWN",
                    "article_severity": p.get("severity") or "",
                    "rule_ids": p.get("rule_ids") or [],
                    "why_triggered": p.get("why_triggered") or p.get("notes") or p.get("rationale") or "",
                }
            )
        return rows

    # fallback: L3 causal trace
    causal = l3.get("causal_trace") or []
    if isinstance(causal, list):
        for c in causal:
            if not isinstance(c, dict):
                continue
            rows.append(
                {
                    "timestamp_utc": ts,
                    "adra_id": adra_id,
                    "adra_hash": adra_hash,
                    "regime": "",
                    "article": c.get("article") or "",
                    "article_status": c.get("status") or "UNKNOWN",
                    "article_severity": c.get("severity") or "",
                    "rule_ids": c.get("rule_ids") or [],
                    "why_triggered": c.get("why_triggered") or "",
                }
            )
    return rows

# ===============================================================
# LEDGER WRITE API (KERNEL ONLY)
# ===============================================================

def append_to_session_ledger(row: Union[Dict[str, Any], List[Dict[str, Any]]]) -> None:
    if isinstance(row, list):
        for r in row:
            append_to_session_ledger(r)
        return

    # Enforce regulator-grade contract right before write
    row = _enforce_session_row_contract(row)

    envelope = {
        "record": row,
        "written_at_utc": _utc_now_iso(),
        "schema_version": "GNCE_LEDGER_v0.7.0",
    }
    _write_jsonl(SESSION_LEDGER_PATH, envelope)


def append_to_article_ledger(row_or_rows: Union[Dict[str, Any], List[Dict[str, Any]]]) -> None:
    if isinstance(row_or_rows, list):
        for r in row_or_rows:
            append_to_article_ledger(r)
        return

    envelope = {
        "record": row_or_rows,
        "written_at_utc": _utc_now_iso(),
        "schema_version": "GNCE_ARTICLE_LEDGER_v0.7.0",
    }
    _write_jsonl(ARTICLE_LEDGER_PATH, envelope)

# ===============================================================
# READ API (UI)
# ===============================================================

def read_session_ledger(last_n: Optional[int] = None) -> List[Dict[str, Any]]:
    rows = _read_jsonl(SESSION_LEDGER_PATH)
    return rows[-last_n:] if isinstance(last_n, int) and last_n > 0 else rows

def read_article_ledger(last_n: Optional[int] = None) -> List[Dict[str, Any]]:
    rows = _read_jsonl(ARTICLE_LEDGER_PATH)
    return rows[-last_n:] if isinstance(last_n, int) and last_n > 0 else rows
