from __future__ import annotations
import re
# gnce/gn_kernel/kernel.py

import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Tuple, Optional, Set, Union, Callable, Collection
import uuid
import copy
import re
import time
import logging
import traceback
from collections import defaultdict
import sys

logger = logging.getLogger(__name__)


from .exporter import export_adra

# Optional jurisdiction/industry router fallback (used to fill scope gaps when profiles are incomplete).
try:
    from gnce.gn_kernel.constitution.gnce_jurisdiction_router import route_regimes as _route_regimes_fallback
except Exception as e:  # pragma: no cover
    _route_regimes_fallback = None
    # Log the import failure for debugging
    import warnings
    warnings.warn(f"Failed to import jurisdiction router: {e}")

from .models.adra_v05 import build_adra_v05_skeleton, validate_adra_v05
from gnce.gn_kernel.industry.registry import INDUSTRY_REGISTRY


# ---------------------------------------------------------------------------
# Compatibility shim: resolve_industry_and_profile
#
# Some kernel variants (and external callers) expect a helper that resolves the
# canonical industry_id + profile_id + profile_spec from INDUSTRY_REGISTRY.
#
# Keep this helper dependency-light and self-contained so it works across
# releases (no reliance on private _canon_* helpers).
# ---------------------------------------------------------------------------

def _canon_regime(x: Any) -> str:
    """Normalize regime-like identifiers to uppercase snake-case."""
    return str(x or "").strip().upper().replace(" ", "_").replace("-", "_")

# UI/profile-friendly aliases -> kernel registry IDs
REGIME_ID_ALIASES = {
    "EU_DSA": "DSA",
    "EU_DMA": "DMA",
    "EU_GDPR": "GDPR",
    "GDPR_EU": "GDPR",
    "EU_AI_ACT": "EU_AI_ACT",
    "AI_ACT_EU": "EU_AI_ACT",
    "ISO_42001": "ISO_42001",
    "ISO_IEC_42001": "ISO_42001",
    "ISO/IEC_42001": "ISO_42001",
    "NIST_AI_RMF": "NIST_AI_RMF",
}

def _canon_regime_id(x: Any) -> str:
    """Canonicalize a regime identifier and apply alias mapping."""
    c = _canon_regime(x)
    return REGIME_ID_ALIASES.get(c, c)

def _canon_regime_set(vals):
    """Canonicalize a list/set of regime IDs, applying alias mapping and de-duping."""
    if not vals:
        return set()
    if isinstance(vals, str):
        vals = [vals]
    out = set()
    for v in vals:
        cv = _canon_regime_id(v)
        if cv:
            out.add(cv)
    return out

def _canon_set(vals: Optional[Collection[Any]]) -> Optional[Set[str]]:
    if not vals:
        return None
    out = {_canon_regime(v) for v in vals if v}
    return out if out else None

def resolve_industry_and_profile(
    payload: Dict[str, Any]
) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, Any]]]:
    """
    Resolve industry + profile deterministically.
    Kernel is the single source of truth.
    """
    if not isinstance(payload, dict):
        return None, None, None

    raw_industry = payload.get("industry_id")
    raw_profile = payload.get("profile_id") or payload.get("industry_profile_id")

    if not raw_industry or not raw_profile:
        return None, None, None

    industry_id = _canon_regime(raw_industry)
    profile_id = _canon_regime(raw_profile)

    industry = INDUSTRY_REGISTRY.get(industry_id)
    if not isinstance(industry, dict):
        # fallback to raw key if registry is non-canonical
        industry = INDUSTRY_REGISTRY.get(str(raw_industry))
        if not isinstance(industry, dict):
            return None, None, None
        industry_id = str(raw_industry)

    profiles = industry.get("profiles") or {}
    if not isinstance(profiles, dict):
        return None, None, None

    profile_spec = profiles.get(profile_id)
    if not isinstance(profile_spec, dict):
        # fallback to raw key
        profile_spec = profiles.get(str(raw_profile))
        if not isinstance(profile_spec, dict):
            return None, None, None
        profile_id = str(raw_profile)

    return industry_id, profile_id, profile_spec

from gnce.ledger.ledger import (
    build_adra_ledger_row,
    build_article_ledger_rows,
    append_to_session_ledger,
    append_to_article_ledger,
)


from gnce.gn_kernel.drift.dda import evaluate_drift
from gnce.gn_kernel.constitution.authority import GNCE_CONSTITUTION
from gnce.gn_kernel.regimes.register import init_registry, REGIME_REGISTRY
from gnce.gn_kernel.rules.dsa_rules import evaluate_dsa_rules
from gnce.gn_kernel.rules.dma_rules import evaluate_dma_rules
from gnce.gn_kernel.rules.finra_rules import evaluate_finra_rules
from gnce.gn_kernel.rules.hipaa_rules import evaluate_hipaa_rules
from gnce.gn_kernel.rules.nydfs_500_rules import evaluate_nydfs_500_rules
from gnce.gn_kernel.rules.eu_ai_act_rules import evaluate_eu_ai_act_rules
from gnce.gn_kernel.rules.pci_dss_rules import evaluate_pci_dss_rules
from gnce.gn_kernel.lineage.lineage_builder import build_lineage
from gnce.gn_kernel.rules.iso_42001_rules import evaluate_iso_42001_rules
from gnce.gn_kernel.rules.nist_ai_rmf_rules import evaluate_nist_ai_rmf_rules
from gnce.gn_kernel.rules.saas_transaction_integrity_rules import evaluate_saas_transaction_integrity_rules

# =========================================================
# NEW: Enhanced Logging Configuration
# =========================================================
# Create a logger for the kernel
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Configure basic logging if not already configured
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# =========================================================
# NEW: Kernel Configuration Manager
# =========================================================
class KernelConfig:
    """Central configuration manager for kernel behavior."""
    
    # Core version and features
    VERSION = "0.7.2-RC"
    EXPORT_ENABLED = False
    
    # Performance optimizations
    PERFORMANCE_OPTIMIZATIONS = {
        "skip_deep_copy_for_single_regime": True,
        "lazy_regime_adra_generation": False,  # Keep False for ledger compliance
        "batch_ledger_writes": False,
        "max_payload_size_bytes": 10 * 1024 * 1024,  # 10MB
        "cache_industry_resolution": True,
    }
    
    # Evaluation modes with detailed metadata
    EVALUATION_MODES = {
        "STRICT": {
            "description": "All rules enforced, blocking failures cause DENY",
            "allow_ledger_writes": True,
            "allow_veto": True,
            "allow_export": True,
        },
        "ADVISORY": {
            "description": "Evaluate but don't block (audit mode)",
            "allow_ledger_writes": True,
            "allow_veto": False,
            "allow_export": True,
        },
        "DRY_RUN": {
            "description": "Evaluate without ledger writes",
            "allow_ledger_writes": False,
            "allow_veto": True,
            "allow_export": False,
        },
        "LEARNING": {
            "description": "Evaluate and collect feedback for ML",
            "allow_ledger_writes": True,
            "allow_veto": True,
            "allow_export": True,
            "collect_telemetry": True,
        },
    }
    
    # Quality gates with thresholds
    QUALITY_GATES = {
        "minimum_evidence_count": 3,
        "maximum_evaluation_time_ms": 5000,
        "maximum_memory_usage_mb": 100,
        "required_fields": ["adra_id", "adra_hash", "timestamp_utc"],
        "allow_partial_failure": False,
    }
    
    # Evidence retention policy
    EVIDENCE_RETENTION_POLICY = {
        "DENY": timedelta(days=365 * 7),      # 7 years for denials
        "ALLOW_WITH_VIOLATIONS": timedelta(days=365 * 3),  # 3 years
        "ALLOW": timedelta(days=365),         # 1 year
        "ERROR": timedelta(days=30),          # 30 days
        "DRY_RUN": timedelta(days=7),         # 7 days for dry runs
    }
    
    # Safety limits
    SAFETY_LIMITS = {
        "max_policies_per_evaluation": 1000,
        "max_regimes_per_profile": 50,
        "max_recursion_depth": 10,
        "max_parallel_evaluations": 1,  # Currently sequential
    }
    
    # Debug and troubleshooting
    DEBUG = {
        "log_payload_summary": True,
        "log_policy_decisions": True,
        "log_performance_metrics": True,
        "trace_exceptions": True,
        "validate_outputs": True,
    }

# Alias for backward compatibility
GNCE_VERSION = KernelConfig.VERSION
EXPORT_ENABLED = KernelConfig.EXPORT_ENABLED
PERFORMANCE_OPTIMIZATIONS = KernelConfig.PERFORMANCE_OPTIMIZATIONS
EVALUATION_MODES = {k: v["description"] for k, v in KernelConfig.EVALUATION_MODES.items()}
QUALITY_GATES = KernelConfig.QUALITY_GATES
EVIDENCE_RETENTION_POLICY = KernelConfig.EVIDENCE_RETENTION_POLICY

# =========================================================
# ENHANCED ERROR TYPES (for better debugging)
# =========================================================

class KernelError(RuntimeError):
    """Base class for all kernel errors."""
    def __init__(self, message: str, error_code: str = "KERNEL_ERROR", details: Optional[Dict] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()

class LedgerComplianceError(KernelError):
    """Raised when an ADRA fails sovereign ledger compliance."""
    def __init__(self, message: str, adra_id: Optional[str] = None, missing_fields: Optional[List[str]] = None):
        super().__init__(
            message=message,
            error_code="LEDGER_COMPLIANCE_ERROR",
            details={
                "adra_id": adra_id,
                "missing_fields": missing_fields or [],
                "required_fields": ["constitution_hash", "veto_layer", "clause"],
            }
        )

class RoutingError(KernelError):
    """Raised when industry/profile routing fails."""
    def __init__(self, message: str, industry_id: Optional[str] = None, profile_id: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="ROUTING_ERROR",
            details={
                "industry_id": industry_id,
                "profile_id": profile_id,
                "available_industries": list(INDUSTRY_REGISTRY.keys()) if INDUSTRY_REGISTRY else [],
            }
        )

class ScopeError(KernelError):
    """Raised when enabled regimes scope is invalid."""
    def __init__(self, message: str, enabled_regimes: Optional[List[str]] = None):
        super().__init__(
            message=message,
            error_code="SCOPE_ERROR",
            details={
                "enabled_regimes": enabled_regimes or [],
                "available_regimes": list(REGIME_REGISTRY.keys()) if REGIME_REGISTRY else [],
            }
        )

class ValidationError(KernelError):
    """Raised when validation fails."""
    def __init__(self, message: str, validation_errors: Optional[List[str]] = None, layer: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={
                "validation_errors": validation_errors or [],
                "layer": layer,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

class PerformanceError(KernelError):
    """Raised when performance thresholds are exceeded."""
    def __init__(self, message: str, duration_ms: float, threshold_ms: float):
        super().__init__(
            message=message,
            error_code="PERFORMANCE_ERROR",
            details={
                "duration_ms": duration_ms,
                "threshold_ms": threshold_ms,
                "exceeded_by_ms": duration_ms - threshold_ms,
            }
        )

# =========================================================
# ENHANCED INTERNAL HELPERS (with better error handling)
# =========================================================

def _map_regime_to_taxonomy_domain_id(regime_id: str) -> str:
    # No taxonomy tree exists in this repo yet, so keep domain_id stable.
    # Use regime IDs (DSA/DMA/...) as domain IDs for now.
    return str(regime_id or "").upper() or ""

def _assert_ledger_compliance(adra: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enforce sovereign ledger requirements BEFORE writing evidence.
    This guarantees Loop 2 / Loop 3 coherence.
    """
    
    try:
        logger.debug("Validating ledger compliance for ADRA")
        
        # Make defensive copies to avoid mutating original
        adra = dict(adra)
        l4 = adra.get("L4_policy_lineage_and_constitution", {}) or {}
        l5 = adra.get("L5", {}) or adra.get("L5_integrity_and_tokenization", {}) or {}
        l7 = adra.get("L7_veto_and_execution_feedback", {}) or {}
        l1 = adra.get("L1_the_verdict_and_constitutional_outcome", {}) or {}

        verdict = str(l1.get("decision_outcome", "")).upper().strip()
        adra_id = adra.get("adra_id", "UNKNOWN")

        # ---------- Constitution hash (MANDATORY) ----------
        constitution_hash = (
            adra.get("constitution_hash")
            or l4.get("constitution_hash")
            or l5.get("content_hash_sha256")
        )

        if not constitution_hash:
            missing_fields = []
            if not adra.get("constitution_hash"): missing_fields.append("constitution_hash")
            if not l4.get("constitution_hash"): missing_fields.append("L4.constitution_hash")
            if not l5.get("content_hash_sha256"): missing_fields.append("L5.content_hash_sha256")
            
            raise LedgerComplianceError(
                "Missing constitution_hash (required for sovereign traceability)",
                adra_id=adra_id,
                missing_fields=missing_fields,
            )

        # ---------- DENY-specific attribution ----------
        if verdict == "DENY":
            veto_layer = (
                l7.get("veto_layer")
                or l7.get("origin_layer")
                or l7.get("trigger_layer")
            )

            if not veto_layer:
                # Try to infer from other layers
                if not l0.get("validated", True):
                    veto_layer = "L0"
                elif not l3.get("validated", True):
                    veto_layer = "L3"
                elif l1.get("decision_outcome") == "DENY":
                    veto_layer = "L1"
                else:
                    veto_layer = "UNKNOWN"
                
                # Still raise error but with inferred value
                if veto_layer == "UNKNOWN":
                    raise LedgerComplianceError(
                        "DENY decision missing veto_layer attribution",
                        adra_id=adra_id,
                        missing_fields=["veto_layer", "origin_layer", "trigger_layer"],
                    )

            clause = (
                l7.get("clause")
                or l7.get("article")
                or l7.get("constitutional_clause")
                or "UNSPECIFIED"
            )

            # Normalize back into ADRA so the ledger writer can rely on it
            l7["veto_layer"] = veto_layer
            l7["clause"] = clause
            adra["L7_veto_and_execution_feedback"] = l7

        # ---------- Promote constitution_hash explicitly ----------
        adra["constitution_hash"] = constitution_hash

        logger.debug(f"Ledger compliance validated for ADRA: {adra_id}")
        return adra
        
    except LedgerComplianceError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in ledger compliance check: {str(e)}")
        raise LedgerComplianceError(
            f"Failed to validate ledger compliance: {str(e)}",
            adra_id=adra.get("adra_id"),
            missing_fields=["unknown"],
        )

def _utc_now_iso(timespec: str = "seconds") -> str:
    """Get current UTC time as ISO string."""
    try:
        return datetime.now(timezone.utc).isoformat(timespec=timespec)
    except Exception as e:
        logger.warning(f"Failed to get UTC time: {e}, falling back to timestamp")
        return str(int(time.time()))

def _normalize_payload(payload: Any, max_size: int = KernelConfig.PERFORMANCE_OPTIMIZATIONS["max_payload_size_bytes"]) -> Dict[str, Any]:
    """Normalize payload with safety checks."""
    try:
        if payload is None:
            return {}
        
        if isinstance(payload, dict):
            # Check size limit
            payload_str = json.dumps(payload)
            if len(payload_str) > max_size:
                logger.warning(f"Payload size {len(payload_str)} exceeds limit {max_size}")
                # Return minimal payload with error flag
                return {
                    "raw_input": "PAYLOAD_SIZE_EXCEEDED",
                    "error": f"Payload size {len(payload_str)} exceeds limit {max_size}",
                    "truncated": True,
                }
            return payload
        
        # Try to convert other types
        try:
            payload_str = str(payload)
            if len(payload_str) > max_size:
                logger.warning(f"Payload string size {len(payload_str)} exceeds limit")
                payload_str = payload_str[:max_size] + "... [TRUNCATED]"
            
            # Try to parse as JSON if it looks like JSON
            if payload_str.strip().startswith(('{', '[')):
                try:
                    parsed = json.loads(payload_str)
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    pass
            
            return {"raw_input": payload_str}
            
        except Exception as e:
            logger.error(f"Failed to normalize payload: {e}")
            return {"raw_input": "UNPARSEABLE_INPUT", "error": str(e)}
            
    except Exception as e:
        logger.error(f"Critical error in payload normalization: {e}")
        return {"error": f"Payload normalization failed: {str(e)}", "timestamp": _utc_now_iso()}

def _sha256_of(obj: Any) -> str:
    """Compute SHA256 hash of JSON-serializable object."""
    try:
        # Use consistent serialization
        data = json.dumps(
            obj, 
            sort_keys=True, 
            separators=(",", ":"),
            ensure_ascii=False
        ).encode("utf-8")
        return "sha256:" + hashlib.sha256(data).hexdigest()
    except (TypeError, ValueError) as e:
        # Fallback for non-serializable objects
        logger.warning(f"Failed to serialize object for hash: {e}, using string representation")
        try:
            data = str(obj).encode("utf-8")
            return "sha256:" + hashlib.sha256(data).hexdigest()
        except Exception as e2:
            logger.error(f"Failed to compute hash: {e2}")
            return "sha256:ERROR"

def _dedupe_causal_trace(items: Optional[List[Dict]]) -> List[Dict]:
    """Deduplicate causal trace items."""
    if not items:
        return []
    
    out = []
    seen = set()
    
    for x in items:
        if not isinstance(x, dict):
            logger.debug(f"Skipping non-dict item in causal trace: {type(x)}")
            continue
        
        # Create unique key
        key = (
            x.get("regime", "UNKNOWN"),
            x.get("article", "UNKNOWN"),
            tuple(x.get("rule_ids") or []),
            x.get("status", "UNKNOWN"),
        )
        
        if key in seen:
            logger.debug(f"Deduplicating duplicate causal trace item: {key}")
            continue
        
        seen.add(key)
        out.append(x)
    
    logger.debug(f"Deduplicated {len(items)} -> {len(out)} causal trace items")
    return out

def _is_allow_baseline(payload: Dict[str, Any]) -> bool:
    """
    Baseline mode is allowed ONLY when no regime-specific context is present.
    CRITICAL FIX: Always return False if any compliance signals exist.
    
    SAFETY FIRST: If any doubt, force full evaluation.
    """
    if not isinstance(payload, dict):
        return True  # Default to baseline for non-dicts

    # CRITICAL SAFETY CHECK 1: If ANY risk indicators key exists, force full evaluation
    if "risk_indicators" in payload:
        # Even if risk_indicators dict is empty, we should evaluate
        # because the presence of the key indicates this is a compliance-aware request
        return False
    
    # CRITICAL SAFETY CHECK 2: Force evaluation for ANY compliance profile
    compliance_profiles = [
        "dsa", "dma_profile", "ai_profile", "platform_behavior",
        "pci_profile", "hipaa_profile", "sec_17a4_profile",
        "finra_profile", "sox_profile", "data_types", "export"
    ]
    
    for profile in compliance_profiles:
        if profile in payload and payload[profile]:
            # Profile exists and is not empty/false
            return False
    
    # CRITICAL SAFETY CHECK 3: Force evaluation for content-related actions
    action = str(payload.get("action", "")).upper()
    content_actions = [
        "POST_CONTENT", "LIST_PRODUCT", "EXPORT_DATA", "PROCESS_TRANSACTION",
        "ACCESS_DATA", "MODIFY_DATA", "DELETE_DATA", "QUERY_DATA",
        "CREATE_ORDER", "CANCEL_ORDER", "REFUND", "SHIP_PRODUCT"
    ]
    
    if action in content_actions:
        return False
    
    # CRITICAL SAFETY CHECK 4: Force evaluation if content exists
    if payload.get("content"):
        return False
    
    # CRITICAL SAFETY CHECK 5: Force evaluation for VLOP/enterprise signals
    meta = payload.get("meta") or {}
    if meta:
        # If meta exists (even empty), likely a compliance-aware request
        return False
    
    # CRITICAL SAFETY CHECK 6: Force evaluation for any governance context
    if payload.get("governance") or payload.get("audit"):
        return False
    
    # ONLY allow baseline for TRULY empty/neutral payloads
    # This should be very rare - most real requests should go through full evaluation
    empty_keys = [k for k in payload.keys() if k not in ["timestamp_utc", "user_id", "request_id"]]
    if not empty_keys:
        return True
    
    # Default to False (force evaluation) when in doubt
    return False

def _filter_policies_by_enabled_regimes(
    policies: List[Dict[str, Any]],
    enabled: Optional[Collection[str]],
) -> List[Dict[str, Any]]:
    enabled_canon = _canon_set(enabled)
    if not enabled_canon:
        return policies

    out: List[Dict[str, Any]] = []
    for p in (policies or []):
        if not isinstance(p, dict):
            continue
        if _canon_regime(p.get("regime")) in enabled_canon:
            out.append(p)
    return out

    import re
def _apply_dsa_vlop_gating(policies: List[Dict[str, Any]], payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Post-process DSA systemic-risk articles so non‑VLOP profiles don't get hard-blocked for missing VLOP-only controls.
    
    IMPORTANT SAFETY RULE: Harmful/illegal content ALWAYS requires DSA Art. 34 evaluation, even for non-VLOPs.
    
    Rules:
    1. If meta.is_vlop is True → Return policies unchanged (VLOPs must meet all DSA obligations)
    2. If meta.is_vlop is False:
        - DSA Art. 36/37/39 → NOT_APPLICABLE (VLOP-only obligations)
        - DSA Art. 34 → ONLY NOT_APPLICABLE if NO harmful/illegal signals present
        * If harmful_flag=True or violation_category indicates illegal content → KEEP VIOLATED/SATISFIED
        - All other DSA articles (14, 16, 17, 20, 22, 24, 27, 38) → Process normally
    3. Harmful content detection:
        - harmful_content_flag=True → Always triggers DSA evaluation
        - violation_category containing 'harmful', 'illegal', 'terrorism', 'extremism', 'child_abuse' → Triggers DSA
    
    Future-proofing:
    - Case-insensitive matching for DSA article patterns
    - Supports both 'DSA' and 'EU_DSA' regime identifiers
    - Handles article variations (Art., Article, Art, §)
    - Defensive coding against malformed policies
    """
    
    # Safe extraction with defaults
    meta = (payload or {}).get("meta") or {}
    is_vlop = bool(meta.get("is_vlop") or meta.get("vlop") or meta.get("is_vlose"))
    
    # VLOPs must meet all obligations - no gating
    if is_vlop:
        return policies

    # Extract risk indicators safely
    ri = (payload or {}).get("risk_indicators") or {}
    harmful_flag = bool(ri.get("harmful_content_flag") or ri.get("illegal_content_flag"))
    violation_category = str(ri.get("violation_category") or "").lower().strip()
    
    # Define illegal/harmful signals (expanded for future-proofing)
    illegal_keywords = {
        'harmful', 'illegal', 'terrorism', 'extremism', 'violent', 
        'child_abuse', 'csam', 'exploitation', 'hate_speech', 'harassment',
        'dangerous', 'suicide', 'self_harm', 'violence', 'threat'
    }
    
    # Check if violation category indicates illegal content
    category_illegal = any(keyword in violation_category for keyword in illegal_keywords)
    
    # Also check content itself for harmful keywords (defensive)
    content = str(payload.get("content") or "").lower()
    content_harmful = any(
        keyword in content 
        for keyword in ['kill', 'harm', 'hurt', 'attack', 'bomb', 'weapon']
    ) if len(content) > 0 else False
    
    # Final illegal signal determination
    illegal_signal = harmful_flag or category_illegal or content_harmful
    
    # Enhanced logging for debugging
    import logging
    logger = logging.getLogger(__name__)
    if illegal_signal:
        logger.debug(f"DSA gating: illegal_signal detected - harmful_flag={harmful_flag}, "
                    f"category='{violation_category}', content_harmful={content_harmful}")

    def _mark_na(p: Dict[str, Any], reason: str, article: str = None) -> Dict[str, Any]:
        """
        Safely mark a policy as NOT_APPLICABLE with proper metadata.
        """
        # Create a defensive copy
        p_copy = dict(p)
        
        # Preserve original status for audit trail
        original_status = p_copy.get("status", "UNKNOWN")
        p_copy["original_status"] = original_status
        p_copy["gating_reason"] = reason
        
        # Set gated status
        p_copy["status"] = "NOT_APPLICABLE"
        p_copy["severity"] = "LOW"
        p_copy["impact_on_verdict"] = "Neutral non-applicable surface (VLOP-gated)."
        
        # Update notes with gating reason
        notes = p_copy.get("notes") or ""
        gating_note = f"[VLOP-gated: {reason}]"
        p_copy["notes"] = f"{gating_note} {notes}".strip()
        
        # Clear violation details (since it's not applicable)
        if "violation_detail" in p_copy:
            p_copy["violation_detail"] = ""
        
        # Preserve evidence but add gating context
        evidence = p_copy.get("evidence") or {}
        evidence["vlop_gated"] = True
        evidence["gating_reason"] = reason
        evidence["is_vlop"] = is_vlop
        p_copy["evidence"] = evidence
        
        # Clear remediation for non-applicable policies
        p_copy["remediation"] = "Not applicable - VLOP-only obligation."
        
        # Add gating metadata for traceability
        p_copy["metadata"] = p_copy.get("metadata") or {}
        p_copy["metadata"]["vlop_gating_applied"] = True
        p_copy["metadata"]["gating_timestamp"] = _utc_now_iso()
        
        return p_copy

    # Process policies with enhanced article detection
    out: List[Dict[str, Any]] = []
    
    for p in policies:
        if not isinstance(p, dict):
            out.append(p)  # Keep malformed entries unchanged
            continue
            
        regime = str(p.get("regime") or "").upper().strip()
        article = str(p.get("article") or "").strip()
        
        # Only process DSA policies
        if regime not in {"DSA", "EU_DSA"}:
            out.append(p)
            continue
        
        # Enhanced article pattern matching (future-proof)
        # Supports: DSA Art. 34, DSA Article 34, Art.34, Art 34, §34, etc.
        article_lower = article.lower()
        
        # Check for VLOP-only articles (36, 37, 39) - always gated for non-VLOPs
        vlop_only_match = re.search(
            r'(?:art(?:icle)?\.?\s*|§\s*)(3[679]|36|37|39)\b', 
            article_lower
        )
        
        if vlop_only_match:
            article_num = vlop_only_match.group(1)
            out.append(_mark_na(p, f"VLOP-only systemic obligation Art. {article_num} (is_vlop=false)", f"DSA Art. {article_num}"))
            continue
        
        # Check for Art. 34 - special handling for harmful/illegal content
        art34_match = re.search(
            r'(?:art(?:icle)?\.?\s*|§\s*)34\b',
            article_lower
        )
        
        if art34_match:
            if illegal_signal:
                # Harmful/illegal content detected - KEEP the policy (don't gate)
                # This ensures harmful content is always evaluated under DSA Art. 34
                if illegal_signal and p.get("status") == "NOT_APPLICABLE":
                    # If policy was marked NOT_APPLICABLE but we have illegal signal, update it
                    p["status"] = "SATISFIED"  # Default to satisfied, evaluator will set violated if needed
                    p["notes"] = f"[VLOP-exception: harmful content triggers Art. 34] {p.get('notes', '')}".strip()
                    p["impact_on_verdict"] = "Systemic risk assessment required for harmful content."
                out.append(p)
            else:
                # No illegal signal - gate Art. 34 for non-VLOPs
                out.append(_mark_na(p, "Systemic risk obligation gated for non-VLOP (no harmful/illegal signals)", "DSA Art. 34"))
            continue
        
        # For all other DSA articles, pass through unchanged
        out.append(p)
    
    # Log statistics for debugging
    gated_count = sum(1 for p in out if isinstance(p, dict) and p.get("status") == "NOT_APPLICABLE" and "VLOP-gated" in str(p.get("notes", "")))
    if gated_count > 0:
        logger.debug(f"DSA VLOP gating applied: {gated_count} policies gated, illegal_signal={illegal_signal}")
    
    return out

def _append_cross_regime_stubs(
    policies: List[Dict[str, Any]],
    enabled: Optional[Set[str]] = None,
) -> None:
    """Append NOT_APPLICABLE regime stubs, optionally filtered to enabled regimes.

    These stubs are *surface only* (LOW, NOT_APPLICABLE) and should never drive a DENY.
    If `enabled` is provided, only stubs whose regime is in-scope are appended.
    """

    def _canon(x: Any) -> str:
        return str(x or "").strip().upper().replace(" ", "_").replace("-", "_")

    stubs: List[Dict[str, Any]] = [
        {
            "domain": "EU AI Act",
            "regime": "EU_AI_ACT",
            "framework": "AI Governance & Risk Management",
            "domain_id": "EU_AI_ACT",
            "article": "AI Act Art. 9",
            "category": "AI governance controls",
            "status": "NOT_APPLICABLE",
            "severity": "LOW",
            "impact_on_verdict": "Not applicable to this scenario.",
            "trigger_type": "NOT_APPLICABLE",
            "rule_ids": ["EU_AI_ACT_NA"],
            "notes": "Regime surface present for completeness; no constraints activated.",
        },
        {
            "domain": "ISO/IEC 42001",
            "regime": "ISO_42001",
            "framework": "AI Governance & Risk Management",
            "domain_id": "ISO_42001",
            "article": "ISO/IEC 42001 Cl. 6",
            "category": "AI governance controls",
            "status": "NOT_APPLICABLE",
            "severity": "LOW",
            "impact_on_verdict": "Not applicable to this scenario.",
            "trigger_type": "NOT_APPLICABLE",
            "rule_ids": ["ISO_42001_NA"],
            "notes": "Regime surface present for completeness; no constraints activated.",
        },
        {
            "domain": "NIST AI RMF",
            "regime": "NIST_AI_RMF",
            "framework": "Risk Management Framework",
            "domain_id": "NIST_AI_RMF",
            "article": "NIST AI RMF Core",
            "category": "Govern function",
            "status": "NOT_APPLICABLE",
            "severity": "LOW",
            "impact_on_verdict": "Not applicable to this scenario.",
            "trigger_type": "NOT_APPLICABLE",
            "rule_ids": ["NIST_AI_RMF_NA"],
            "notes": "Regime surface present for completeness; no constraints activated.",
        },
    ]

    if enabled:
        enabled_canon = {_canon(x) for x in enabled if x}
        stubs = [s for s in stubs if _canon(s.get("regime")) in enabled_canon]

    policies.extend(stubs)

def _decorate_policy_items(payload: Dict[str, Any], policies: List[Dict[str, Any]]) -> None:
    risk = payload.get("risk_indicators") or {}
    cat = str(risk.get("violation_category") or "").lower().strip()

    for p in policies:
        if not isinstance(p, dict):
            continue

        existing = p.get("evidence")
        evidence = existing if isinstance(existing, dict) else {}

        evidence.update(
            {
                "action": payload.get("action"),
                "content": payload.get("content"),
                "user_id": payload.get("user_id"),
                "harmful_content_flag": bool(risk.get("harmful_content_flag")),
                "violation_category": risk.get("violation_category"),
                "previous_violations": risk.get("previous_violations"),
            }
        )
        p["evidence"] = evidence

        status = str(p.get("status", "")).upper()

        # Respect regime-specific remediation if already set (e.g., PCI/DMA/EU AI Act)
        if status == "VIOLATED":
            if not str(p.get("remediation") or "").strip():
                if cat == "extremism":
                    p["remediation"] = (
                        "Block the action, preserve evidence, flag the account, require verification, "
                        "and route to Integrity review."
                    )
                elif cat:
                    p["remediation"] = (
                        f"Block the action and route to policy owner review (category: {cat}); "
                        "collect evidence and re-run GNCE after mitigation."
                    )
                else:
                    p["remediation"] = (
                        "Block the action and route to the policy owner for review; "
                        "collect evidence and re-run GNCE after mitigation."
                    )
        else:
            # Non-violations keep any existing remediation; otherwise default
            p.setdefault("remediation", "No remediation required.")

def _is_material_policy(p: Dict[str, Any]) -> bool:
    if not isinstance(p, dict):
        return False
    status = str(p.get("status", "")).upper()
    return status in {"VIOLATED", "SATISFIED"}

# =========================================================
# EXECUTION LOOP COMPATIBILITY HELPERS
# =========================================================

def prepare_execution_payload(
    raw_request: Dict[str, Any],
    industry_id: Optional[str] = None,
    profile_id: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    evaluation_mode: str = "STRICT",
    enabled_regimes: Optional[List[str]] = None,
    context_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Prepare execution loop payload for kernel consumption.
    
    This helper bridges the execution loop with the kernel by:
    1. Adding required metadata fields
    2. Setting proper industry/profile routing
    3. Adding jurisdiction information
    4. Ensuring proper evaluation mode
    
    Args:
        raw_request: Original request from execution loop
        industry_id: Optional industry override
        profile_id: Optional profile override
        jurisdiction: Optional jurisdiction (e.g., "EU", "US", "US-NY")
        evaluation_mode: Evaluation mode (STRICT, ADVISORY, DRY_RUN, LEARNING)
        enabled_regimes: Optional list of regimes to enable
        context_id: Optional evaluation context ID for chained evaluations
    
    Returns:
        Kernel-ready payload
    """
    # Start with a copy of the raw request
    payload = dict(raw_request) if isinstance(raw_request, dict) else {}
    
    # Ensure meta object exists
    meta = payload.get("meta") or {}
    if not isinstance(meta, dict):
        meta = {}
    
    # Add/override jurisdiction if provided
    if jurisdiction:
        meta["jurisdiction"] = jurisdiction
    
    # Add execution loop metadata
    meta.update({
        "source": "execution_loop",
        "received_at_utc": _utc_now_iso(),
        "execution_loop_version": "1.0.0",
    })
    
    payload["meta"] = meta
    
    # Add/override industry and profile
    if industry_id:
        payload["industry_id"] = industry_id
    if profile_id:
        payload["profile_id"] = profile_id
    
    # Ensure we have at least basic industry/profile hints
    if "industry_id" not in payload:
        # Try to infer from request type
        action = str(payload.get("action", "")).upper()
        if "DSA" in action or "DMA" in action or "PLATFORM" in action or "LIST" in action or "POST" in action:
            payload["industry_id"] = "SOCIAL_MEDIA"
        elif "EXPORT" in action or "DATA" in action or "PROCESS" in action:
            payload["industry_id"] = "DATA_PROCESSING"
        elif "PAYMENT" in action or "TRANSACTION" in action or "ECOMMERCE" in action:
            payload["industry_id"] = "ECOMMERCE"
        else:
            payload["industry_id"] = "GENERAL"
    
    if "profile_id" not in payload:
        # Default profile based on industry
        industry = payload.get("industry_id", "GENERAL")
        if industry == "SOCIAL_MEDIA":
            payload["profile_id"] = "PLATFORM_STANDARD"
        elif industry == "ECOMMERCE":
            # Check if it's a marketplace
            if "MARKETPLACE" in str(payload.get("meta", {}).get("customer_profile_id", "")).upper():
                payload["profile_id"] = "ECOMMERCE_MARKETPLACE_EU"
            else:
                payload["profile_id"] = "MERCHANT_STANDARD"
        elif industry == "DATA_PROCESSING":
            payload["profile_id"] = "PROCESSOR_STANDARD"
        else:
            payload["profile_id"] = "STANDARD"
    
    # Add evaluation mode and context
    payload["evaluation_mode"] = evaluation_mode
    if context_id:
        payload["evaluation_context_id"] = context_id
    
    # Add enabled regimes if specified
    if enabled_regimes:
        payload["enabled_regimes"] = enabled_regimes
    
    # Ensure risk_indicators exists for safety
    if "risk_indicators" not in payload:
        payload["risk_indicators"] = {}
    
    # Add execution loop specific fields if missing
    execution_loop_fields = {
        "request_id": payload.get("request_id") or f"req-{uuid.uuid4().hex[:12]}",
        "timestamp_utc": payload.get("timestamp_utc") or _utc_now_iso(),
        "correlation_id": payload.get("correlation_id") or f"corr-{uuid.uuid4().hex[:12]}",
    }
    
    payload.update(execution_loop_fields)
    
    # Log the transformation for debugging
    logger.debug(f"Prepared execution payload: industry={payload.get('industry_id')}, "
                f"profile={payload.get('profile_id')}, mode={evaluation_mode}")
    
    return payload


def validate_execution_request(raw_request: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate execution loop request before kernel processing.
    
    Args:
        raw_request: Request from execution loop
    
    Returns:
        Tuple of (is_valid, issues)
    """
    issues = []
    
    if not isinstance(raw_request, dict):
        issues.append("Request must be a dictionary")
        return False, issues
    
    # Check for required execution loop fields
    required_fields = ["action", "content"]
    for field in required_fields:
        if field not in raw_request:
            issues.append(f"Missing required field: {field}")
    
    # Validate action types
    valid_actions = [
        "LIST_PRODUCT", "POST_CONTENT", "EXPORT_DATA", "PROCESS_TRANSACTION", 
        "ACCESS_DATA", "MODIFY_DATA", "DELETE_DATA", "QUERY_DATA", "UPDATE_USER",
        "CREATE_ORDER", "CANCEL_ORDER", "REFUND", "SHIP_PRODUCT", "REVIEW_PRODUCT"
    ]
    action = raw_request.get("action")
    if action and action not in valid_actions:
        issues.append(f"Invalid action: {action}. Must be one of {valid_actions}")
    
    # Check for reasonable content size
    content = raw_request.get("content", "")
    if isinstance(content, str) and len(content) > 100000:  # 100KB limit
        issues.append(f"Content too large: {len(content)} characters")
    
    return len(issues) == 0, issues

# =========================================================
# GDPR (minimal) evaluator - MISSING FROM NEW KERNEL
# =========================================================
def evaluate_gdpr_rules(payload: dict) -> tuple[list[dict], dict]:
    """Minimal GDPR surface for export / lawful-basis checks.

    Conservative behavior:
    - Only emits a blocking VIOLATED when the payload explicitly indicates an EXPORT_DATA
    without lawful basis (export.lawful_basis == 'NONE'/empty, or violation_category matches).
    - Otherwise returns NOT_APPLICABLE/SATISFIED so we don't over-claim GDPR scope.
    """
    payload = payload or {}
    meta = payload.get("meta") or {}
    jurisdiction = str(meta.get("jurisdiction") or "").upper().strip()

    action = str(payload.get("action") or "").upper().strip()
    export = payload.get("export") or {}
    lawful_basis = str(export.get("lawful_basis") or "").upper().strip()

    risk = payload.get("risk_indicators") or {}
    violation_cat = str(risk.get("violation_category") or "").upper().strip()

    policies: list[dict] = []
    total_rules = 0
    passed = 0
    failed = 0
    blocking_failures = 0

    def emit(p: dict):
        nonlocal total_rules, passed, failed, blocking_failures
        total_rules += 1
        st = p.get("status")
        if st == "SATISFIED":
            passed += 1
        elif st == "VIOLATED":
            failed += 1
            if p.get("severity") in {"HIGH", "CRITICAL"}:
                blocking_failures += 1
        policies.append(p)

    # Applicability surface (EU/UK only)
    if jurisdiction not in {"EU", "UK"}:
        emit({
            "regime": "GDPR",
            "domain": "GDPR",
            "framework": "Data Protection",
            "domain_id": "GDPR",
            "policy_id": "GDPR:APPLICABILITY",
            "article": "GDPR:APPLICABILITY",
            "title": "Applicability",
            "category": "Applicability",
            "status": "NOT_APPLICABLE",
            "severity": "LOW",
            "trigger_type": "NOT_APPLICABLE",
            "impact_on_verdict": "Not applicable: jurisdiction not EU/UK.",
            "notes": "Not applicable: payload jurisdiction is not EU/UK.",
            "rule_ids": ["GDPR_APPLICABILITY_NA"],
            "evidence": {"jurisdiction": jurisdiction},
            "remediation": "",
            "violation_detail": "",
        })
        return policies, {
            "total_rules": total_rules,
            "passed": passed,
            "failed": failed,
            "blocking_failures": blocking_failures,
            "regime": "GDPR",
        }

    # Non-export actions: keep GDPR neutral in this minimal implementation
    if action != "EXPORT_DATA":
        emit({
            "regime": "GDPR",
            "domain": "GDPR",
            "framework": "Data Protection",
            "domain_id": "GDPR",
            "policy_id": "GDPR:EXPORT_LAWFUL_BASIS",
            "article": "GDPR Art. 6",
            "title": "Lawful basis for processing",
            "category": "Lawful basis",
            "status": "NOT_APPLICABLE",
            "severity": "LOW",
            "trigger_type": "GDPR_OBLIGATION",
            "impact_on_verdict": "Neutral non-applicable surface.",
            "notes": "Not applicable: action is not EXPORT_DATA.",
            "rule_ids": ["GDPR_ART6_LAWFUL_BASIS_NA"],
            "evidence": {"action": action},
            "remediation": "",
            "violation_detail": "",
        })
        return policies, {
            "total_rules": total_rules,
            "passed": passed,
            "failed": failed,
            "blocking_failures": blocking_failures,
            "regime": "GDPR",
        }

    # Export action: detect explicit unlawful signals
    unlawful_export = (lawful_basis in {"", "NONE", "NO", "NULL"}) or (violation_cat == "DATA_EXPORT_NONCOMPLIANT")

    if unlawful_export:
        emit({
            "regime": "GDPR",
            "domain": "GDPR",
            "framework": "Data Protection",
            "domain_id": "GDPR",
            "policy_id": "GDPR:ART6_LAWFUL_BASIS",
            "article": "GDPR Art. 6",
            "title": "Lawful basis required for personal-data export",
            "category": "Lawful basis",
            "status": "VIOLATED",
            "severity": "HIGH",
            "control_severity": "CRITICAL",
            "trigger_type": "GDPR_OBLIGATION",
            "impact_on_verdict": "Blocking violation: export without lawful basis.",
            "notes": "Export indicates no lawful basis (lawful_basis=NONE/empty or violation_category=DATA_EXPORT_NONCOMPLIANT).",
            "rule_ids": ["GDPR_ART6_EXPORT_NO_LAWFUL_BASIS"],
            "evidence": {
                "action": action,
                "export.dataset": export.get("dataset"),
                "export.lawful_basis": export.get("lawful_basis"),
                "violation_category": risk.get("violation_category"),
            },
            "remediation": "Require and validate a lawful basis (e.g., consent, contract, legal obligation) before exporting personal data; otherwise block and escalate to compliance review.",
            "violation_detail": "Export of patient/personal data requested without lawful basis.",
        })
    else:
        emit({
            "regime": "GDPR",
            "domain": "GDPR",
            "framework": "Data Protection",
            "domain_id": "GDPR",
            "policy_id": "GDPR:ART6_LAWFUL_BASIS",
            "article": "GDPR Art. 6",
            "title": "Lawful basis required for personal-data export",
            "category": "Lawful basis",
            "status": "SATISFIED",
            "severity": "LOW",
            "trigger_type": "GDPR_OBLIGATION",
            "impact_on_verdict": "Satisfied: lawful basis provided for export.",
            "notes": "Export request includes a lawful basis.",
            "rule_ids": ["GDPR_ART6_EXPORT_LAWFUL_BASIS_OK"],
            "evidence": {"export.lawful_basis": export.get("lawful_basis")},
            "remediation": "",
            "violation_detail": "",
        })

    return policies, {
        "total_rules": total_rules,
        "passed": passed,
        "failed": failed,
        "blocking_failures": blocking_failures,
        "regime": "GDPR",
    }

def _merge_resolver_output(l4: dict, out) -> None:
    """Merge resolver output into L4 in a tolerant way."""
    if out is None:
        return

    # Resolver returned a list of policy dicts
    if isinstance(out, list):
        l4.setdefault("policies_triggered", []).extend(out)
        return

    # Resolver returned a dict
    if isinstance(out, dict):
        if "policies_triggered" in out and isinstance(out["policies_triggered"], list):
            l4.setdefault("policies_triggered", []).extend(out["policies_triggered"])

        # Merge other keys without clobbering non-empty existing values
        for k, v in out.items():
            if k == "policies_triggered":
                continue
            if k not in l4 or l4[k] in (None, "", [], {}):
                l4[k] = v
        return

def _juris_ok(reg_jurisdiction: str | None, adra_jurisdiction: str | None) -> bool:
    """Return True if a regime jurisdiction should apply to an ADRA jurisdiction."""
    if not adra_jurisdiction:
        return True  # no filter requested
    if not reg_jurisdiction:
        return True  # missing metadata -> don't hide

    aj = str(adra_jurisdiction).upper().strip()
    rj = str(reg_jurisdiction).upper().strip()

    if aj in {"ALL"}:
        return True
    if rj in {"GLOBAL"}:
        return True

    # Parent -> child match
    if aj == "US":
        return rj == "US" or rj.startswith("US-")
    if aj == "EU":
        return rj == "EU" or rj.startswith("EU-")

    # Exact otherwise (e.g., US-NY)
    return rj == aj

def _evaluate_policies(
    payload: Dict[str, Any],
    enabled_regimes: Optional[List[str]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Evaluate kernel-native policy regimes ONLY.
    IMPORTANT: This function must NEVER widen scope.
    Executable registry regimes are run in run_gn_kernel (single call site).
    """
    payload = payload if isinstance(payload, dict) else {}

    enabled_canon = _canon_regime_set(enabled_regimes)  # None => unscoped

    policies: List[Dict[str, Any]] = []

    # --------------------------------------------
    # BASELINE ONLY WHEN NO EXPLICIT SCOPE EXISTS
    # --------------------------------------------
    if enabled_canon is None and _is_allow_baseline(payload):
        base = {
            "domain": "EU Digital Services Act (DSA)",
            "regime": "DSA",
            "framework": "Digital Sovereignty",
            "domain_id": "DSA",
            "trigger_type": "ALLOW_BASELINE",
        }
        policies.append(
            {
                **base,
                "article": "DSA Art. 34",
                "category": "Systemic risk assessment",
                "status": "SATISFIED",
                "severity": "LOW",
                "impact_on_verdict": "Baseline satisfied; supports ALLOW.",
                "rule_ids": ["DSA_ART_34_ALLOW_BASELINE"],
                "notes": "Harmless baseline input.",
            }
        )

        # Baseline: decorate only; no cross-regime stubs
        _decorate_policy_items(payload, policies)

    else:
        # --------------------------------------------
        # HARD EVALUATORS (built-in)
        # --------------------------------------------
        evaluator_map = {
            "DSA": evaluate_dsa_rules,
            "DMA": evaluate_dma_rules,
            "EU_AI_ACT": evaluate_eu_ai_act_rules,
            "GDPR": evaluate_gdpr_rules,
            "PCI_DSS": evaluate_pci_dss_rules,
            "HIPAA": evaluate_hipaa_rules,
            "FINRA": evaluate_finra_rules,
            "NYDFS_500": evaluate_nydfs_500_rules,
            "ISO_42001": evaluate_iso_42001_rules,
            "NIST_AI_RMF": evaluate_nist_ai_rmf_rules,
            "SAAS_TRANSACTION_INTEGRITY": evaluate_saas_transaction_integrity_rules,
        }

        # Determine regimes to run
        if enabled_canon is None:
            regimes_to_run = set(evaluator_map.keys())
        else:
            regimes_to_run = {r for r in enabled_canon if r in evaluator_map}

        for rid in sorted(regimes_to_run):
            fn = evaluator_map.get(rid)
            if not fn:
                continue
            out, _ = fn(payload)
            policies.extend(out or [])

        # --------------------------------------------
        # FINAL HARD SCOPE FILTER (authoritative)
        # --------------------------------------------
        if enabled_canon is not None:
            policies = [
                p for p in (policies or [])
                if isinstance(p, dict) and _canon_regime(p.get("regime")) in enabled_canon
            ]

            # --------------------------------------------
            # UNSUPPORTED REGIME SIGNAL (explicit & safe)
            # --------------------------------------------
            present = {_canon_regime(p.get("regime")) for p in policies if isinstance(p, dict)}
            missing = sorted([r for r in enabled_canon if r not in present])

            for r in missing:
                policies.append(
                    {
                        "domain": r,
                        "regime": r,
                        "framework": "Regime Surface",
                        "domain_id": r,
                        "article": f"{r}:UNSUPPORTED",
                        "category": "Regime not implemented",
                        "status": "UNSUPPORTED",
                        "severity": "LOW",  # must not drive DENY
                        "impact_on_verdict": "Enabled by scope but no evaluator produced output.",
                        "trigger_type": "UNSUPPORTED_REGIME",
                        "rule_ids": [f"{r}_UNSUPPORTED"],
                        "notes": "Kernel evaluator surface is incomplete for this enabled regime.",
                    }
                )
        else:
            # Global/unscoped mode: optional cross-regime surface
            _append_cross_regime_stubs(policies, None)

        # Decoration after scope logic settles
        _decorate_policy_items(payload, policies)

    # Summary (post-scope)
    def _norm_status(p: Dict[str, Any]) -> str:
        return str((p or {}).get("status", "")).upper()

    def _norm_sev(p: Dict[str, Any]) -> str:
        return str((p or {}).get("severity", "LOW")).upper()

    failed = sum(1 for p in policies if isinstance(p, dict) and _norm_status(p) == "VIOLATED")
    passed = sum(1 for p in policies if isinstance(p, dict) and _norm_status(p) == "SATISFIED")
    blocking = sum(
        1 for p in policies
        if isinstance(p, dict)
        and _norm_status(p) == "VIOLATED"
        and _norm_sev(p) in {"HIGH", "CRITICAL"}
        and p.get("enforcement_scope") == "TRANSACTION"

    )

    summary = {
        "total_rules": len([p for p in policies if isinstance(p, dict)]),
        "passed": passed,
        "failed": failed,
        "blocking_failures": int(blocking),
    }

    # Normalize domain_id last
    for p in policies:
        if isinstance(p, dict) and p.get("regime"):
            p["domain_id"] = _map_regime_to_taxonomy_domain_id(p.get("regime")) or p.get("domain_id")

    return policies, summary

def _run_executable_regimes(
    payload: Dict[str, Any],
    policies: List[Dict[str, Any]],
    enabled_regimes: Optional[List[str]] = None,
) -> None:
    """
    Execute registry regimes where:
    - l4_executable=True
    - (OPTIONAL) rid is in enabled_regimes (kernel scope gate)
    - jurisdiction matches
    - applicability(payload) is True
    - resolver is callable

    IMPORTANT INVARIANT:
    If enabled_regimes is provided, MUST NOT widen scope.
    """
    init_registry()

    enabled_canon = _canon_regime_set(enabled_regimes)  # None => unscoped

    adra_jurisdiction = (payload.get("meta", {}) or {}).get("jurisdiction")
    adra_jurisdiction = str(adra_jurisdiction).upper() if adra_jurisdiction else None

    for rid, spec in (REGIME_REGISTRY or {}).items():
        rid_c = _canon_regime(rid)

        # 0) 🔒 Scope gate
        if enabled_canon is not None and rid_c not in enabled_canon:
            continue

        # 1) Must be executable
        if not bool(spec.get("l4_executable", False)):
            continue

        # 2) Jurisdiction gate
        if not _juris_ok(spec.get("jurisdiction"), adra_jurisdiction):
            continue

        # 3) Applicability gate
        applicability = spec.get("applicability")
        if callable(applicability):
            try:
                if not bool(applicability(payload)):
                    continue
            except Exception:
                continue  # never crash kernel

        # 4) Resolver must be callable
        resolver = spec.get("resolver")
        if not callable(resolver):
            continue

        # 5) Run resolver safely
        try:
            out = resolver(payload)
        except Exception:
            continue  # never crash kernel

        # Accept list OR dict outputs
        if isinstance(out, list):
            emitted = out
        elif isinstance(out, dict):
            emitted = out.get("policies_triggered") or []
        else:
            emitted = []

        if not isinstance(emitted, list) or not emitted:
            continue

        for p in emitted:
            p.setdefault("regime", rid_c)
            p.setdefault("domain", spec.get("display_name") or spec.get("domain") or rid_c)
            p.setdefault("framework", spec.get("framework") or "")
            p.setdefault("domain_id", rid_c)

            p.setdefault("policy_id", p.get("policy_id") or f"{rid_c}:STUB")
            p.setdefault("article", p.get("article") or p.get("policy_id") or f"{rid_c}:POLICY")

            p.setdefault("title", p.get("title") or p.get("category") or "Policy obligation")
            p.setdefault("category", p.get("category") or p.get("title") or "Policy obligation")

            p.setdefault("status", "NOT_APPLICABLE")
            p.setdefault("severity", "LOW")
            p.setdefault("trigger_type", p.get("trigger_type") or p.get("status") or "UNKNOWN")

            rationale = p.get("rationale") or p.get("notes") or ""
            p.setdefault("impact_on_verdict", p.get("impact_on_verdict") or rationale)
            p.setdefault("notes", p.get("notes") or rationale)

            rid_val = p.get("policy_id") or f"{rid_c}:STUB"
            p.setdefault("rule_ids", p.get("rule_ids") or [rid_val])

            policies.append(p)

def build_article_ledger_rows(adra: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    l1 = adra.get("L1_the_verdict_and_constitutional_outcome", {}) or {}
    l3 = adra.get("L3_rule_level_trace", {}) or {}
    l4 = adra.get("L4_policy_lineage_and_constitution", {}) or {}

    ts = (
        adra.get("timestamp_utc")
        or l1.get("timestamp_utc")
        or (adra.get("provenance", {}) or {}).get("received_at_utc")
        or _utc_now_iso()
    )
    adra_id = adra.get("adra_id") or "UNKNOWN"
    adra_hash = adra.get("adra_hash")

    policies = l4.get("policies_triggered") or []
    if isinstance(policies, list) and policies:
        for p in policies:
            if not p.get("article"):
                p["article"] = "UNSPECIFIED"

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
                    "why_triggered": p.get("why_triggered") or p.get("rationale") or p.get("notes") or "",
                }
            )
        return rows

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

# =========================================================
# ENHANCED TELEMETRY WITH ERROR TRACKING
# =========================================================

class EvaluationTelemetry:
    """Capture performance and quality metrics with error tracking."""
    
    def __init__(self):
        self.metrics = {
            "layer_durations_ms": defaultdict(list),
            "policy_counts": [],
            "evaluation_times": [],
            "rule_coverage": defaultdict(int),
            "error_counts": defaultdict(int),
            "warnings": [],
        }
        self.start_time = None
        self.current_evaluation_id = None
    
    def start_evaluation(self, evaluation_id: Optional[str] = None):
        """Start timing evaluation."""
        self.start_time = time.perf_counter()
        self.current_evaluation_id = evaluation_id or str(uuid.uuid4())
        logger.debug(f"Starting evaluation: {self.current_evaluation_id}")
    
    def record_layer_duration(self, layer: str, duration_ms: float):
        """Record duration for a specific layer."""
        self.metrics["layer_durations_ms"][layer].append(duration_ms)
        if duration_ms > 1000:  # Log slow layers
            logger.warning(f"Slow layer {layer}: {duration_ms:.2f}ms")
    
    def record_policy_count(self, count: int):
        """Record number of policies triggered."""
        self.metrics["policy_counts"].append(count)
        if count > KernelConfig.SAFETY_LIMITS["max_policies_per_evaluation"]:
            logger.error(f"Policy count {count} exceeds safety limit")
    
    def record_rule_coverage(self, regime: str, article: str, status: str):
        """Record rule coverage statistics."""
        key = f"{regime}.{article}.{status}"
        self.metrics["rule_coverage"][key] += 1
    
    def record_error(self, error_type: str, message: str, details: Optional[Dict] = None):
        """Record an error occurrence."""
        self.metrics["error_counts"][error_type] += 1
        error_entry = {
            "type": error_type,
            "message": message,
            "timestamp": _utc_now_iso(),
            "evaluation_id": self.current_evaluation_id,
        }
        if details:
            error_entry["details"] = details
        self.metrics["warnings"].append(error_entry)
        logger.error(f"{error_type}: {message}")
    
    def record_warning(self, warning_type: str, message: str):
        """Record a warning."""
        warning_entry = {
            "type": warning_type,
            "message": message,
            "timestamp": _utc_now_iso(),
            "evaluation_id": self.current_evaluation_id,
        }
        self.metrics["warnings"].append(warning_entry)
        logger.warning(f"{warning_type}: {message}")
    
    def end_evaluation(self) -> Tuple[float, bool]:
        """End evaluation and compute total duration."""
        if self.start_time:
            end_time = time.perf_counter()
            duration_ms = (end_time - self.start_time) * 1000
            self.metrics["evaluation_times"].append(duration_ms)
            
            # Check performance threshold
            if duration_ms > KernelConfig.QUALITY_GATES["maximum_evaluation_time_ms"]:
                self.record_warning(
                    "PERFORMANCE_WARNING",
                    f"Evaluation took {duration_ms:.2f}ms, exceeding threshold"
                )
                return duration_ms, False
            
            logger.debug(f"Evaluation completed in {duration_ms:.2f}ms")
            return duration_ms, True
        
        return 0.0, False
    
    def get_summary(self) -> Dict[str, Any]:
        """Get telemetry summary."""
        summary = {
            "total_evaluations": len(self.metrics["evaluation_times"]),
            "avg_evaluation_time_ms": 0.0,
            "avg_policy_count": 0.0,
            "layer_performance": {},
            "rule_coverage_summary": {},
            "error_summary": dict(self.metrics["error_counts"]),
            "warnings": self.metrics["warnings"][-100:],  # Last 100 warnings
            "current_evaluation_id": self.current_evaluation_id,
        }
        
        if self.metrics["evaluation_times"]:
            summary["avg_evaluation_time_ms"] = sum(self.metrics["evaluation_times"]) / len(self.metrics["evaluation_times"])
        
        if self.metrics["policy_counts"]:
            summary["avg_policy_count"] = sum(self.metrics["policy_counts"]) / len(self.metrics["policy_counts"])
        
        for layer, durations in self.metrics["layer_durations_ms"].items():
            if durations:
                summary["layer_performance"][layer] = {
                    "avg_ms": sum(durations) / len(durations),
                    "min_ms": min(durations),
                    "max_ms": max(durations),
                    "count": len(durations),
                    "p95_ms": sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 1 else durations[0],
                }
        
        # Aggregate rule coverage
            coverage_summary = defaultdict(dict)
            for key, count in self.metrics["rule_coverage"].items():
                parts = key.split(".")
                if len(parts) == 3:
                    regime, article, status = parts
                    regime_key = f"{regime}.{article}"
                    # Use .get() to handle missing keys
                    coverage_summary[regime_key]["total"] = coverage_summary[regime_key].get("total", 0) + count
                    coverage_summary[regime_key][status.lower()] = coverage_summary[regime_key].get(status.lower(), 0) + count
            
            summary["rule_coverage_summary"] = dict(coverage_summary)
            
            return summary
        
        pass  # TEMPORARY FIX - was: return summary
    
    def clear_current(self):
        """Clear current evaluation data (keep historical)."""
        self.start_time = None
        self.current_evaluation_id = None

# Global telemetry instance
_TELEMETRY = EvaluationTelemetry()

# =========================================================
# NEW: UTILITY FUNCTIONS FOR ERROR HANDLING
# =========================================================

def _create_error_adra(
    evaluation_id: str,
    error_message: str,
    issues: List[str],
    timestamp: str,
    payload: Any,
    kernel_timeline: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Create an ADRA-v0.5-shaped emergency artifact when the kernel fails."""
    adra_id = f"error-{uuid.uuid4().hex[:16]}"
    ts = timestamp or _utc_now_iso()

    # Best-effort scope hints
    industry_id = None
    profile_id = None
    enabled_regimes: List[str] = []
    payload_summary = None

    if isinstance(payload, dict):
        industry_id = payload.get("industry_id")
        profile_id = payload.get("profile_id") or payload.get("industry_profile_id")
        er = payload.get("enabled_regimes")
        if isinstance(er, list):
            enabled_regimes = [_canon_regime_id(x) for x in er if x]
        payload_summary = {
            "action": payload.get("action"),
            "jurisdiction": (payload.get("meta") or {}).get("jurisdiction"),
            "keys_present": list(payload.keys()),
        }
    else:
        payload_summary = {"type": type(payload).__name__}

    # Minimal but schema-coherent ADRA
    error_adra: Dict[str, Any] = {
        "adra_id": adra_id,
        "timestamp_utc": ts,
        "evaluation_id": evaluation_id,
        "gnce_version": KernelConfig.VERSION,
        "industry_id": industry_id,
        "profile_id": profile_id,
        "enabled_regimes": enabled_regimes,
        "decision_bundle_id": f"bundle-{evaluation_id}",
        "kernel_execution_timeline": list(kernel_timeline or []),
        "error": {
            "message": error_message,
            "issues": issues,
            "timestamp": ts,
        },

        # L0
        "L0_structural_validation": {
            "layer": "L0",
            "title": "Emergency Error Handler",
            "validated": False,
            "issues": issues,
            "severity": "CRITICAL",
            "evidence": {"payload_summary": payload_summary},
            "decision_gate": {"allow_downstream": False, "block_reason": error_message},
        },

        # L1
        "L1_the_verdict_and_constitutional_outcome": {
            "layer": "L1",
            "title": "Emergency Verdict",
            "validated": False,
            "decision_outcome": "ERROR",
            "severity": "CRITICAL",
            "rationale": "Kernel encountered a critical error before producing a reliable decision.",
            "constitutional": {
                "clause": "GNCE Emergency Clause — Kernel failure requires immediate human intervention.",
                "justification": error_message,
            },
            "evidence": {"error": error_message},
            "summary": {"satisfied": 0, "violated": 0},
        },

        # L2 (best-effort)
        "L2_input_snapshot_and_provenance": {
            "layer": "L2",
            "title": "Input Snapshot & Deterministic Record Anchor (DRA)",
            "validated": False,
            "issues": ["Emergency path: input snapshot may be partial."],
            "severity": "HIGH",
            "input_snapshot": payload if isinstance(payload, dict) else {"raw_input": str(payload)[:500]},
            "input_hash_sha256": _sha256_of(payload) if isinstance(payload, (dict, list, str, int, float, bool, type(None))) else None,
            "provenance": {"received_at_utc": ts, "evaluation_id": evaluation_id},
            "decision_gate": {"allow_downstream": False, "block_reason": error_message},
        },

        # L3-L6 placeholders so UI can render the layer strip consistently
        "L3_deterministic_rule_engine": {
            "layer": "L3",
            "title": "Deterministic Rule Engine (DRE)",
            "validated": False,
            "issues": ["Emergency path: rules not evaluated."],
            "severity": "HIGH",
            "summary": {"total_rules": 0, "passed": 0, "failed": 0, "blocking_failures": 0},
            "decision_gate": {"allow_downstream": False, "block_reason": error_message},
        },
        "L4_policy_lineage_and_constitution": {
            "layer": "L4",
            "title": "Policy Lineage & Constitution Binding",
            "validated": False,
            "issues": ["Emergency path: policy lineage not computed."],
            "severity": "HIGH",
            "policies_triggered": [],
            "constitution_hash": None,
            "decision_gate": {"allow_downstream": False, "block_reason": error_message},
        },
        "L5_integrity_and_tokenization": {
            "layer": "L5",
            "title": "CET Integrity & Tokenization",
            "validated": False,
            "issues": ["Emergency path: integrity tokens not generated."],
            "severity": "HIGH",
            "content_hash_sha256": None,
            "cet_tokens": [],
            "decision_gate": {"allow_downstream": False, "block_reason": error_message},
        },
        "L6_execution_trace_and_sars": {
            "layer": "L6",
            "title": "Execution Trace & SARS Evidence",
            "validated": False,
            "issues": ["Emergency path: no execution trace."],
            "severity": "HIGH",
            "sars_entries": [],
            "decision_gate": {"allow_downstream": False, "block_reason": error_message},
        },

        # L7
        "L7_veto_and_execution_feedback": {
            "layer": "L7",
            "title": "Emergency Veto",
            "validated": False,
            "execution_authorized": False,
            "veto_triggered": True,
            "veto_category": "CRITICAL_ERROR",
            "escalation_required": "IMMEDIATE_HUMAN_REVIEW",
            "veto_layer": "KERNEL",
            "origin_layer": "KERNEL",
            "trigger_layer": "KERNEL",
            "clause": "GNCE Emergency Clause — Kernel failure requires immediate human intervention.",
            "veto_basis": [{"article": "KERNEL.FAILURE", "status": "VIOLATED", "explanation": error_message}],
            "severity": "CRITICAL",
            "issues": issues,
        },

        "governance_context": {
            "emergency_mode": True,
            "error": error_message,
            "timestamp": ts,
        },
        "emergency": True,
    }

    # Ensure a stable top-level constitution_hash exists for ledger compliance
    if not error_adra.get("constitution_hash"):
        error_adra["constitution_hash"] = "sha256:EMERGENCY_ERROR_ADRA"

    # Hash the artifact
    canon = dict(error_adra)
    canon.pop("adra_hash", None)
    error_adra["adra_hash"] = _sha256_of(canon)

    # Validate v0.5 shape if validator exists; never crash emergency path.
    try:
        validate_adra_v05(error_adra)
    except Exception:
        pass

    return error_adra

def _regime_prefix(reg: str) -> str:
    """Get regime prefix for filtering."""
    prefixes = {
        "DSA": "DSA",
        "DMA": "DMA",
        "EU_AI_ACT": "AI Act",
        "ISO_42001": "ISO/IEC",
        "NIST_AI_RMF": "NIST AI RMF",
        "GDPR": "GDPR",
        "PCI_DSS": "PCI",
        "HIPAA": "HIPAA",
        "FINRA": "FINRA",
        "NYDFS_500": "NYDFS",
    }
    return prefixes.get(reg, reg)

def _derive_regime_decision(reg_policies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Derive regime-local decision."""
    def _norm_status(p: Dict[str, Any]) -> str:
        return str((p or {}).get("status", "")).upper()
    
    def _norm_sev(p: Dict[str, Any]) -> str:
        return str((p or {}).get("severity", "LOW")).upper()
    
    violations = [
        p for p in reg_policies
        if isinstance(p, dict) and _norm_status(p) == "VIOLATED"
    ]
    hi_crit = [p for p in violations if _norm_sev(p) in {"HIGH", "CRITICAL"}
    and p.get("enforcement_scope") == "TRANSACTION" ]
    decision_outcome = "DENY" if hi_crit else "ALLOW"
    
    highest = "LOW"
    for p in violations:
        sev = _norm_sev(p)
        if sev == "CRITICAL":
            highest = "CRITICAL"
            break
        if sev == "HIGH":
            highest = "HIGH"
        elif sev == "MEDIUM" and highest not in {"HIGH", "CRITICAL"}:
            highest = "MEDIUM"
    
    return {
        "decision": decision_outcome,
        "severity": highest,
        "blocking": len(hi_crit),
        "hi_crit": hi_crit,
    }

def _sha256_json(obj: Any) -> str:
    """Compute SHA256 hash of JSON object."""
    return _sha256_of(obj)

def _check_quality_gates(adra: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Check ADRA against quality gates."""
    failures = []
    
    # Check minimum evidence count
    l4 = adra.get("L4_policy_lineage_and_constitution", {})
    policies = l4.get("policies_triggered", [])
    if len(policies) < KernelConfig.QUALITY_GATES["minimum_evidence_count"]:
        failures.append(f"Only {len(policies)} policies triggered, minimum is {KernelConfig.QUALITY_GATES['minimum_evidence_count']}")
    
    # Check required fields
    for field in KernelConfig.QUALITY_GATES["required_fields"]:
        if field not in adra or not adra[field]:
            failures.append(f"Missing required field: {field}")
    
    return len(failures) == 0, failures

def analyze_rule_coverage(policies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze rule coverage from policies."""
    coverage = {
        "total_policies": len(policies),
        "by_status": defaultdict(int),
        "by_severity": defaultdict(int),
        "by_regime": defaultdict(lambda: {"total": 0, "violated": 0, "satisfied": 0}),
    }
    
    for policy in policies:
        if not isinstance(policy, dict):
            continue
            
        status = policy.get("status", "UNKNOWN")
        severity = policy.get("severity", "UNKNOWN")
        regime = policy.get("regime", "UNKNOWN")
        
        coverage["by_status"][status] += 1
        coverage["by_severity"][severity] += 1
        
        coverage["by_regime"][regime]["total"] += 1
        if status == "VIOLATED":
            coverage["by_regime"][regime]["violated"] += 1
        elif status == "SATISFIED":
            coverage["by_regime"][regime]["satisfied"] += 1
    
    return coverage

# =========================================================
# ENHANCED MAIN KERNEL FUNCTION WITH DEBUGGING SUPPORT
# =========================================================

def run_gn_kernel(payload: Dict[str, Any], debug_mode: bool = False) -> Dict[str, Any]:
    """
    GNCE Sovereign Kernel — SINGLE RUN MODEL (no per-regime ADRAs)
    
    Args:
        payload: Input payload for evaluation
        debug_mode: If True, include additional debugging information
        
    Returns:
        Complete ADRA with evaluation results
        
    Raises:
        KernelError: If kernel encounters a critical error
        ValidationError: If validation fails
        RoutingError: If industry/profile routing fails
        ScopeError: If enabled regimes scope is invalid
    """
    
    # Store original payload for debugging
    original_payload = copy.deepcopy(payload) if debug_mode else payload
    
    try:
        # Initialize evaluation context with debugging support
        evaluation_id = str(uuid.uuid4())
        logger.info(f"Starting kernel evaluation: {evaluation_id}")
        
        if debug_mode and KernelConfig.DEBUG["log_payload_summary"]:
            payload_summary = {
                "keys": list(payload.keys()),
                "size_bytes": len(json.dumps(payload)) if payload else 0,
                "has_risk_indicators": "risk_indicators" in payload,
                "has_meta": "meta" in payload,
                "action": payload.get("action"),
            }
            logger.debug(f"Payload summary: {payload_summary}")
        
        # Start telemetry
        _TELEMETRY.start_evaluation(evaluation_id)
        start_time = time.perf_counter()
        
        # Get evaluation mode with validation
        evaluation_mode = payload.get("evaluation_mode", "STRICT")
        if evaluation_mode not in KernelConfig.EVALUATION_MODES:
            logger.warning(f"Invalid evaluation mode '{evaluation_mode}', defaulting to STRICT")
            evaluation_mode = "STRICT"
        
        evaluation_context_id = payload.get("evaluation_context_id") or str(uuid.uuid4())
        
        # Normalize payload with size checking
        payload = _normalize_payload(payload)
        
        import inspect
        logger.debug(f"KERNEL LOADED FROM: {inspect.getfile(run_gn_kernel)}")
        
        # ---------------------------
        # ONE canonical timestamp per run (never overwritten)
        # ---------------------------
        received_at_utc = (
            payload.get("timestamp_utc")
            or (payload.get("provenance", {}) or {}).get("received_at_utc")
            or _utc_now_iso()
        )
        
        # ONE correlation token per kernel run
        decision_bundle_id = "bundle-" + uuid.uuid4().hex[:12]
        
        kernel_timeline: List[Dict[str, Any]] = []
        
        def _event(stage: str, detail: str = "", level: str = "INFO"):
            """Log timeline event with level."""
            event_data = {"ts_utc": _utc_now_iso(), "stage": stage, "detail": detail}
            kernel_timeline.append(event_data)
            
            if level == "ERROR":
                logger.error(f"{stage}: {detail}")
            elif level == "WARNING":
                logger.warning(f"{stage}: {detail}")
            else:
                logger.debug(f"{stage}: {detail}")
        
        _event("REQUEST_RECEIVED", f"Evaluation {evaluation_id} received by GNCE sovereign kernel")
        
        # =========================================================
        # L0 — Pre-Execution Validation (Enhanced)
        # =========================================================
        l0_start = time.perf_counter()
        l0_issues: List[str] = []
        
        try:
            if not isinstance(payload, dict):
                l0_issues.append("Payload is not a JSON object.")
                _TELEMETRY.record_error("VALIDATION_ERROR", "Payload is not a dict")
            
            if not payload:
                l0_issues.append("Payload is empty; defaults applied.")
                _TELEMETRY.record_warning("EMPTY_PAYLOAD", "Payload is empty")
            
            # Check for required fields if specified
            required_fields = payload.get("required_fields")
            if required_fields and isinstance(required_fields, list):
                for field in required_fields:
                    if field not in payload:
                        l0_issues.append(f"Missing required field: {field}")
            
            is_dict = isinstance(payload, dict)
            keys_present = list(payload.keys()) if is_dict else []
            
            # Check for suspicious payload patterns
            if is_dict:
                # Very large payloads
                payload_size = len(json.dumps(payload))
                if payload_size > 1000000:  # 1MB
                    _TELEMETRY.record_warning("LARGE_PAYLOAD", f"Payload size: {payload_size} bytes")
                
                # Deeply nested structures
                def check_nesting(obj, depth=0, max_depth=10):
                    if depth > max_depth:
                        return True
                    if isinstance(obj, dict):
                        for v in obj.values():
                            if check_nesting(v, depth + 1, max_depth):
                                return True
                    elif isinstance(obj, list):
                        for item in obj:
                            if check_nesting(item, depth + 1, max_depth):
                                return True
                    return False
                
                if check_nesting(payload):
                    _TELEMETRY.record_warning("DEEP_NESTING", "Payload has deep nesting")
            
            l0_validated = (len([x for x in l0_issues if "not a json object" in x.lower()]) == 0)
            
        except Exception as e:
            logger.error(f"Error during L0 validation: {e}")
            l0_issues.append(f"Validation error: {str(e)}")
            l0_validated = False
            _TELEMETRY.record_error("L0_VALIDATION_ERROR", str(e))
        
        l0 = {
            "layer": "L0",
            "title": "Pre-Execution Constitutional Validation",
            "validated": l0_validated,
            "issues": l0_issues,
            "severity": "LOW" if l0_validated else "HIGH",
            "constitutional": {
                "clause": "GNCE Sec. 0.1 — Inputs must be structurally valid JSON objects.",
                "justification": "L0 verifies structural integrity before downstream layers execute.",
                "explainability": {
                    "why_required": "GNCE must guarantee deterministic inputs.",
                    "impact": "If L0 fails, downstream computation must be blocked.",
                },
            },
            "checks": [
                {
                    "check_id": "L0.JSON_OBJECT",
                    "description": "Payload is a JSON object (dict).",
                    "pass": bool(is_dict),
                    "observed": type(payload).__name__,
                },
                {
                    "check_id": "L0.KEYS_CAPTURED",
                    "description": "Payload keys captured for evidence.",
                    "pass": True,
                    "observed": f"keys={len(keys_present)}",
                },
            ],
            "evidence": {
                "input_shape": type(payload).__name__,
                "keys_present": keys_present,
                "issues_count": len(l0_issues),
                "evaluation_id": evaluation_id,
            },
            "decision_gate": {
                "allow_downstream": l0_validated,
                "block_reason": None if l0_validated else "L0 structural validation failed.",
            },
        }
        
        l0_duration = (time.perf_counter() - l0_start) * 1000
        _TELEMETRY.record_layer_duration("L0", l0_duration)
        
        if not l0_validated:
            _event("L0_VALIDATION_FAILED", f"issues_count={len(l0_issues)}", "ERROR")
            if KernelConfig.DEBUG["trace_exceptions"]:
                error_adra = _create_error_adra(
                    evaluation_id, 
                    "L0 validation failed", 
                    l0_issues, 
                    received_at_utc,
                    original_payload if debug_mode else payload
                )
                return error_adra
        else:
            _event("L0_COMPLETED", f"validated={l0_validated} issues_count={len(l0_issues)}")
        
        # =========================================================
        # INDUSTRY → PROFILE ROUTING (Enhanced with error handling)
        # =========================================================
        routing_start = time.perf_counter()
        
        try:
            industry_id, profile_id, profile_spec = resolve_industry_and_profile(payload)
            
            # Debug logging
            if debug_mode:
                logger.debug(f"Routing result: industry={industry_id}, profile={profile_id}")
                logger.debug(f"Profile spec keys: {list(profile_spec.keys()) if profile_spec else 'None'}")
            
            # Stamp safe, portable profile classification hints onto payload.meta for downstream rule gating.
            meta = payload.setdefault("meta", {}) if isinstance(payload, dict) else {}
            if isinstance(meta, dict):
                meta.setdefault("is_vlop", bool(profile_spec.get("is_vlop")) or str(profile_id).startswith("VLOP_"))
                meta.setdefault("platform_classification", profile_spec.get("platform_classification", ""))
                meta.setdefault("targets_minors", bool(profile_spec.get("targets_minors", False)))
                meta.setdefault("routing_debug", {
                    "industry_id": industry_id,
                    "profile_id": profile_id,
                    "profile_found": bool(profile_spec),
                })
            
            if not industry_id or not profile_id or not isinstance(profile_spec, dict):
                error_msg = (
                    "GNCE ROUTING ERROR: industry/profile resolution failed "
                    f"(payload_industry_id={payload.get('industry_id')}, "
                    f"payload_profile_id={payload.get('profile_id') or payload.get('industry_profile_id')})"
                )
                logger.error(error_msg)
                _TELEMETRY.record_error("ROUTING_ERROR", error_msg)
                raise RoutingError(
                    message=error_msg,
                    industry_id=payload.get('industry_id'),
                    profile_id=payload.get('profile_id') or payload.get('industry_profile_id'),
                )
            
            # ✅ canonical + dedupe + deterministic order
            enabled_regimes = sorted({
                _canon_regime_id(r)
                for r in (profile_spec.get("enabled_regimes") or [])
                if r
            })
            
            # Log enabled regimes for debugging
            logger.debug(f"Profile enabled regimes: {enabled_regimes}")
            
            # Check if we have too many regimes
            if len(enabled_regimes) > KernelConfig.SAFETY_LIMITS["max_regimes_per_profile"]:
                _TELEMETRY.record_warning(
                    "MANY_REGIMES", 
                    f"Profile has {len(enabled_regimes)} enabled regimes"
                )
                # Take only first N for safety
                enabled_regimes = enabled_regimes[:KernelConfig.SAFETY_LIMITS["max_regimes_per_profile"]]
            
            # Additive router scope: union profile scope with router suggestions.
            if _route_regimes_fallback is not None:
                try:
                    routed = _route_regimes_fallback(payload) or []
                    added_regimes = []
                    for r in routed:
                        rid = _canon_regime_id(r)
                        if rid and rid not in enabled_regimes:
                            enabled_regimes.append(rid)
                            added_regimes.append(rid)
                    enabled_regimes = sorted(set(enabled_regimes))
                    if added_regimes:
                        logger.debug(f"Router added regimes: {added_regimes}")
                except Exception as e:
                    logger.warning(f"Router fallback failed: {e}")
                    _TELEMETRY.record_warning("ROUTER_FAILED", str(e))
            
            # 🛡️ Kernel safety augmentation
            try:
                ri = payload.get('risk_indicators') or {}
                if industry_id == 'ECOMMERCE':
                    fraud_suspected = bool(ri.get('fraud_suspected'))
                    prev_viol = int(ri.get('previous_violations') or 0)
                    if fraud_suspected or prev_viol >= 3:
                        eti_id = 'ECOMMERCE_TRANSACTION_INTEGRITY'
                        if eti_id not in enabled_regimes:
                            enabled_regimes = sorted(set(enabled_regimes + [eti_id]))
                            logger.debug(f"Added {eti_id} due to fraud risk")
                
                # Healthcare augmentation
                jur_u = str((payload.get("meta") or {}).get("jurisdiction") or "").upper().strip()
                if str(industry_id).upper().strip() == "HEALTHCARE":
                    act_u = str(payload.get("action") or "").upper().strip()
                    export = payload.get("export") or {}
                    lawful_u = str(export.get("lawful_basis") or "").upper().strip()
                    viol_cat_u = str(ri.get("violation_category") or "").upper().strip()

                    # EU/UK exports without lawful basis should be blockable under GDPR surface.
                    if jur_u in {"EU", "UK"} and act_u == "EXPORT_DATA":
                        if lawful_u in {"", "NONE", "NO", "NULL"} or viol_cat_u == "DATA_EXPORT_NONCOMPLIANT":
                            if "GDPR" not in enabled_regimes:
                                enabled_regimes = sorted(set(enabled_regimes + ["GDPR"]))
                                logger.debug("Added GDPR for healthcare export")

                    # US healthcare: ensure HIPAA surface exists if profile forgot it.
                    if jur_u == "US":
                        if "HIPAA" not in enabled_regimes:
                            enabled_regimes = sorted(set(enabled_regimes + ["HIPAA"]))
                            logger.debug("Added HIPAA for US healthcare")
            except Exception as e:
                logger.warning(f"Safety augmentation failed: {e}")
                _TELEMETRY.record_warning("SAFETY_AUGMENTATION_FAILED", str(e))
            
            if not enabled_regimes:
                error_msg = (
                    "GNCE SCOPE ERROR: profile has no enabled_regimes "
                    f"(industry_id={industry_id}, profile_id={profile_id})"
                )
                logger.error(error_msg)
                _TELEMETRY.record_error("SCOPE_ERROR", error_msg)
                raise ScopeError(
                    message=error_msg,
                    enabled_regimes=enabled_regimes,
                )
            
            # 🔒 Authoritative stamping (kernel wins)
            payload["industry_id"] = industry_id
            payload["profile_id"] = profile_id
            
        except (RoutingError, ScopeError):
            # Re-raise kernel errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error during routing: {e}")
            _TELEMETRY.record_error("ROUTING_UNEXPECTED", str(e), {"traceback": traceback.format_exc()})
            raise RoutingError(
                message=f"Unexpected routing error: {str(e)}",
                industry_id=payload.get('industry_id'),
                profile_id=payload.get('profile_id') or payload.get('industry_profile_id'),
            )
        
        routing_duration = (time.perf_counter() - routing_start) * 1000
        _TELEMETRY.record_layer_duration("ROUTING", routing_duration)
        
        _event(
            "ROUTED_TO_PROFILE",
            f"industry_id={industry_id} profile_id={profile_id} enabled_regimes={len(enabled_regimes)}",
        )
        
        # =========================================================
        # L2 — Input snapshot + provenance (hash early)
        # =========================================================
        l2_start = time.perf_counter()
        
        try:
            input_hash = _sha256_of(payload)
            
            l2 = {
                "layer": "L2",
                "title": "Input Snapshot & Deterministic Record Anchor (DRA)",
                "validated": True,
                "issues": [],
                "severity": "LOW",
                "input_snapshot": payload if debug_mode else {},  # Only include full payload in debug mode
                "input_hash_sha256": input_hash,
                "provenance": {
                    "received_at_utc": received_at_utc,  # canonical
                    "format_valid": isinstance(payload, dict),
                    "fields_present": list(payload.keys()) if isinstance(payload, dict) else [],
                    "evaluation_id": evaluation_id,
                },
                "constitutional": {
                    "clause": "GNCE Sec. 2.2 — Every ADRA must bind to a deterministic input hash.",
                    "explainability": {
                        "headline": "INPUT BOUND — payload is cryptographically anchored to this ADRA.",
                        "impact": "The hash is carried into L5 CET integrity tokens.",
                    },
                },
                "checks": [
                    {"check_id": "L2.INPUT_HASH_PRESENT", "description": "Input hash computed.", "pass": bool(input_hash), "observed": input_hash[:32] + "..."},
                    {"check_id": "L2.PROVENANCE_CAPTURED", "description": "Provenance captured.", "pass": True, "observed": received_at_utc},
                ],
                "evidence": {
                    "input_shape": type(payload).__name__,
                    "keys_present": list(payload.keys()) if isinstance(payload, dict) else [],
                    "received_at_utc": received_at_utc,
                    "input_hash": input_hash,
                },
                "decision_gate": {"allow_downstream": True, "block_reason": None},
            }
            
        except Exception as e:
            logger.error(f"Error during L2: {e}")
            _TELEMETRY.record_error("L2_ERROR", str(e))
            # Create minimal L2 in case of error
            l2 = {
                "layer": "L2",
                "title": "Input Snapshot & Deterministic Record Anchor (DRA)",
                "validated": False,
                "issues": [f"L2 processing error: {str(e)}"],
                "severity": "HIGH",
                "input_hash_sha256": "ERROR",
                "provenance": {"received_at_utc": received_at_utc, "format_valid": False},
                "constitutional": {"clause": "GNCE Sec. 2.2 — Every ADRA must bind to a deterministic input hash."},
                "checks": [],
                "evidence": {"error": str(e)},
                "decision_gate": {"allow_downstream": False, "block_reason": f"L2 error: {str(e)}"},
            }
        
        l2_duration = (time.perf_counter() - l2_start) * 1000
        _TELEMETRY.record_layer_duration("L2", l2_duration)
        
        _event("L2_SNAPSHOT_HASHED", f"input_hash={input_hash[:18]}...")
        
        # =========================================================
        # L3 + L4 — Policy evaluation (STRICTLY SCOPED)
        # =========================================================
        l3l4_start = time.perf_counter()
        
        try:
            # IMPORTANT: _evaluate_policies MUST accept enabled_regimes and enforce scope
            policies, rule_summary = _evaluate_policies(payload, enabled_regimes=enabled_regimes)
            policies = _apply_dsa_vlop_gating(policies, payload)
            
            # Execute registry regimes (l4_executable=True) — ALSO SCOPE-GATED
            try:
                _run_executable_regimes(payload, policies, enabled_regimes)
            except Exception as e:
                logger.warning(f"Registry regime execution failed: {e}")
                _TELEMETRY.record_warning("REGISTRY_REGIME_FAILED", str(e))
            
            # Final hard filter (belt-and-suspenders): policies MUST be in-scope
            policies = _filter_policies_by_enabled_regimes(policies, enabled_regimes)
            
            # Scope invariant
            if enabled_regimes and not any(isinstance(p, dict) for p in (policies or [])):
                error_msg = "GNCE SCOPE ERROR: enabled_regimes specified but no policies produced."
                logger.error(error_msg)
                _TELEMETRY.record_error("SCOPE_VIOLATION", error_msg)
                
                # Create stub policies for each enabled regime to avoid crashing
                for regime in enabled_regimes:
                    policies.append({
                        "domain": regime,
                        "regime": regime,
                        "framework": "Regime Surface",
                        "domain_id": regime,
                        "article": f"{regime}:NO_POLICIES",
                        "category": "No policies produced",
                        "status": "NOT_APPLICABLE",
                        "severity": "LOW",
                        "trigger_type": "SCOPE_VIOLATION",
                        "impact_on_verdict": "Enabled by scope but no policies were produced.",
                        "notes": f"Scope violation: regime {regime} was enabled but no policies produced.",
                        "rule_ids": [f"{regime}_SCOPE_VIOLATION"],
                        "evidence": {"enabled_regimes": enabled_regimes},
                        "remediation": "Check regime implementation or profile configuration.",
                        "violation_detail": "",
                    })
                
                logger.warning(f"Created stub policies for {len(enabled_regimes)} regimes with no output")
            
            # Recompute summary from the final merged policy list
            def _norm_status(p: Dict[str, Any]) -> str:
                return str((p or {}).get("status", "")).upper()
            
            def _norm_sev(p: Dict[str, Any]) -> str:
                return str((p or {}).get("severity", "LOW")).upper()
            
            failed = sum(1 for p in (policies or []) if isinstance(p, dict) and _norm_status(p) == "VIOLATED")
            passed = sum(1 for p in (policies or []) if isinstance(p, dict) and _norm_status(p) == "SATISFIED")
            blocking = sum(
                1
                for p in (policies or [])
                if isinstance(p, dict)
                and _norm_status(p) == "VIOLATED"
                and _norm_sev(p) in {"HIGH", "CRITICAL"}
                and p.get("enforcement_scope") == "TRANSACTION"
            )
            
            total_rules = len([p for p in (policies or []) if isinstance(p, dict)])
            blocking_failures = int(blocking)
            
            # Record telemetry for policies
            _TELEMETRY.record_policy_count(total_rules)
            
            # Record rule coverage for telemetry
            for policy in policies:
                if isinstance(policy, dict):
                    regime = policy.get("regime", "UNKNOWN")
                    article = policy.get("article", "UNKNOWN")
                    status = policy.get("status", "UNKNOWN")
                    _TELEMETRY.record_rule_coverage(regime, article, status)
            
            rule_summary = dict(rule_summary or {})
            rule_summary.update(
                {
                    "total_rules": total_rules,
                    "passed": passed,
                    "failed": failed,
                    "blocking_failures": blocking_failures,
                    "industry_id": industry_id,
                    "profile_id": profile_id,
                    "enabled_regimes": list(enabled_regimes),
                }
            )
            
            l3_valid = (blocking_failures == 0)
            l3 = {
                "layer": "L3",
                "title": "Deterministic Rule Engine (DRE)",
                "validated": True,
                "issues": [] if l3_valid else [f"Blocking failures detected: {blocking_failures}"],
                "severity": "LOW" if l3_valid else "HIGH",
                "summary": rule_summary,
                "causal_trace": [
                    {
                        "article": p.get("article"),
                        "rule_ids": p.get("rule_ids", []),
                        "status": p.get("status"),
                        "severity": p.get("severity"),
                        "why_triggered": p.get("why_triggered") or p.get("notes") or "",
                    }
                    for p in (policies or [])
                    if isinstance(p, dict)
                ],
                "constitutional": {
                    "clause": "GNCE Sec. 3.4 — Rule-level explainability must be available for regulators.",
                    "explainability": {
                        "headline": (
                            f"RULE TRACE OK — {total_rules} rules evaluated, 0 blocking failures."
                            if l3_valid
                            else f"RULE TRACE WARNING — blocking_failures={blocking_failures} (review required)."
                        ),
                        "impact": "Anchors policy lineage and supports audit-grade replay.",
                    },
                },
                "checks": [
                    {
                        "check_id": "L3.RULE_EVAL_EXECUTED",
                        "description": "Policy rules evaluated deterministically.",
                        "pass": total_rules > 0,
                        "observed": f"total_rules={total_rules}",
                    },
                    {
                        "check_id": "L3.NO_BLOCKING_FAILURES",
                        "description": "No blocking failures in evaluation.",
                        "pass": blocking_failures == 0,
                        "observed": f"blocking_failures={blocking_failures}",
                    },
                ],
                "evidence": {
                    "total_rules": total_rules,
                    "passed": passed,
                    "failed": failed,
                    "blocking_failures": blocking_failures,
                    "policies_emitted": len(policies or []),
                },
                "decision_gate": {
                    "allow_downstream": l3_valid,
                    "block_reason": None if l3_valid else "L3 failed: blocking rule failures present.",
                },
            }
            
            sev_rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
            max_sev = "LOW"
            for p in (policies or []):
                if not isinstance(p, dict):
                    continue
                s = _norm_sev(p)
                if sev_rank.get(s, 1) > sev_rank.get(max_sev, 1):
                    max_sev = s
            
            # -------------------------------------------------------
            # Enrich policies with UI-friendly violation details
            # -------------------------------------------------------
            for p in (policies or []):
                if not isinstance(p, dict):
                    continue
                
                p.setdefault("title", p.get("category") or p.get("article") or "Policy obligation")
                
                reason = p.get("notes") or p.get("impact_on_verdict") or ""
                if not isinstance(reason, str):
                    reason = str(reason)
                reason = reason.strip()
                
                status = str(p.get("status", "")).upper()
                if status == "VIOLATED":
                    p.setdefault("violation_detail", reason or "Violation detected (no details provided).")
                else:
                    p.setdefault("violation_detail", "")
                
                p.setdefault("trigger_type", p.get("trigger_type") or "unknown")
            
            l4_valid = bool(policies) and all(
                isinstance(p, dict)
                and p.get("domain") is not None
                and p.get("regime") is not None
                and p.get("article") is not None
                and p.get("status") is not None
                and p.get("severity") is not None
                for p in (policies or [])
            )
            
            l4 = {
                "layer": "L4",
                "title": "Policy Lineage & Constitutional Authority",
                "validated": l4_valid,
                "issues": [] if l4_valid else ["L4 lineage validation failed (missing fields / empty policies)."],
                "severity": "LOW" if l4_valid else "HIGH",
                "policies_triggered": policies,
                "policy_lineage": [
                    {
                        "article": p.get("article"),
                        "domain": p.get("domain"),
                        "regime": p.get("regime"),
                        "severity": p.get("severity"),
                        "status": p.get("status"),
                        "title": p.get("title"),
                        "trigger_type": p.get("trigger_type"),
                        "violation_detail": p.get("violation_detail"),
                        "explainability": {
                            "rule_chain": p.get("rule_ids", []),
                            "justification": p.get("impact_on_verdict") or "",
                            "notes": p.get("notes") or "",
                        },
                        "evidence": p.get("evidence"),
                        "remediation": p.get("remediation"),
                    }
                    for p in (policies or [])
                    if isinstance(p, dict)
                ],
                "constitutional": {
                    "clause": "GNCE Sec. 4.0 — Policy lineage must deterministically link rules to obligations.",
                    "justification": "L4 binds legal obligations (articles) to adjudication inputs.",
                    "explainability": {
                        "headline": (
                            f"POLICY LINEAGE READY — {len(policies or [])} obligations emitted."
                            if l4_valid
                            else "POLICY LINEAGE BROKEN — missing fields or empty lineage (must block)."
                        ),
                        "impact": "L4 is the legal anchor used by L1, and integrity-bound by L5.",
                    },
                },
                "checks": [
                    {
                        "check_id": "L4.POLICIES_EMITTED",
                        "description": "At least one policy obligation emitted.",
                        "pass": len(policies or []) > 0,
                        "observed": f"total_policies={len(policies or [])}",
                    },
                    {
                        "check_id": "L4.MIN_FIELDS_PRESENT",
                        "description": "Policies include domain/regime/article/status/severity.",
                        "pass": l4_valid,
                        "observed": "ok" if l4_valid else "missing_fields",
                    },
                ],
                "evidence": {"total_policies": len(policies or []), "max_policy_severity": max_sev},
                "decision_gate": {
                    "allow_downstream": l4_valid,
                    "block_reason": None if l4_valid else "L4 failed: policy lineage incomplete or malformed.",
                },
            }
            
        except Exception as e:
            logger.error(f"Error during L3/L4 evaluation: {e}")
            _TELEMETRY.record_error("L3L4_ERROR", str(e), {"traceback": traceback.format_exc()})
            
            # Create error L3/L4 to allow continuation
            l3 = {
                "layer": "L3",
                "title": "Deterministic Rule Engine (DRE)",
                "validated": False,
                "issues": [f"L3 evaluation error: {str(e)}"],
                "severity": "HIGH",
                "summary": {"error": str(e), "evaluation_id": evaluation_id},
                "causal_trace": [],
                "constitutional": {"clause": "GNCE Sec. 3.4 — Rule-level explainability must be available for regulators."},
                "checks": [],
                "evidence": {"error": str(e), "traceback": traceback.format_exc() if debug_mode else "HIDDEN"},
                "decision_gate": {"allow_downstream": False, "block_reason": f"L3 error: {str(e)}"},
            }
            
            l4 = {
                "layer": "L4",
                "title": "Policy Lineage & Constitutional Authority",
                "validated": False,
                "issues": [f"L4 evaluation error: {str(e)}"],
                "severity": "HIGH",
                "policies_triggered": [],
                "policy_lineage": [],
                "constitutional": {"clause": "GNCE Sec. 4.0 — Policy lineage must deterministically link rules to obligations."},
                "checks": [],
                "evidence": {"error": str(e)},
                "decision_gate": {"allow_downstream": False, "block_reason": f"L4 error: {str(e)}"},
            }
            
            policies = []
            blocking_failures = 0
        
        l3l4_duration = (time.perf_counter() - l3l4_start) * 1000
        _TELEMETRY.record_layer_duration("L3_L4", l3l4_duration)
        
        _event("L3_L4_COMPLETED", f"policies={len(policies or [])} blocking_failures={blocking_failures}")
        
        # =========================================================
        # L1 — Verdict (SINGLE, across scoped regimes)
        # =========================================================
        l1_start = time.perf_counter()
        
        try:
            # Handle ADVISORY mode - don't block on violations
            if evaluation_mode == "ADVISORY":
                # In advisory mode, we still evaluate but don't trigger veto
                # The constitution will still see violations but we'll override veto later
                pass
            
            l1_raw = GNCE_CONSTITUTION.adjudicate(policies=policies, engine_version=KernelConfig.VERSION) or {}
            l1_raw["timestamp_utc"] = received_at_utc  # canonical
            
            # Ensure required fields exist
            l1_raw.setdefault("decision_outcome", "ERROR")
            l1_raw.setdefault("severity", "HIGH")
            l1_raw.setdefault("human_oversight_required", False)
            l1_raw.setdefault("safe_state_triggered", False)
            l1_raw.setdefault("rationale", "Constitutional adjudication completed")
            
            l1 = {
                "layer": "L1",
                "title": "The Verdict & Constitutional Outcome",
                **l1_raw,
                "constitutional": {
                    "clause": "GNCE Sec. 1.0 — Verdict must be derived deterministically from binding obligations.",
                    "justification": "L1 adjudicates L4 policy lineage into a sovereign decision.",
                    "explainability": {
                        "headline": (
                            "DENY — constitutional obligations were violated."
                            if str(l1_raw.get("decision_outcome", "")).upper() == "DENY"
                            else "ALLOW — no blocking constitutional violations detected."
                        ),
                        "impact": "Downstream layers bind to this verdict for integrity, drift and veto enforcement.",
                    },
                },
                "evidence": {
                    "engine_version": KernelConfig.VERSION,
                    "policy_counts": {
                        "total": len(policies or []),
                        "violated": sum(1 for p in (policies or []) if str(p.get("status", "")).upper() == "VIOLATED"),
                        "satisfied": sum(1 for p in (policies or []) if str(p.get("status", "")).upper() == "SATISFIED"),
                        "not_applicable": sum(1 for p in (policies or []) if str(p.get("status", "")).upper() == "NOT_APPLICABLE"),
                    },
                    "evaluation_mode": evaluation_mode,
                },
                "decision_gate": {
                    "decision_outcome": str(l1_raw.get("decision_outcome", "N/A")).upper(),
                    "severity": str(l1_raw.get("severity", "LOW")).upper(),
                    "human_oversight_required": bool(l1_raw.get("human_oversight_required")),
                    "safe_state_triggered": bool(l1_raw.get("safe_state_triggered")),
                },
            }
            
        except Exception as e:
            logger.error(f"Error during L1 adjudication: {e}")
            _TELEMETRY.record_error("L1_ERROR", str(e))
            
            l1 = {
                "layer": "L1",
                "title": "The Verdict & Constitutional Outcome",
                "validated": False,
                "issues": [f"L1 adjudication error: {str(e)}"],
                "severity": "HIGH",
                "decision_outcome": "ERROR",
                "rationale": f"Constitutional adjudication failed: {str(e)}",
                "constitutional": {
                    "clause": "GNCE Sec. 1.0 — Verdict must be derived deterministically from binding obligations.",
                    "justification": "L1 adjudicates L4 policy lineage into a sovereign decision.",
                    "explainability": {
                        "headline": "ERROR — constitutional adjudication failed.",
                        "impact": "Cannot proceed without valid verdict.",
                    },
                },
                "evidence": {
                    "engine_version": KernelConfig.VERSION,
                    "error": str(e),
                    "traceback": traceback.format_exc() if debug_mode else "HIDDEN",
                },
                "decision_gate": {
                    "decision_outcome": "ERROR",
                    "severity": "HIGH",
                    "human_oversight_required": True,
                    "safe_state_triggered": True,
                },
            }
        
        l1_duration = (time.perf_counter() - l1_start) * 1000
        _TELEMETRY.record_layer_duration("L1", l1_duration)
        
        decision = str(l1.get("decision_outcome", "N/A")).upper()
        _event("L1_VERDICT_COMPUTED", f"decision={decision} severity={l1.get('severity')}")
        
        # =========================================================
        # L5 — CET (SINGLE)
        # =========================================================
        l5_start = time.perf_counter()
        
        try:
            content_to_sign = {"L1": l1, "L3": l3, "L4": l4}
            content_hash_sha256 = _sha256_of(content_to_sign)
            nonce = hashlib.sha256(uuid.uuid4().hex.encode("utf-8")).hexdigest()
            signature_input = f"{content_hash_sha256}:{nonce}".encode("utf-8")
            pseudo_signature_sha256 = "sha256:" + hashlib.sha256(signature_input).hexdigest()
            
            l5_valid = bool(content_hash_sha256 and nonce and pseudo_signature_sha256)
            l5 = {
                "layer": "L5",
                "title": "Integrity & Cryptographic Execution Token (CET)",
                "validated": l5_valid,
                "issues": [] if l5_valid else ["Missing CET integrity fields."],
                "severity": "LOW" if l5_valid else "HIGH",
                "content_hash_sha256": content_hash_sha256,
                "nonce": nonce,
                "pseudo_signature_sha256": pseudo_signature_sha256,
                "signing_strategy": "GNCE_v0.4_pseudo_signature",
                "constitutional": {
                    "clause": "GNCE Sec. 5.1 — Constitutional decisions must be integrity-bound via CET.",
                    "explainability": {
                        "headline": "CET SIGNED — constitutional substrate is integrity-bound (non-repudiable)."
                        if l5_valid else "CET NOT SIGNED — integrity binding failed (must block)."
                    },
                },
                "checks": [
                    {"check_id": "L5.CONTENT_HASH_PRESENT", "description": "Content hash present.", "pass": bool(content_hash_sha256), "observed": str(content_hash_sha256)[:28] + "..."},
                    {"check_id": "L5.NONCE_PRESENT", "description": "Nonce present.", "pass": bool(nonce), "observed": str(nonce)[:28] + "..."},
                    {"check_id": "L5.SIGNATURE_PRESENT", "description": "Signature present.", "pass": bool(pseudo_signature_sha256), "observed": str(pseudo_signature_sha256)[:28] + "..."},
                ],
                "evidence": {
                    "signing_strategy": "GNCE_v0.4_pseudo_signature",
                    "content_hash_sha256": content_hash_sha256,
                },
                "decision_gate": {
                    "allow_downstream": l5_valid,
                    "block_reason": None if l5_valid else f"L5 CET not signed (verdict={decision}); integrity binding failed.",
                    "gate_reason": (
                        f"ALLOW: CET signed and integrity-bound for verdict={decision}."
                        if l5_valid
                        else f"DENY: CET not signed (verdict={decision}); integrity binding failed."
                    ),
                },
            }
            
        except Exception as e:
            logger.error(f"Error during L5 CET creation: {e}")
            _TELEMETRY.record_error("L5_ERROR", str(e))
            
            l5 = {
                "layer": "L5",
                "title": "Integrity & Cryptographic Execution Token (CET)",
                "validated": False,
                "issues": [f"CET creation error: {str(e)}"],
                "severity": "HIGH",
                "content_hash_sha256": "ERROR",
                "nonce": "ERROR",
                "pseudo_signature_sha256": "ERROR",
                "signing_strategy": "GNCE_v0.4_pseudo_signature",
                "constitutional": {
                    "clause": "GNCE Sec. 5.1 — Constitutional decisions must be integrity-bound via CET.",
                    "explainability": {
                        "headline": "CET NOT SIGNED — integrity binding failed (must block)."
                    },
                },
                "checks": [],
                "evidence": {"error": str(e)},
                "decision_gate": {
                    "allow_downstream": False,
                    "block_reason": f"L5 CET creation failed: {str(e)}",
                    "gate_reason": f"DENY: CET not signed due to error",
                },
            }
        
        l5_duration = (time.perf_counter() - l5_start) * 1000
        _TELEMETRY.record_layer_duration("L5", l5_duration)
        
        _event("L5_CET_SIGNATURE_ATTACHED", f"content_hash={l5.get('content_hash_sha256', 'ERROR')[:18]}...")
        
        # =========================================================
        # L6 — Drift (SINGLE)
        # =========================================================
        l6_start = time.perf_counter()
        
        try:
            drift = evaluate_drift(payload, policies, l1)
            drift = drift if isinstance(drift, dict) else {}
            drift_outcome = str(drift.get("drift_outcome", "NO_DRIFT")).upper()
            drift_score = drift.get("drift_score", 0)
            drift_alert = (drift_outcome == "DRIFT_ALERT")
            
            l6 = {
                **drift,
                "layer": "L6",
                "title": "Behavioral Drift & Constitutional Monitoring",
                "validated": True,
                "issues": [] if not drift_alert else ["Drift alert raised by monitoring engine."],
                "severity": "LOW" if not drift_alert else "HIGH",
                "drift_outcome": drift_outcome,
                "drift_score": drift_score,
                "constitutional": {
                    "clause": "GNCE Sec. 6.1 — Behavioral drift monitoring must detect unsafe patterns.",
                    "explainability": {
                        "headline": "NO DRIFT — monitoring reports stable behavior."
                        if not drift_alert else "DRIFT ALERT — anomalous behavior detected; escalation required."
                    },
                },
                "checks": [
                    {"check_id": "L6.DRIFT_ENGINE_EMITTED", "description": "Drift outcome emitted.", "pass": True, "observed": f"{drift_outcome}/{drift_score}"},
                    {"check_id": "L6.DRIFT_ALERT_CHECK", "description": "No drift alert (or escalation required).", "pass": not drift_alert, "observed": drift_outcome},
                ],
                "evidence": {"drift_outcome": drift_outcome, "drift_score": drift_score, "notes": drift.get("notes")},
                "decision_gate": {
                    "allow_downstream": True,
                    "block_reason": None if not drift_alert else "L6 DRIFT_ALERT: safety escalation required.",
                },
            }
            
        except Exception as e:
            logger.warning(f"Error during L6 drift evaluation: {e}")
            _TELEMETRY.record_warning("L6_ERROR", str(e))
            
            l6 = {
                "layer": "L6",
                "title": "Behavioral Drift & Constitutional Monitoring",
                "validated": True,
                "issues": [f"Drift evaluation error: {str(e)}"],
                "severity": "LOW",
                "drift_outcome": "ERROR",
                "drift_score": 0,
                "constitutional": {
                    "clause": "GNCE Sec. 6.1 — Behavioral drift monitoring must detect unsafe patterns.",
                    "explainability": {
                        "headline": "DRIFT EVALUATION ERROR — monitoring failed but proceeding."
                    },
                },
                "checks": [],
                "evidence": {"error": str(e)},
                "decision_gate": {
                    "allow_downstream": True,
                    "block_reason": None,
                },
            }
        
        l6_duration = (time.perf_counter() - l6_start) * 1000
        _TELEMETRY.record_layer_duration("L6", l6_duration)
        
        _event("L6_DRIFT_EVALUATED", f"outcome={l6.get('drift_outcome')} score={l6.get('drift_score')}")
        
        # =========================================================
        # L7 — Veto (SINGLE, derived from merged scoped policies)
        # =========================================================
        l7_start = time.perf_counter()
        
        try:
            # Handle different evaluation modes for veto
            mode_config = KernelConfig.EVALUATION_MODES.get(evaluation_mode, KernelConfig.EVALUATION_MODES["STRICT"])
            
            if evaluation_mode == "ADVISORY":
                # In advisory mode, never trigger veto (but still report violations)
                veto_triggered = False
                execution_authorized = True  # Always authorize in advisory mode
            else:
                # Normal veto logic for STRICT, DRY_RUN, LEARNING modes
                veto_triggered = bool(blocking_failures > 0)
                execution_authorized = (decision == "ALLOW") and (not veto_triggered)
            
            veto_category = "CONSTITUTIONAL_BLOCK" if (veto_triggered and evaluation_mode == "STRICT") else "NONE"
            
            # In advisory mode, execution is always authorized
            if evaluation_mode == "ADVISORY":
                execution_authorized = True
            
            veto_basis: List[Dict[str, Any]] = []
            for p in (policies or []):
                if (
                    isinstance(p, dict)
                    and _norm_status(p) == "VIOLATED"
                    and _norm_sev(p) in {"HIGH", "CRITICAL"}
                    and p.get("enforcement_scope") == "TRANSACTION"
                ):
                    veto_basis.append(
                        {
                            "article": p.get("article"),
                            "status": "VIOLATED",
                            "severity": p.get("severity"),
                            "constitutional_clause": "GNCE Sec. 1.1 — No HIGH/CRITICAL violation may yield ALLOW.",
                            "explanation": (
                                p.get("violation_detail")
                                or p.get("impact_on_verdict")
                                or "Blocking policy violation detected."
                            ),
                        }
                    )
            
            # If we claim veto_triggered, we must record the basis
            if veto_triggered and not veto_basis:
                logger.warning("veto_triggered=True but no veto_basis recorded, creating default")
                veto_basis.append({
                    "article": "UNKNOWN",
                    "status": "VIOLATED",
                    "severity": "HIGH",
                    "constitutional_clause": "GNCE Sec. 1.1 — No HIGH/CRITICAL violation may yield ALLOW.",
                    "explanation": "Blocking violation detected but details unavailable.",
                })
            
            corrective_signal = None
            if veto_triggered and evaluation_mode == "STRICT":
                corrective_signal = {
                    "signal_type": "VETO_CORRECTIVE_SIGNAL",
                    "action_required": "REPLAN_AND_RESUBMIT",
                    "blocked_at": "PRE_EXECUTION",
                    "violations": [
                        {
                            "article": vb.get("article"),
                            "severity": vb.get("severity"),
                            "explanation": vb.get("explanation"),
                            "constitutional_clause": vb.get("constitutional_clause"),
                        }
                        for vb in veto_basis
                    ],
                    "instruction": "Request cannot proceed. Revise inputs/plan to satisfy the violated constraints and resubmit.",
                }
                _event("VETO_CORRECTIVE_SIGNAL_EMITTED", f"count={len(veto_basis)}")
            
            escalation_required = "HUMAN_REVIEWER" if (veto_triggered and evaluation_mode == "STRICT") else "NONE"
            
            # ✅ IMPORTANT: attribution must exist for ALL DENY outcomes (ledger contract)
            veto_layer_attr = None
            if veto_triggered and evaluation_mode == "STRICT":
                veto_layer_attr = "L7"
            elif decision == "DENY":
                # Non-veto DENY still needs attribution for ledger compliance
                # Prefer earliest deterministic gate if available
                try:
                    if isinstance(l0, dict) and (not bool(l0.get("validated", True))):
                        veto_layer_attr = "L0"
                    elif isinstance(l3, dict) and (not bool(l3.get("validated", True))):
                        veto_layer_attr = "L3"
                    else:
                        veto_layer_attr = "L1"
                except Exception:
                    veto_layer_attr = "L1"
            
            l7 = {
                "layer": "L7",
                "title": "Veto Path & Sovereign Execution Feedback",
                "validated": True,
                "execution_authorized": execution_authorized,
                "veto_triggered": veto_triggered,
                "veto_path_triggered": veto_triggered,
                "veto_category": veto_category,
                "escalation_required": escalation_required,
                "evaluation_mode": evaluation_mode,  # NEW: Include evaluation mode in L7
                
                # ✅ ledger compliance requirement
                "veto_layer": veto_layer_attr,
                "origin_layer": veto_layer_attr,
                "trigger_layer": veto_layer_attr,
                
                # attribution
                "clause": (veto_basis[0].get("constitutional_clause") if veto_triggered and veto_basis else None),
                "veto_basis": veto_basis,
                "constitutional_citation": (
                    "A system cannot execute an ALLOW verdict when HIGH/CRITICAL obligations are violated."
                ),
                
                "corrective_signal": corrective_signal,
                
                "severity": "LOW" if execution_authorized else "HIGH",
                "issues": [] if execution_authorized else [
                    f"Execution blocked (veto_category={veto_category})."
                ],
                "decision_gate": {
                    "allow_downstream": execution_authorized,
                    "block_reason": (
                        None if execution_authorized
                        else f"L7 veto: {veto_category} (escalation={escalation_required})."
                    ),
                },
            }
            
            l7["veto_artifact_hash_sha256"] = _sha256_of(l7)
            
        except Exception as e:
            logger.error(f"Error during L7 veto evaluation: {e}")
            _TELEMETRY.record_error("L7_ERROR", str(e))
            
            l7 = {
                "layer": "L7",
                "title": "Veto Path & Sovereign Execution Feedback",
                "validated": False,
                "execution_authorized": False,
                "veto_triggered": False,
                "veto_path_triggered": False,
                "veto_category": "ERROR",
                "escalation_required": "HUMAN_REVIEWER",
                "evaluation_mode": evaluation_mode,
                "veto_layer": "L7",
                "origin_layer": "L7",
                "trigger_layer": "L7",
                "clause": "GNCE Sec. 1.1 — No HIGH/CRITICAL violation may yield ALLOW.",
                "veto_basis": [{
                    "article": "ERROR",
                    "status": "ERROR",
                    "severity": "CRITICAL",
                    "constitutional_clause": "GNCE Sec. 7.1 — Veto evaluation failed.",
                    "explanation": f"Veto evaluation error: {str(e)}",
                }],
                "constitutional_citation": "Veto evaluation encountered an error.",
                "corrective_signal": None,
                "severity": "HIGH",
                "issues": [f"L7 veto evaluation error: {str(e)}"],
                "decision_gate": {
                    "allow_downstream": False,
                    "block_reason": f"L7 veto evaluation error: {str(e)}",
                },
                "veto_artifact_hash_sha256": "ERROR",
            }
        
        l7_duration = (time.perf_counter() - l7_start) * 1000
        _TELEMETRY.record_layer_duration("L7", l7_duration)
        
        _event("L7_VETO_EVALUATED", f"authorized={l7.get('execution_authorized')} veto_category={l7.get('veto_category')} evaluation_mode={evaluation_mode}")
        
        # =========================================================
        # Stewardship + governance context (now includes industry/profile)
        # =========================================================
        stewardship_start = time.perf_counter()
        
        try:
            stewardship_context: Dict[str, Any] = {
                "organizational_steward": {
                    "steward_type": "ORGANIZATIONAL_STEWARD",
                    "display_name": "Deployment-Level Policy Team (L4 Stewardship)",
                    "governance_domain": "GNCE Policy Lineage & Constitutional Authority (L4)",
                },
                "human_steward": {"steward_type": "HUMAN_REVIEW_POOL", "display_name": "Unassigned (Review Pool)"},
                "governance_tier": {"tier": "TIER_2_OPERATIONAL", "description": "Operational governance tier for day-to-day GNCE decisions."},
                "sovereign_engine": {"engine_name": "GNCE Sovereign Constitutional Engine", "version": KernelConfig.VERSION},
            }
            
            chain_of_custody: Dict[str, Any] = {
                "request_received_utc": received_at_utc,
                "kernel_evaluated_by": "GNCE Sovereign Constitutional Engine",
                "kernel_version": KernelConfig.VERSION,
                "execution_authorized": l7.get("execution_authorized"),
                "veto_category": l7.get("veto_category"),
                "timeline_events": kernel_timeline,
                "evaluation_id": evaluation_id,
                "decision_bundle_id": decision_bundle_id,
            }
            
            # ✅ Required by ADRA v0.5 schema: governance_context.verdict_snapshot
            verdict_snapshot: Dict[str, Any] = {
                "decision_outcome": l1.get("decision_outcome"),
                "severity": l1.get("severity"),
                "timestamp_utc": received_at_utc,
                "engine_version": KernelConfig.VERSION,
                "human_oversight_required": bool(l1.get("human_oversight_required")),
                "safe_state_triggered": bool(l1.get("safe_state_triggered")),
                "drift_outcome": l6.get("drift_outcome"),
                "drift_score": l6.get("drift_score"),
                "evaluation_mode": evaluation_mode,
            }
            
            governance_context: Dict[str, Any] = {
                "industry_id": industry_id,
                "profile_id": profile_id,
                "industry_display_name": profile_spec.get("industry_display_name") or profile_spec.get("industry_name"),
                "profile_display_name": profile_spec.get("display_name"),
                "scope_enabled_regimes": list(enabled_regimes),
                "decision_bundle_id": decision_bundle_id,
                "chain_of_custody": chain_of_custody,
                # ✅ ADD THIS
                "verdict_snapshot": verdict_snapshot,
            }
            
        except Exception as e:
            logger.error(f"Error during stewardship context creation: {e}")
            _TELEMETRY.record_error("STEWARDSHIP_ERROR", str(e))
            
            governance_context = {
                "industry_id": industry_id,
                "profile_id": profile_id,
                "scope_enabled_regimes": list(enabled_regimes),
                "decision_bundle_id": decision_bundle_id,
                "chain_of_custody": {
                    "request_received_utc": received_at_utc,
                    "error": f"Stewardship context creation failed: {str(e)}",
                },
                "verdict_snapshot": {
                    "decision_outcome": decision,
                    "severity": "HIGH",
                    "timestamp_utc": received_at_utc,
                    "engine_version": KernelConfig.VERSION,
                    "human_oversight_required": True,
                    "error": str(e),
                },
            }
        
        stewardship_duration = (time.perf_counter() - stewardship_start) * 1000
        _TELEMETRY.record_layer_duration("STEWARDSHIP", stewardship_duration)
        
        # =========================================================
        # SINGLE ADRA EMISSION (AUTHORITATIVE)
        # =========================================================
        adra_build_start = time.perf_counter()
        
        try:
            adra_id = "adra-" + uuid.uuid4().hex[:18]
            
            # 🔒 ADRA v0.5 schema requirement — MUST exist BEFORE skeleton (it may validate internally)
            if not isinstance(governance_context, dict):
                governance_context = {}
            
            # Ensure verdict_snapshot is present (authoritative)
            if "verdict_snapshot" not in governance_context or not isinstance(governance_context.get("verdict_snapshot"), dict):
                governance_context["verdict_snapshot"] = {
                    "decision_outcome": l1.get("decision_outcome"),
                    "severity": l1.get("severity"),
                    "timestamp_utc": received_at_utc,
                    "engine_version": KernelConfig.VERSION,
                    "human_oversight_required": bool(l1.get("human_oversight_required")),
                    "safe_state_triggered": bool(l1.get("safe_state_triggered")),
                    "drift_outcome": l6.get("drift_outcome"),
                    "drift_score": l6.get("drift_score"),
                }
            
            adra = build_adra_v05_skeleton(
                adra_id=adra_id,
                gnce_version=KernelConfig.VERSION,
                drift_outcome=l6.get("drift_outcome"),
                drift_score=l6.get("drift_score"),
                l0=l0,
                l1=l1,
                l2=l2,
                l3=l3,
                l4=l4,
                l5=l5,
                l6=l6,
                l7=l7,
                stewardship_context=stewardship_context,
                governance_context=governance_context,
            )
            
            # 🔒 REQUIRED BY ADRA v0.5 — enforce governance_context as dict (setdefault won't override None)
            if not isinstance(adra.get("governance_context"), dict):
                adra["governance_context"] = {}
            
            adra["governance_context"]["verdict_snapshot"] = dict(governance_context.get("verdict_snapshot", {}))
            
            # Add evaluation context and mode
            adra["evaluation_context_id"] = evaluation_context_id
            adra["evaluation_mode"] = evaluation_mode
            adra["evaluation_id"] = evaluation_id
            
            # Add rule coverage analysis
            rule_coverage = analyze_rule_coverage(policies)
            adra["rule_coverage_analysis"] = rule_coverage
            
            # --- Correlation + scope metadata ---
            adra["decision_bundle_id"] = decision_bundle_id
            adra["timestamp_utc"] = received_at_utc
            adra["kernel_execution_timeline"] = list(kernel_timeline)
            
            # --- Domains triggered (multi-regime, single ADRA) ---
            adra["domains_triggered"] = sorted({
                p.get("domain_id")
                for p in (policies or [])
                if isinstance(p, dict) and p.get("domain_id")
            })
            
            # Check quality gates
            quality_gates_passed, quality_gate_failures = _check_quality_gates(adra)
            adra["quality_gates"] = {
                "passed": quality_gates_passed,
                "failures": quality_gate_failures,
                "checked_at": _utc_now_iso(),
            }
            
            if not quality_gates_passed and evaluation_mode == "STRICT":
                _event("QUALITY_GATES_FAILED", f"failures={len(quality_gate_failures)}", "WARNING")
                # In strict mode, quality gate failures are warnings but don't block
                # Could be escalated to monitoring
            
            # --- Validate ADRA ---
            if KernelConfig.DEBUG["validate_outputs"]:
                is_valid, errors = validate_adra_v05(adra)
                if not is_valid:
                    error_msg = "GNCE CONSTITUTIONAL BREACH: ADRA invalid: " + "; ".join(errors)
                    logger.error(error_msg)
                    _TELEMETRY.record_error("ADRA_VALIDATION_ERROR", error_msg, {"errors": errors})
                    
                    # Try to fix common validation issues
                    for error in errors:
                        if "Missing required field" in error:
                            field = error.split("'")[1] if "'" in error else "unknown"
                            logger.warning(f"Adding missing field: {field}")
                            adra[field] = "AUTO_GENERATED"
                    
                    # Re-validate
                    is_valid, errors = validate_adra_v05(adra)
                    if not is_valid:
                        raise ValidationError(
                            message="ADRA validation failed even after fixes",
                            validation_errors=errors,
                            layer="ADRA_BUILD",
                        )
            
            # --- Canonical hash ---
            canon = dict(adra)
            canon.pop("adra_hash", None)
            canonical_bytes = json.dumps(canon, sort_keys=True, separators=(",", ":")).encode("utf-8")
            adra["adra_hash"] = "sha256:" + hashlib.sha256(canonical_bytes).hexdigest()
            
            # Add debugging information if requested
            if debug_mode:
                adra["_debug"] = {
                    "original_payload_keys": list(original_payload.keys()) if isinstance(original_payload, dict) else [],
                    "evaluation_start_time": start_time,
                    "kernel_version": KernelConfig.VERSION,
                    "python_version": sys.version,
                    "telemetry_available": True,
                }
                
                # Add error summaries if any
                error_summary = _TELEMETRY.get_summary().get("error_summary", {})
                if error_summary:
                    adra["_debug"]["error_summary"] = error_summary
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error during ADRA build: {e}")
            _TELEMETRY.record_error("ADRA_BUILD_ERROR", str(e), {"traceback": traceback.format_exc()})
            
            # Create emergency ADRA
            adra = _create_error_adra(
                evaluation_id,
                f"ADRA build failed: {str(e)}",
                [f"ADRA build error: {str(e)}"],
                received_at_utc,
                original_payload if debug_mode else payload
            )
            adra["emergency_mode"] = True
        
        adra_build_duration = (time.perf_counter() - adra_build_start) * 1000
        _TELEMETRY.record_layer_duration("ADRA_BUILD", adra_build_duration)
        
        # --- Ledger writes (PER-REGIME ADRAxREGIME) ---
        try:
            # Only write to ledger in modes that allow it
            mode_config = KernelConfig.EVALUATION_MODES.get(evaluation_mode, KernelConfig.EVALUATION_MODES["STRICT"])
            skip_ledger_writes = not mode_config.get("allow_ledger_writes", True)
            
            # Build one ADRA envelope per regime (unique adra_id / adra_hash)
            regime_adrAs: List[Dict[str, Any]] = []
            l4_obj = adra.get("L4_policy_lineage_and_constitution") or {}
            policies_all = l4_obj.get("policies_triggered") or []
            l3_obj = adra.get("L3_rule_level_trace") or {}
            causal_all = l3_obj.get("causal_trace") or []
            
            for reg in (enabled_regimes or []):
                try:
                    reg_adra = copy.deepcopy(dict(adra))
                    # Unique identifiers per regime ADRA
                    reg_adra_id = f"adra-{uuid.uuid4().hex[:16]}"
                    reg_adra["adra_id"] = reg_adra_id
                    
                    # Filter L4 policies for this regime
                    reg_policies = [p for p in (policies_all or []) if isinstance(p, dict) and p.get("regime") == reg]
                    reg_adra.setdefault("L4_policy_lineage_and_constitution", {})
                    reg_adra["L4_policy_lineage_and_constitution"]["policies_triggered"] = reg_policies
                    
                    # Keep policy_lineage consistent if present
                    if isinstance(reg_adra["L4_policy_lineage_and_constitution"].get("policy_lineage"), list):
                        reg_adra["L4_policy_lineage_and_constitution"]["policy_lineage"] = [
                            p for p in reg_adra["L4_policy_lineage_and_constitution"]["policy_lineage"]
                            if isinstance(p, dict) and p.get("regime") == reg
                        ]
                    
                    # Filter L3 trace by article prefix heuristic
                    pref = _regime_prefix(reg)
                    reg_adra.setdefault("L3_rule_level_trace", {})
                    reg_adra["L3_rule_level_trace"]["enabled_regimes"] = [reg]
                    reg_adra["L3_rule_level_trace"]["causal_trace"] = [
                        c for c in (causal_all or [])
                        if isinstance(c, dict) and str(c.get("article", "")).startswith(pref)
                    ]
                    
                    # Regime-local decision
                    d = _derive_regime_decision(reg_policies)
                    reg_adra.setdefault("L1_the_verdict_and_constitutional_outcome", {})
                    reg_adra["L1_the_verdict_and_constitutional_outcome"]["decision_outcome"] = d["decision"]
                    reg_adra["L1_the_verdict_and_constitutional_outcome"]["severity"] = d["severity"]
                    reg_adra["L1_the_verdict_and_constitutional_outcome"]["summary"] = dict(
                        reg_adra["L1_the_verdict_and_constitutional_outcome"].get("summary") or {}
                    )
                    reg_adra["L1_the_verdict_and_constitutional_outcome"]["summary"]["blocking_violations"] = d["blocking"]
                    reg_adra["L1_the_verdict_and_constitutional_outcome"]["rationale"] = (
                        "Regime-local verdict computed from regime-scoped policy lineage."
                    )
                    
                    # Regime-local veto attribution
                    reg_adra.setdefault("L7_veto_and_execution_feedback", {})
                    veto_triggered_reg = bool(d["blocking"] > 0)
                    reg_adra["L7_veto_and_execution_feedback"]["veto_triggered"] = veto_triggered_reg
                    reg_adra["L7_veto_and_execution_feedback"]["veto_category"] = "CONSTITUTIONAL_BLOCK" if veto_triggered_reg else "NONE"
                    reg_adra["L7_veto_and_execution_feedback"]["execution_authorized"] = (d["decision"] == "ALLOW") and (not veto_triggered_reg)
                    reg_adra["L7_veto_and_execution_feedback"]["escalation_required"] = "HUMAN_REVIEWER" if veto_triggered_reg else "NONE"
                    reg_adra["L7_veto_and_execution_feedback"]["veto_layer"] = "L7" if veto_triggered_reg else ("L1" if d["decision"] == "DENY" else None)
                    reg_adra["L7_veto_and_execution_feedback"]["origin_layer"] = reg_adra["L7_veto_and_execution_feedback"]["veto_layer"]
                    reg_adra["L7_veto_and_execution_feedback"]["trigger_layer"] = reg_adra["L7_veto_and_execution_feedback"]["veto_layer"]
                    
                    # Basis for veto if triggered
                    if veto_triggered_reg:
                        reg_adra["L7_veto_and_execution_feedback"]["veto_basis"] = [
                            {
                                "article": p.get("article"),
                                "status": "VIOLATED",
                                "severity": p.get("severity"),
                                "constitutional_clause": "GNCE Sec. 1.1 — No HIGH/CRITICAL violation may yield ALLOW.",
                                "explanation": (p.get("violation_detail") or p.get("impact_on_verdict") or "Blocking policy violation detected."),
                            }
                            for p in d["hi_crit"]
                        ]
                    else:
                        reg_adra["L7_veto_and_execution_feedback"]["veto_basis"] = []
                    
                    # Recompute hash AFTER modifications
                    reg_adra["adra_hash"] = _sha256_json(reg_adra)
                    
                    # Skip ledger writes in DRY_RUN or ADVISORY modes if configured
                    if not skip_ledger_writes:
                        # Enforce ledger compliance per regime ADRA envelope and write ledgers
                        compliant = _assert_ledger_compliance(dict(reg_adra))
                        append_to_session_ledger(build_adra_ledger_row(dict(compliant)))
                        for rr in build_article_ledger_rows(dict(compliant)):
                            append_to_article_ledger(rr)
                    else:
                        _event("LEDGER_SKIPPED", f"mode={evaluation_mode} regime={reg}", "INFO")
                    
                    regime_adrAs.append(reg_adra)
                    
                except Exception as e:
                    logger.warning(f"Failed to create regime ADRA for {reg}: {e}")
                    _TELEMETRY.record_warning("REGIME_ADRA_ERROR", f"{reg}: {str(e)}")
                    # Continue with other regimes
            
            # Attach to the returned ADRA for debugging/inspection (does not affect ledger uniqueness)
            adra["regime_adrAs"] = regime_adrAs
            
        except Exception as e:
            logger.error(f"Error during ledger writes: {e}")
            _TELEMETRY.record_error("LEDGER_ERROR", str(e))
            adra["ledger_error"] = str(e)
        
        # Add performance metrics to ADRA
        total_duration_ms = (time.perf_counter() - start_time) * 1000
        evaluation_success, _ = _TELEMETRY.end_evaluation()
        
        adra["performance_metrics"] = {
            "total_duration_ms": total_duration_ms,
            "evaluation_success": evaluation_success,
            "layer_durations_ms": {
                "L0": l0_duration,
                "ROUTING": routing_duration,
                "L2": l2_duration,
                "L3_L4": l3l4_duration,
                "L1": l1_duration,
                "L5": l5_duration,
                "L6": l6_duration,
                "L7": l7_duration,
                "STEWARDSHIP": stewardship_duration,
                "ADRA_BUILD": adra_build_duration,
            },
            "evaluation_mode": evaluation_mode,
            "telemetry_available": True,
            "evaluation_id": evaluation_id,
        }
        
        # Check for performance issues
        if total_duration_ms > KernelConfig.QUALITY_GATES["maximum_evaluation_time_ms"]:
            _TELEMETRY.record_warning(
                "PERFORMANCE_WARNING",
                f"Total evaluation time {total_duration_ms:.2f}ms exceeds threshold"
            )
            adra["performance_metrics"]["performance_warning"] = True
        
        # Add evidence retention hint
        verdict = adra.get("L1_the_verdict_and_constitutional_outcome", {}).get("decision_outcome", "ALLOW")
        if verdict == "DENY":
            retention_days = KernelConfig.EVIDENCE_RETENTION_POLICY["DENY"].days
        elif blocking_failures > 0:
            retention_days = KernelConfig.EVIDENCE_RETENTION_POLICY["ALLOW_WITH_VIOLATIONS"].days
        elif evaluation_mode == "DRY_RUN":
            retention_days = KernelConfig.EVIDENCE_RETENTION_POLICY["DRY_RUN"].days
        else:
            retention_days = KernelConfig.EVIDENCE_RETENTION_POLICY["ALLOW"].days
        
        adra["evidence_retention_hint"] = {
            "recommended_retention_days": retention_days,
            "basis": verdict,
            "expiry_date": (datetime.now(timezone.utc) + timedelta(days=retention_days)).isoformat(),
            "evaluation_mode": evaluation_mode,
        }
        
        # Add telemetry summary if in debug mode
        if debug_mode and KernelConfig.DEBUG["log_performance_metrics"]:
            telemetry_summary = _TELEMETRY.get_summary()
            adra["telemetry_summary"] = {
                "total_evaluations": telemetry_summary.get("total_evaluations", 0),
                "avg_evaluation_time_ms": telemetry_summary.get("avg_evaluation_time_ms", 0),
                "error_summary": telemetry_summary.get("error_summary", {}),
            }
        
        _event("EVALUATION_COMPLETED", f"duration={total_duration_ms:.2f}ms decision={decision} evaluation_id={evaluation_id}")
        
        logger.info(f"Completed kernel evaluation {evaluation_id} in {total_duration_ms:.2f}ms")
        
        return adra
        
    except (KernelError, ValidationError, RoutingError, ScopeError):
        # Re-raise kernel-specific errors
        raise
    except Exception as e:
        # Catch-all for unexpected errors
        logger.critical(f"CRITICAL: Kernel evaluation failed: {e}", exc_info=True)
        _TELEMETRY.record_error("CRITICAL_ERROR", str(e), {
            "traceback": traceback.format_exc(),
            "evaluation_id": evaluation_id if 'evaluation_id' in locals() else "UNKNOWN",
        })
        
        # Create emergency ADRA
        emergency_adra = _create_error_adra(
            evaluation_id if 'evaluation_id' in locals() else str(uuid.uuid4()),
            f"Kernel critical error: {str(e)}",
            [f"Critical kernel failure: {str(e)}", traceback.format_exc()],
            _utc_now_iso(),
            original_payload if debug_mode else payload,
            kernel_timeline if 'kernel_timeline' in locals() else []
        )
        emergency_adra["critical_error"] = True
        return emergency_adra

# =========================================================
# ENHANCED MAIN KERNEL FUNCTION WITH EXECUTION LOOP SUPPORT
# =========================================================

def run_gn_kernel_for_execution_loop(
    raw_request: Dict[str, Any],
    industry_id: Optional[str] = None,
    profile_id: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    evaluation_mode: str = "STRICT",
    enabled_regimes: Optional[List[str]] = None,
    context_id: Optional[str] = None,
    debug_mode: bool = False,
) -> Dict[str, Any]:
    """
    GNCE Kernel entry point specifically for execution loop.
    
    This is the main function the execution loop should call.
    It handles payload preparation and error handling.
    
    Args:
        raw_request: Raw request from execution loop
        industry_id: Optional industry override
        profile_id: Optional profile override  
        jurisdiction: Optional jurisdiction
        evaluation_mode: Evaluation mode
        enabled_regimes: Optional enabled regimes
        context_id: Optional context ID
        debug_mode: Enable debug output
    
    Returns:
        Complete ADRA with evaluation results
    """
    try:
        # Validate the raw request
        is_valid, issues = validate_execution_request(raw_request)
        if not is_valid:
            logger.error(f"Invalid execution request: {issues}")
            # Use the comprehensive _create_error_adra function
            return _create_error_adra(
                evaluation_id=str(uuid.uuid4()),
                error_message="Invalid execution request",
                issues=issues,
                timestamp=_utc_now_iso(),
                payload=raw_request,
                kernel_timeline=[{
                    "ts_utc": _utc_now_iso(),
                    "stage": "VALIDATION_FAILED",
                    "detail": f"Validation failed: {issues}"
                }]
            )
        
        # Prepare the payload for kernel
        payload = prepare_execution_payload(
            raw_request=raw_request,
            industry_id=industry_id,
            profile_id=profile_id,
            jurisdiction=jurisdiction,
            evaluation_mode=evaluation_mode,
            enabled_regimes=enabled_regimes,
            context_id=context_id,
        )
        
        # Run the kernel (note: current run_gn_kernel doesn't have debug_mode param)
        adra = run_gn_kernel(payload)
        
        # Add execution loop context to the ADRA
        adra["execution_loop_context"] = {
            "original_request_id": raw_request.get("request_id"),
            "prepared_at": _utc_now_iso(),
            "industry_provided": industry_id is not None,
            "profile_provided": profile_id is not None,
            "jurisdiction_provided": jurisdiction is not None,
            "evaluation_mode": evaluation_mode,
        }
        
        return adra
        
    except Exception as e:
        logger.critical(f"Execution loop kernel call failed: {e}", exc_info=True)
        return _create_error_adra(
            evaluation_id=str(uuid.uuid4()),
            error_message=f"Execution loop kernel error: {str(e)}",
            issues=[f"Execution loop processing failed: {str(e)}"],
            timestamp=_utc_now_iso(),
            payload=raw_request,
            kernel_timeline=[{
                "ts_utc": _utc_now_iso(),
                "stage": "EXECUTION_LOOP_ERROR",
                "detail": f"Exception: {str(e)}"
            }]
        )

# =========================================================
# DIAGNOSTIC FUNCTIONS
# =========================================================

def diagnose_kernel_health() -> Dict[str, Any]:
    """Run diagnostic checks on kernel health."""
    health = {
        "timestamp": _utc_now_iso(),
        "kernel_version": KernelConfig.VERSION,
        "status": "HEALTHY",
        "issues": [],
        "checks": [],
    }
    
    # Check imports
    try:
        from .models.adra_v05 import validate_adra_v05
        health["checks"].append({"component": "ADRA model", "status": "OK"})
    except ImportError as e:
        health["checks"].append({"component": "ADRA model", "status": "ERROR", "error": str(e)})
        health["issues"].append(f"ADRA model import failed: {e}")
        health["status"] = "DEGRADED"
    
    # Check registry
    try:
        init_registry()
        health["checks"].append({"component": "Regime registry", "status": "OK", "count": len(REGIME_REGISTRY)})
    except Exception as e:
        health["checks"].append({"component": "Regime registry", "status": "ERROR", "error": str(e)})
        health["issues"].append(f"Registry init failed: {e}")
        health["status"] = "DEGRADED"
    
    # Check industry registry
    try:
        health["checks"].append({"component": "Industry registry", "status": "OK", "count": len(INDUSTRY_REGISTRY)})
    except Exception as e:
        health["checks"].append({"component": "Industry registry", "status": "ERROR", "error": str(e)})
        health["issues"].append(f"Industry registry error: {e}")
        health["status"] = "DEGRADED"
    
    # Check constitution
    try:
        constitution_status = "OK" if GNCE_CONSTITUTION else "ERROR"
        health["checks"].append({"component": "Constitution", "status": constitution_status})
    except Exception as e:
        health["checks"].append({"component": "Constitution", "status": "ERROR", "error": str(e)})
        health["issues"].append(f"Constitution error: {e}")
        health["status"] = "DEGRADED"
    
    # Check telemetry
    try:
        telemetry_summary = _TELEMETRY.get_summary()
        health["telemetry"] = {
            "total_evaluations": telemetry_summary.get("total_evaluations", 0),
            "error_summary": telemetry_summary.get("error_summary", {}),
        }
        health["checks"].append({"component": "Telemetry", "status": "OK"})
    except Exception as e:
        health["checks"].append({"component": "Telemetry", "status": "ERROR", "error": str(e)})
        health["issues"].append(f"Telemetry error: {e}")
        health["status"] = "DEGRADED"
    
    return health

def get_kernel_config_summary() -> Dict[str, Any]:
    """Get summary of kernel configuration."""
    return {
        "version": KernelConfig.VERSION,
        "evaluation_modes": list(KernelConfig.EVALUATION_MODES.keys()),
        "performance_optimizations": KernelConfig.PERFORMANCE_OPTIMIZATIONS,
        "safety_limits": KernelConfig.SAFETY_LIMITS,
        "quality_gates": {
            "maximum_evaluation_time_ms": KernelConfig.QUALITY_GATES["maximum_evaluation_time_ms"],
            "minimum_evidence_count": KernelConfig.QUALITY_GATES["minimum_evidence_count"],
        },
        "debug_enabled": KernelConfig.DEBUG,
    }

# =========================================================
# PUBLIC KERNEL API (Enhanced)
# =========================================================

def run_gn_kernel_safe(payload: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """
    Safe wrapper around run_gn_kernel that never raises exceptions.
    
    Returns:
        ADRA with error information if kernel fails
    """
    try:
        return run_gn_kernel(payload, **kwargs)
    except Exception as e:
        logger.critical(f"Kernel failed in safe mode: {e}", exc_info=True)
        return _create_error_adra(
            evaluation_id=str(uuid.uuid4()),
            error_message=f"Kernel safe mode error: {str(e)}",
            issues=[f"Kernel exception: {str(e)}"],
            timestamp=_utc_now_iso(),
            payload=payload,
            kernel_timeline=[{
                "ts_utc": _utc_now_iso(),
                "stage": "SAFE_MODE_ERROR",
                "detail": f"Exception: {str(e)}"
            }]
        )
    
def get_kernel_telemetry() -> Dict[str, Any]:
    """Get telemetry summary for monitoring."""
    return _TELEMETRY.get_summary()

def reset_kernel_telemetry() -> None:
    """Reset telemetry (for testing or rotation)."""
    global _TELEMETRY
    _TELEMETRY = EvaluationTelemetry()
    logger.info("Kernel telemetry reset")

class EvaluationContext:
    """Evaluation context for chained evaluations."""
    def __init__(self, context_id: Optional[str] = None):
        self.context_id = context_id or str(uuid.uuid4())
        self.evaluations = []
        self.start_time = time.perf_counter()
    
    def add_evaluation(self, adra: Dict[str, Any]) -> None:
        """Add an evaluation result to the context."""
        self.evaluations.append({
            "timestamp": _utc_now_iso(),
            "adra_id": adra.get("adra_id"),
            "decision": adra.get("L1_the_verdict_and_constitutional_outcome", {}).get("decision_outcome"),
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get context summary."""
        return {
            "context_id": self.context_id,
            "total_evaluations": len(self.evaluations),
            "duration_ms": (time.perf_counter() - self.start_time) * 1000,
            "evaluations": self.evaluations[-10:],  # Last 10 evaluations
        }

def create_evaluation_context(context_id: Optional[str] = None) -> EvaluationContext:
    """Create a new evaluation context for chained evaluations."""
    return EvaluationContext(context_id)

def set_kernel_log_level(level: Union[str, int]) -> None:
    """Set kernel logging level."""
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)

# After the existing run_gn_kernel function (around line 1200-1300 in your current file)
# Add this right after the last line of run_gn_kernel function:

# =========================================================
# EXECUTION LOOP COMPATIBILITY WRAPPERS
# =========================================================

def evaluate_ecommerce_listing(
    product_details: Dict[str, Any],
    user_id: str,
    jurisdiction: str = "EU",
    marketplace_type: str = "STANDARD",
    evaluation_mode: str = "STRICT",
    debug_mode: bool = False,
) -> Dict[str, Any]:
    """
    Evaluate an ecommerce product listing request.
    
    Args:
        product_details: Product details (title, description, price, category, etc.)
        user_id: User ID
        jurisdiction: Jurisdiction
        marketplace_type: Type of marketplace (STANDARD, MARKETPLACE, PEER_TO_PEER)
        evaluation_mode: Evaluation mode
        debug_mode: Enable debug
    
    Returns:
        ADRA with evaluation results
    """
    request = {
        "action": "LIST_PRODUCT",
        "user_id": user_id,
        "content": f"List product: {product_details.get('title', 'Unknown product')}",
        "listing": product_details,
        "timestamp_utc": _utc_now_iso(),
        "request_id": f"list-{uuid.uuid4().hex[:12]}",
        "risk_indicators": {
            "harmful_content_flag": False,
            "violation_category": None,
            "previous_violations": 0
        }
    }
    
    # Determine profile based on marketplace type
    if marketplace_type == "MARKETPLACE":
        if jurisdiction == "EU":
            profile = "ECOMMERCE_MARKETPLACE_EU"
        elif jurisdiction == "US":
            profile = "ECOMMERCE_MARKETPLACE_US"
        else:
            profile = "ECOMMERCE_MARKETPLACE_GLOBAL"
    else:
        profile = "MERCHANT_STANDARD"
    
    return run_gn_kernel_for_execution_loop(
        raw_request=request,
        industry_id="ECOMMERCE",
        profile_id=profile,
        jurisdiction=jurisdiction,
        evaluation_mode=evaluation_mode,
        debug_mode=debug_mode,
    )


def evaluate_content_post(
    content: str,
    user_id: str,
    platform_context: Optional[Dict[str, Any]] = None,
    jurisdiction: str = "EU",
    platform_type: str = "SOCIAL_MEDIA",
    evaluation_mode: str = "STRICT",
    debug_mode: bool = False,
) -> Dict[str, Any]:
    """
    Evaluate a content post request (simplified execution loop interface).
    
    Args:
        content: Content to post
        user_id: User ID
        platform_context: Platform-specific context
        jurisdiction: Jurisdiction
        platform_type: Platform type (SOCIAL_MEDIA, FORUM, MESSAGING)
        evaluation_mode: Evaluation mode
        debug_mode: Enable debug
    
    Returns:
        ADRA with evaluation results
    """
    request = {
        "action": "POST_CONTENT",
        "user_id": user_id,
        "content": content,
        "timestamp_utc": _utc_now_iso(),
        "request_id": f"post-{uuid.uuid4().hex[:12]}",
    }
    
    if platform_context:
        request.update(platform_context)
    
    # Determine profile based on platform type
    if platform_type == "SOCIAL_MEDIA":
        if jurisdiction == "EU":
            profile = "VLOP_SOCIAL_META"  # Default for EU social media
        else:
            profile = "PLATFORM_STANDARD"
    else:
        profile = "PLATFORM_STANDARD"
    
    return run_gn_kernel_for_execution_loop(
        raw_request=request,
        industry_id="SOCIAL_MEDIA",
        profile_id=profile,
        jurisdiction=jurisdiction,
        evaluation_mode=evaluation_mode,
        debug_mode=debug_mode,
    )


def evaluate_data_export(
    dataset: str,
    data_type: str = "PERSONAL",
    lawful_basis: Optional[str] = None,
    user_id: str = "SYSTEM",
    jurisdiction: str = "EU",
    evaluation_mode: str = "STRICT",
    debug_mode: bool = False,
) -> Dict[str, Any]:
    """
    Evaluate a data export request (simplified execution loop interface).
    
    Args:
        dataset: Dataset description
        data_type: Type of data (PERSONAL, ANONYMIZED, AGGREGATE)
        lawful_basis: Lawful basis for processing
        user_id: User ID
        jurisdiction: Jurisdiction
        evaluation_mode: Evaluation mode
        debug_mode: Enable debug
    
    Returns:
        ADRA with evaluation results
    """
    request = {
        "action": "EXPORT_DATA",
        "user_id": user_id,
        "content": f"Export {data_type} dataset: {dataset}",
        "export": {
            "dataset": dataset,
            "data_type": data_type,
            "lawful_basis": lawful_basis or "CONSENT",
        },
        "timestamp_utc": _utc_now_iso(),
        "request_id": f"export-{uuid.uuid4().hex[:12]}",
    }
    
    return run_gn_kernel_for_execution_loop(
        raw_request=request,
        industry_id="DATA_PROCESSING",
        profile_id="PROCESSOR_STANDARD",
        jurisdiction=jurisdiction,
        evaluation_mode=evaluation_mode,
        debug_mode=debug_mode,
    )


def evaluate_transaction(
    transaction_details: Dict[str, Any],
    user_id: str,
    jurisdiction: str = "US",
    evaluation_mode: str = "STRICT",
    debug_mode: bool = False,
) -> Dict[str, Any]:
    """
    Evaluate a transaction request (simplified execution loop interface).
    
    Args:
        transaction_details: Transaction details
        user_id: User ID
        jurisdiction: Jurisdiction
        evaluation_mode: Evaluation mode
        debug_mode: Enable debug
    
    Returns:
        ADRA with evaluation results
    """
    request = {
        "action": "PROCESS_TRANSACTION",
        "user_id": user_id,
        "content": json.dumps(transaction_details),
        "transaction": transaction_details,
        "timestamp_utc": _utc_now_iso(),
        "request_id": f"txn-{uuid.uuid4().hex[:12]}",
    }
    
    return run_gn_kernel_for_execution_loop(
        raw_request=request,
        industry_id="ECOMMERCE",
        profile_id="MERCHANT_STANDARD",
        jurisdiction=jurisdiction,
        evaluation_mode=evaluation_mode,
        debug_mode=debug_mode,
    )


# =========================================================
# BATCH EVALUATION FOR EXECUTION LOOP
# =========================================================

def evaluate_batch_requests(
    requests: List[Dict[str, Any]],
    default_industry: Optional[str] = None,
    default_profile: Optional[str] = None,
    default_jurisdiction: Optional[str] = None,
    evaluation_mode: str = "STRICT",
    debug_mode: bool = False,
) -> List[Dict[str, Any]]:
    """
    Evaluate multiple requests in batch (for execution loop).
    
    Args:
        requests: List of request dictionaries
        default_industry: Default industry if not specified in request
        default_profile: Default profile if not specified
        default_jurisdiction: Default jurisdiction if not specified
        evaluation_mode: Evaluation mode
        debug_mode: Enable debug
    
    Returns:
        List of ADRAs with evaluation results
    """
    results = []
    
    for i, raw_request in enumerate(requests):
        try:
            # Use request-specific values or defaults
            industry = raw_request.get("industry_id") or default_industry
            profile = raw_request.get("profile_id") or default_profile
            jurisdiction = raw_request.get("meta", {}).get("jurisdiction") or default_jurisdiction
            
            adra = run_gn_kernel_for_execution_loop(
                raw_request=raw_request,
                industry_id=industry,
                profile_id=profile,
                jurisdiction=jurisdiction,
                evaluation_mode=evaluation_mode,
                debug_mode=debug_mode,
            )
            results.append(adra)
            
        except Exception as e:
            logger.error(f"Batch evaluation failed for request {i}: {e}")
            error_adra = _create_error_adra(
                evaluation_id=str(uuid.uuid4()),
                error_message=f"Batch evaluation error: {str(e)}",
                issues=[f"Failed to process request {i}"],
                timestamp=_utc_now_iso(),
                payload=raw_request,
                kernel_timeline=[{
                    "ts_utc": _utc_now_iso(),
                    "stage": "BATCH_ERROR",
                    "detail": f"Request {i} failed: {str(e)}"
                }]
            )
            results.append(error_adra)
    
    return results


# =========================================================
# EXPORT PUBLIC API
# =========================================================

# These functions will be available when importing the kernel module
__all__ = [
    'run_gn_kernel',
    'run_gn_kernel_for_execution_loop',
    'evaluate_ecommerce_listing',
    'evaluate_content_post',
    'evaluate_data_export',
    'evaluate_transaction',
    'evaluate_batch_requests',
    'prepare_execution_payload',
    'validate_execution_request',
]

# Keep backward compatibility
__all__ = [
    'run_gn_kernel',
    'run_gn_kernel_safe',
    'GNCE_VERSION',
    'KernelConfig',
    'diagnose_kernel_health',
    'get_kernel_telemetry',
    'reset_kernel_telemetry',
    'create_evaluation_context',
    'set_kernel_log_level',
]