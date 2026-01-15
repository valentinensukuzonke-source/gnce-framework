# gnce/kernel/exporter.py
"""
GNCE v0.5 — ADRA Export Module (Mixed Pretty/Compact Mode)
----------------------------------------------------------

This module writes ADRA artifacts to disk using the mixed-format
structure chosen by the governance architect:

    • Pretty-print: L4, L6, L7    ← Legal/audit review layers
    • Compact/minified: L0–L3, L5 ← Operational layers

Output folder: ./adra_logs/
Filename: adra-<adra_id>-<timestamp>.json
"""

from __future__ import annotations
import os
import json
from datetime import datetime, timezone
from typing import Dict, Any

from .models.adra_v05 import validate_adra_v05

# ============================================================
#  Paths & Setup
# ============================================================

EXPORT_DIR = "./adra_logs"


def _ensure_directory():
    """Create folder if missing."""
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR, exist_ok=True)


def _timestamp() -> str:
    """Return safe timestamp for filenames."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


# ============================================================
#  Layer export format logic
# ============================================================

PRETTY_LAYERS = {
    "L4_policy_lineage_and_constitution",
    "L6_behavioral_drift_and_monitoring",
    "L7_veto_and_execution_feedback",
}

COMPACT_LAYERS = {
    "L0_pre_execution_validation",
    "L1_the_verdict_and_constitutional_outcome",
    "L2_input_snapshot_and_dra",
    "L3_rule_level_trace",
    "L5_integrity_and_tokenization",
}


def _mixed_format_transform(adra: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reconstructs the ADRA for export:
      - pretty layers stay nested dicts (unmodified)
      - compact layers become minified JSON
    """

    export_adra = {}

    for key, value in adra.items():
        if key in PRETTY_LAYERS:
            export_adra[key] = value  # as-is, pretty-printed later
        elif key in COMPACT_LAYERS:
            # Compact format (minified)
            try:
                export_adra[key] = json.loads(
                    json.dumps(value, separators=(",", ":"), sort_keys=True)
                )
            except Exception:
                export_adra[key] = value
        else:
            # Keep other fields default
            export_adra[key] = value

    return export_adra


# ============================================================
#  Main Export Function
# ============================================================

def export_adra(adra: Dict[str, Any], enable: bool = False) -> str | None:
    if not enable:
        return None

    _ensure_directory()

    # ---- v0.5 schema validation (non-blocking) ----
    if not adra.get("finalized", False):
        raise RuntimeError("Refusing to export: ADRA is not finalized.")

    is_valid, errors = validate_adra_v05(adra)


    # IMPORTANT: never mutate the ADRA (immutability barrier)
    export_blob = dict(adra)  # shallow copy is fine for top-level annotations
    export_blob["_schema_valid"] = is_valid
    if not is_valid:
        export_blob["_schema_errors"] = errors

    adra_id = adra.get("adra_id", "unknown")
    ts = _timestamp()
    filename = f"adra-{adra_id}-{ts}.json"
    path = os.path.join(EXPORT_DIR, filename)

    # Build mixed-format ADRA FROM THE EXPORT BLOB (not the ADRA)
    export_payload = _mixed_format_transform(export_blob)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(export_payload, f, indent=2, ensure_ascii=False)

    return path

