# gnce/gn_kernel/adra/canonical.py
"""Canonical Evidence Envelope (CEE v1)

Purpose:
- Normalize key evidence fields so *all* downstream tooling (SARS ledger, Ops console)
  can reliably compute verdict counts, drift/veto engagement, and traceability KPIs.
- Keep the original ADRA payload intact; we only add/normalize fields.

This module should NOT run policy logic. It only canonicalizes / hashes evidence.
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _sha256_json(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_canonical_adra(adra: Dict[str, Any]) -> Dict[str, Any]:
    """Return the same ADRA dict with canonical evidence fields populated.

    Canonical fields (top-level):
      - cee_version: str
      - timestamp_utc: ISO8601 UTC timestamp
      - constitution_hash: sha256 of constitution (if present)
      - final_verdict: "ALLOW" | "DENY" | "UNKNOWN"
      - decision: alias of final_verdict (for older UI code)
      - severity: best-effort severity string
      - envelope_hash_sha256: sha256 of the full envelope (excluding the hash field itself)
    """

    # ---- Version ----
    adra.setdefault("cee_version", "GNCE_CEE_v1")

    # ---- Timestamp ----
    # Many UIs treat missing timestamp as "0% timeline coverage"
    adra.setdefault("timestamp_utc", _utc_now_iso())

    # ---- Constitution hash ----
    constitution = (
        adra.get("constitution")
        or adra.get("L0_constitution")
        or adra.get("L0", {}).get("constitution")
        or None
    )
    if constitution is not None:
        adra.setdefault("constitution_hash", _sha256_json(constitution))

    # ---- Final verdict ----
    l7 = adra.get("L7_veto_and_execution_feedback") or adra.get("L7_veto_and_execution_feedback".lower()) or {}
    l1 = adra.get("L1_the_verdict_and_constitutional_outcome") or {}

    # L7 is the execution gate: if it vetoes, the final verdict must be DENY for run-ledger/accountability.
    veto_triggered = bool(l7.get("veto_path_triggered")) or (l7.get("execution_authorized") is False)
    l1_decision = (l1.get("decision_outcome") or l1.get("decision") or adra.get("decision") or "UNKNOWN")
    l1_decision = str(l1_decision).upper()

    final_verdict = "DENY" if veto_triggered else ("ALLOW" if l1_decision == "ALLOW" else l1_decision)
    if final_verdict not in {"ALLOW", "DENY"}:
        final_verdict = "UNKNOWN"

    adra["final_verdict"] = final_verdict
    # Back-compat for existing tables / filters
    adra["decision"] = final_verdict

    # ---- Severity ----
    severity = (
        l1.get("severity")
        or adra.get("severity")
        or (l7.get("severity") if isinstance(l7, dict) else None)
        or "N/A"
    )
    adra["severity"] = str(severity)

    # ---- Envelope hash ----
    # Hash should be stable and not self-referential.
    to_hash = dict(adra)
    to_hash.pop("envelope_hash_sha256", None)
    adra["envelope_hash_sha256"] = _sha256_json(to_hash)

    return adra
