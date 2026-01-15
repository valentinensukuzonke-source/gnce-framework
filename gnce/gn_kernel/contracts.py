# gnce/kernel/contracts.py
from __future__ import annotations

"""
GNCE CONSTITUTIONAL CONTRACT (IMMUTABLE)
=======================================

This file defines the *public, stable contract* for GNCE v0.6.1-RC and beyond.

RULES (NON-NEGOTIABLE):
- The kernel returns a single ADRA dict.
- ADRA is immutable after finalization + hashing.
- UI / exporters / federation layers MUST treat ADRA as read-only.
- This file contains ZERO logic — contract only.
"""

from typing import Any, Dict, List, TypedDict, Literal


# =========================================================
# Contract version (bump ONLY when you break consumers)
# =========================================================
GNCE_CONTRACT_VERSION = "1.1"  # bumped from 1.0 → adds L1 + L4 narrative surfaces


# =========================================================
# Shared literals
# =========================================================
DecisionOutcome = Literal[
    "ALLOW",
    "DENY",
    "VETO",
    "DRIFT_ALERT",
    "UNKNOWN",
]

PolicyStatus = Literal[
    "VIOLATED",
    "SATISFIED",
    "NOT_APPLICABLE",
    "UNKNOWN",
]

SeverityBand = Literal[
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
    "UNKNOWN",
]

FederationMode = Literal[
    "OFF",
    "HASH_ONLY",
    "REDACTED",
    "FULL",
]


# =========================================================
# L4 — Policy Line Item (what regulators & UI inspect)
# =========================================================
class PolicyLineItem(TypedDict, total=False):
    # identity
    domain: str
    regime: str
    framework: str
    domain_id: str
    article: str
    category: str

    # outcome
    status: PolicyStatus
    severity: SeverityBand

    # explanation
    impact_on_verdict: str
    rationale: str
    notes: str

    # mechanics
    trigger_type: str
    rule_ids: List[str]

    # v0.6.1 — REQUIRED "MEAT"
    evidence: Dict[str, Any]          # what inputs caused this policy to trigger
    remediation: str                  # what must be done to resolve / mitigate


# =========================================================
# L1 — Verdict Contract (Decision Summary surface)
# =========================================================
class L1Verdict(TypedDict, total=False):
    # canonical outcome
    decision_outcome: DecisionOutcome
    severity: SeverityBand

    # metadata
    timestamp_utc: str
    engine_version: str

    # execution flags
    human_oversight_required: bool
    safe_state_triggered: bool

    # v0.6.1 — REQUIRED "MEAT"
    human_readable_outcome: str        # single-line executive explanation
    because: List[str]                # ordered causal reasons (human readable)
    regulator_summary: str            # concise regulator-grade explanation
    recommended_actions: List[str]    # what an operator must do next


# =========================================================
# ADRA — Top-level Constitutional Artifact
# =========================================================
class ADRA(TypedDict, total=False):
    # -----------------------------------------------------
    # Identity + immutability
    # -----------------------------------------------------
    gnce_contract_version: str
    adra_version: str
    gnce_version: str

    adra_id: str
    adra_hash: str
    created_at_utc: str

    # Finalization barrier
    finalized: bool

    # -----------------------------------------------------
    # Root signals
    # -----------------------------------------------------
    drift_outcome: str
    drift_score: float

    # -----------------------------------------------------
    # Constitutional layers (L0–L7)
    # -----------------------------------------------------
    L0_pre_execution_validation: Dict[str, Any]
    L1_the_verdict_and_constitutional_outcome: L1Verdict
    L2_input_snapshot_and_dra: Dict[str, Any]
    L3_rule_level_trace: Dict[str, Any]
    L4_policy_lineage_and_constitution: Dict[str, Any]
    L5_integrity_and_tokenization: Dict[str, Any]
    L6_behavioral_drift_and_monitoring: Dict[str, Any]
    L7_veto_and_execution_feedback: Dict[str, Any]

    # -----------------------------------------------------
    # Governance surfaces (non-authoritative)
    # -----------------------------------------------------
    stewardship_context: Dict[str, Any]
    governance_context: Dict[str, Any]

    # -----------------------------------------------------
    # Execution / audit surfaces
    # -----------------------------------------------------
    kernel_execution_timeline: List[Dict[str, Any]]
    constitutional_path: List[Dict[str, Any]]
    evidence_chain: List[Dict[str, Any]]

    # -----------------------------------------------------
    # Optional embedded lineage (post-finalization)
    # -----------------------------------------------------
    lineage: Dict[str, Any]

    # -----------------------------------------------------
    # Reserved future surfaces (allowed, optional)
    # -----------------------------------------------------
    sars_v2: Dict[str, Any]
    dsa_cet_extended: Dict[str, Any]

    # -----------------------------------------------------
    # Diagnostics (MUST NOT affect verdict)
    # -----------------------------------------------------
    _schema_valid: bool
    _schema_errors: List[str]
    _diagnostics: Dict[str, Any]


# =========================================================
# Backwards-compatibility alias
# =========================================================
# In v0.6.1 the kernel returns ADRA directly.
KernelOutput = ADRA
