# gnce/kernel/redaction.py

from __future__ import annotations

REDACTION_POLICY_VERSION = "1.0"

from typing import Any, Dict, List, Optional

from gnce.gn_kernel.guards.immutability import assert_mutable
import copy

# ============================================================
#  Helpers
# ============================================================

MINIMAL_KEYS_L4 = {"article", "status", "severity", "regime"}

DRIFT_PUBLIC_MAP = {
    "NO_DRIFT": "NO_DRIFT",
    "DRIFT_ALERT": "DRIFT_ALERT",
    # Any other internal drift codes map to a neutral placeholder
}

VETO_CATEGORY_MAP = {
    True: "BLOCKED",
    False: "NONE",
}


def _minimal_article_view(policy: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce a strict-minimal L4 article lineage for regulators.
    (Option A confirmed)
    """
    out = {}
    for k in MINIMAL_KEYS_L4:
        if k in policy:
            out[k] = policy[k]

    # Ensure regime is uppercase standard
    if "regime" in out and isinstance(out["regime"], str):
        out["regime"] = out["regime"].upper()

    # Guarantee severity is uppercase
    if "severity" in out:
        out["severity"] = str(out["severity"]).upper()

    return out


def _minimal_l6_view(l6: Dict[str, Any]) -> Dict[str, Any]:
    """
    Public drift report (reduces internal drift engine details).
    """
    drift = str(l6.get("drift_outcome", "NO_DRIFT")).upper()
    drift = DRIFT_PUBLIC_MAP.get(drift, "NO_DRIFT")  # collapse unknowns

    return {
        "drift_outcome": drift,
        "notes": (
            "GNCE detected behavioural drift indicators. "
            "Detailed drift telemetry withheld under GNCE Regulator Mode."
            if drift == "DRIFT_ALERT"
            else "No material behavioural drift detected."
        ),
    }


def _minimal_l7_view(l7: Dict[str, Any]) -> Dict[str, Any]:
    """
    Minimal veto view for regulators:
    - They see that execution was blocked.
    - But not the full internal corrective signal.
    """
    execution = bool(l7.get("execution_authorized", False))
    veto = bool(l7.get("veto_path_triggered", not execution))

    return {
        "execution_authorized": execution,
        "veto_triggered": veto,
        "veto_category": VETO_CATEGORY_MAP[veto],
    }


def _minimal_l5_view(l5: Dict[str, Any]) -> Dict[str, Any]:
    """
    CET exposure policy (Option A):
    - Keep content_hash_sha256 (immutable audit anchor)
    - Keep nonce (ensures uniqueness)
    - REMOVE internal pseudo-signature
    - REMOVE signing strategy
    """
    return {
        "content_hash_sha256": l5.get("content_hash_sha256", ""),
        "nonce": l5.get("nonce", ""),
    }


# ============================================================
#  MAIN ENTRYPOINT
# ============================================================

def redact_adra_for_regulator(adra: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a full GNCE ADRA into a regulator-safe (R-Mode) ADRA.

    Removes:
        - DRE internals
        - Rule IDs
        - Constitutional engine metadata
        - Full veto artifact details
        - Full drift telemetry
        - Internal CET pseudo-signature

    Retains:
        - Decision outcome + severity
        - Minimal L4 lineage (strict Option A)
        - Minimal drift report
        - Minimal veto report
        - CET content hash + nonce
    """
    if not isinstance(adra, dict):
        return {}

    # -----------------------------
    # Extract useful layers safely
    # -----------------------------
    l0 = adra.get("L0_pre_execution_validation", {}) or {}
    l1 = adra.get("L1_the_verdict_and_constitutional_outcome",{}) or {}
    l2 = adra.get("L2_input_snapshot_and_dra", {}) or {}
    l3 = adra.get("L3_rule_level_trace", {}) or {}
    l4 = adra.get("L4_policy_lineage_and_constitution", {}) or {}
    l5 = adra.get("L5_integrity_and_tokenization", {}) or {}
    l6 = adra.get("L6_behavioral_drift_and_monitoring", {}) or {}
    l7 = adra.get("L7_veto_and_execution_feedback", {}) or {}

    # -----------------------------
    # Build regulator L4 (minimal)
    # -----------------------------
    policies = l4.get("policies_triggered", []) or []
    minimal_l4 = [_minimal_article_view(p) for p in policies]

    # -----------------------------
    # Build R-Mode ADRA
    # -----------------------------
    redacted = {
    +   "redaction_policy_version": REDACTION_POLICY_VERSION,
        "adra_id": adra.get("adra_id"),
        "GNCE_version": adra.get("GNCE_version"),

        # Decision + severity remain fully public for compliance
        "decision": l1.get("decision_outcome"),
        "severity": l1.get("severity"),

        # Minimal constitutional reasoning
        "constitutional_basis": (
            "GNCE constitutional engine determined the verdict based on "
            "severity-weighted governing articles. Full internal basis "
            "is withheld under Regulator Mode."
        ),

        # L4 (minimal)
        "policy_lineage_minimal": minimal_l4,

        # CET (Option A)
        "CET": _minimal_l5_view(l5),

        # Drift (minimal)
        "drift": _minimal_l6_view(l6),

        # Veto (minimal)
        "veto": _minimal_l7_view(l7),
    }

    # Optional: include validation errors if present (harmless)
    if l0.get("issues"):
        redacted["input_validation"] = {
            "validated": l0.get("validated"),
            "issues": l0.get("issues"),
        }

    return redacted
