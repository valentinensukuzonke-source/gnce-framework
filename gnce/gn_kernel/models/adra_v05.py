# ============================================================
#  GNCE v0.5 — ADRA SCHEMA (Authoritative Specification)
# ============================================================
# This module defines the standard structure of an Auditable Decision
# Rationale Artifact (ADRA) for GNCE v0.5 and provides lightweight
# validation utilities.
#
# Design goals:
#   - Kernel layers (L0–L7) populate this structure without changing shape.
#   - Validation is structural (not semantic) and safe to run everywhere.
#   - v0.4 compatibility: missing optional fields can be None/empty.
#
# Path: gnce/gn_kernel/models/adra_v05.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from ..contracts import GNCE_CONTRACT_VERSION


# -----------------------------
# Required schema keys
# -----------------------------

REQUIRED_TOP_LEVEL_KEYS: List[str] = [
    "gnce_contract_version",
    "adra_version",
    "adra_id",
    "GNCE_version",
    "created_at_utc",
    "drift_outcome",
    "drift_score",
    "L0_pre_execution_validation",
    "L1_the_verdict_and_constitutional_outcome",
    "L2_input_snapshot_and_dra",
    "L3_rule_level_trace",
    "L4_policy_lineage_and_constitution",
    "L5_integrity_and_tokenization",
    "L6_behavioral_drift_and_monitoring",
    "L7_veto_and_execution_feedback",
    "stewardship_context",
    "governance_context",
]

REQUIRED_L1_FIELDS: List[str] = [
    "decision_outcome",
    "severity",
    "timestamp_utc",
]


def validate_adra_v05(adra: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Lightweight schema validation for GNCE ADRA v0.5.

    Returns:
        (is_valid, errors)
        - is_valid: True if no structural issues found
        - errors: list of human-readable schema issues
    """
    errors: List[str] = []

    if not isinstance(adra, dict):
        return False, ["ADRA must be a dict."]

    # ---- top-level keys ----
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in adra:
            errors.append(f"Missing top-level key: '{key}'")

    # ---- version sanity ----
    contract = adra.get("gnce_contract_version")
    if contract != GNCE_CONTRACT_VERSION:
        errors.append(
            f"Invalid gnce_contract_version: {contract!r} (expected {GNCE_CONTRACT_VERSION})."
        )

    version = adra.get("adra_version")
    if version not in ("0.5", "0.5.0"):
        errors.append(f"Unexpected adra_version: {version!r} (expected '0.5').")

    # ---- L1 mandatory fields ----
    l1 = adra.get("L1_the_verdict_and_constitutional_outcome")
    if not isinstance(l1, dict):
        errors.append("L1_the_verdict_and_constitutional_outcome must be a dict.")
    else:
        for field in REQUIRED_L1_FIELDS:
            if field not in l1:
                errors.append(
                    f"Missing L1_the_verdict_and_constitutional_outcome field: '{field}'"
                )

    # ---- governance surfaces ----
    gov_ctx = adra.get("governance_context")
    if not isinstance(gov_ctx, dict):
        errors.append("governance_context must be a dict.")
    else:
        if "verdict_snapshot" not in gov_ctx:
            errors.append("governance_context.verdict_snapshot missing.")
        if "chain_of_custody" not in gov_ctx:
            errors.append("governance_context.chain_of_custody missing.")

    return (len(errors) == 0), errors


def build_adra_v05_skeleton(
    *,
    adra_id: str,
    gnce_version: str,
    drift_outcome: str,
    drift_score: float,
    l0: Dict[str, Any],
    l1: Dict[str, Any],
    l2: Dict[str, Any],
    l3: Dict[str, Any],
    l4: Dict[str, Any],
    l5: Dict[str, Any],
    l6: Dict[str, Any],
    l7: Dict[str, Any],
    stewardship_context: Dict[str, Any],
    governance_context: Dict[str, Any],
) -> Dict[str, Any]:
    """GNCE v0.5 — Canonical ADRA schema (runtime shape).

    - Matches what kernel.py and the UI expect:
      adra_id, GNCE_version, drift_outcome, drift_score,
      L0..L7, stewardship_context, governance_context.
    - Enforces schema-safety defaults so the builder never returns
      an invalid v0.5 ADRA (even if upstream forgets fields).
    """
    created_at_utc = datetime.now(timezone.utc).isoformat()

    adra: Dict[str, Any] = {
        # Core identity / metadata
        "gnce_contract_version": GNCE_CONTRACT_VERSION,
        "finalized": False,
        "adra_version": "0.5",
        "adra_id": adra_id,
        "GNCE_version": gnce_version,
        "created_at_utc": created_at_utc,
        # Root drift signals (used by SARS + UI chips)
        "drift_outcome": drift_outcome,
        "drift_score": drift_score,
        # Constitutional layers (L0–L7)
        "L0_pre_execution_validation": l0,
        "L1_the_verdict_and_constitutional_outcome": l1,
        "L2_input_snapshot_and_dra": l2,
        "L3_rule_level_trace": l3,
        "L4_policy_lineage_and_constitution": l4,
        "L5_integrity_and_tokenization": l5,
        "L6_behavioral_drift_and_monitoring": l6,
        "L7_veto_and_execution_feedback": l7,
        # Governance surfaces
        "stewardship_context": stewardship_context,
        "governance_context": governance_context,
    }

    # ------------------------------------------------------------
    # REQUIRED GOVERNANCE FIELDS (schema safety)
    # ------------------------------------------------------------
    # Validator requires governance_context as dict with:
    #   - verdict_snapshot
    #   - chain_of_custody
    if not isinstance(adra.get("governance_context"), dict):
        adra["governance_context"] = {}

    gc: Dict[str, Any] = adra["governance_context"]

    # Ensure chain_of_custody exists (empty dict acceptable)
    if not isinstance(gc.get("chain_of_custody"), dict):
        gc["chain_of_custody"] = {}

    # Ensure verdict_snapshot exists (derive safe defaults)
    if not isinstance(gc.get("verdict_snapshot"), dict):
        l1v = l1 if isinstance(l1, dict) else {}
        l6v = l6 if isinstance(l6, dict) else {}
        gc["verdict_snapshot"] = {
            "decision_outcome": l1v.get("decision_outcome"),
            "severity": l1v.get("severity"),
            "timestamp_utc": l1v.get("timestamp_utc") or created_at_utc,
            "engine_version": gnce_version,
            "human_oversight_required": bool(l1v.get("human_oversight_required")),
            "safe_state_triggered": bool(l1v.get("safe_state_triggered")),
            "drift_outcome": l6v.get("drift_outcome"),
            "drift_score": l6v.get("drift_score"),
        }

    adra["governance_context"] = gc

    # ------------------------------------------------------------
    # Optional v0.5+ reserved surfaces (forward compatible)
    # ------------------------------------------------------------
    adra.setdefault(
        "sars_v2",
        {
            "article_compliance": [],
            "severity_weighted_score": None,
            "heatmap_vector": {},
            "explainability": {
                "scoring_method": "",
                "cross_article_links": [],
            },
        },
    )

    adra.setdefault("evidence_chain", [])
    adra.setdefault("constitutional_path", [])
    adra.setdefault("kernel_execution_timeline", [])

    adra.setdefault(
        "dsa_cet_extended",
        {
            "articles_evaluated": [],
            "trusted_flagger_chain": [],
            "regulatory_access_chain": [],
            "explainability": {
                "why_article_applied": "",
                "evidence_links": [],
            },
        },
    )

    return adra
