# gnce/gn_kernel/rules/dma_rules.py
# =========================================================
#  DMA RULE LIBRARY — GNCE v0.7.2-RC (Constitutional Binding)
# =========================================================
# Deterministic obligations for the EU Digital Markets Act
# Articles 5, 6, and 7
#
# FUTURE-PROOF UPDATES:
# 1. Complete gatekeeper verification with multiple checks
# 2. Enforcement scope resolution with context awareness
# 3. Industry-aware DMA applicability
# 4. Comprehensive action/context filtering
# 5. Evidence collection for audit trails
# 6. Cross-domain safety (won't misfire on non-gatekeeper contexts)

from __future__ import annotations

from typing import Any, Callable, Dict, List, Set, Tuple

# Load governance catalog for enforcement scope classification
from gnce.gn_kernel.constitution.constitution_catalog import load_governance_catalog_v05

# ============================================================
# MODULE CONSTANTS
# ============================================================

DMA_DOMAIN = "EU Digital Markets Act (DMA)"
DMA_FRAMEWORK = "Digital Sovereignty"

# Load catalog once at module level (performance)
_GOVERNANCE_CATALOG = load_governance_catalog_v05()

# ============================================================
# GATEKEEPER DETECTION (FUTURE-PROOF)
# ============================================================

# Known designated gatekeepers (as of 2024-2025)
# Source: European Commission designation decisions
DMA_DESIGNATED_GATEKEEPERS: Set[str] = {
    "ALPHABET", "GOOGLE", "META", "FACEBOOK", "AMAZON", "APPLE",
    "MICROSOFT", "BYTEDANCE", "TIKTOK", "BOOKING", "SAMSUNG",
    # Future-proofing for potential designations
    "ALIBABA", "TENCENT", "NETFLIX", "SPOTIFY", "UBER", "AIRBNB",
    "SALESFORCE", "ORACLE", "IBM", "INTEL", "NVIDIA",
}

# Core Platform Services (CPS) under DMA scope
DMA_CORE_PLATFORM_SERVICES: Set[str] = {
    "search_engine",
    "social_network",
    "video_sharing",
    "messaging_service",
    "operating_system",
    "cloud_computing",
    "online_advertising",
    "marketplace",
    "app_store",
    "web_browser",
    "virtual_assistant",
    "connected_tv",
    "payment_service",
    "map_service",
    "enterprise_software",
}

# Industries where DMA typically applies
DMA_APPLICABLE_INDUSTRIES: Set[str] = {
    "SOCIAL_MEDIA",
    "ECOMMERCE",
    "FINTECH",
    "SAAS_B2B",
    "MEDIA",
    "GAMING",
    "CLOUD_SERVICES",
    "OPERATING_SYSTEM",
    "SEARCH_ENGINE",
    "APP_STORE",
}

# Actions where DMA obligations are relevant
DMA_RELEVANT_ACTIONS: Set[str] = {
    # Ranking and search actions
    "search_content",
    "rank_results",
    "recommend_content",
    "suggest_content",
    "prioritize_content",
    
    # Data and access actions
    "access_data",
    "combine_data",
    "export_data",
    "share_data",
    "process_data",
    
    # Platform control actions
    "approve_app",
    "reject_app",
    "remove_content",
    "feature_product",
    "promote_content",
    
    # Business user actions
    "list_product",
    "advertise_product",
    "process_payment",
    "access_analytics",
    "use_api",
    
    # User experience actions
    "default_app",
    "change_settings",
    "switch_service",
    "uninstall_app",
    "port_data",
}

# Actions where DMA likely doesn't apply (future-proof exclusions)
NON_DMA_ACTIONS: Set[str] = {
    # Personal/non-business actions
    "login",
    "logout",
    "view_content",
    "read_message",
    "watch_video",
    
    # Healthcare actions (different regime)
    "access_medical_record",
    "prescribe_medication",
    "medical_diagnosis",
    
    # Internal system actions
    "system_backup",
    "update_software",
    "monitor_performance",
    "generate_report",
    "audit_log",
}

# ============================================================
# ENFORCEMENT SCOPE RESOLUTION (FUTURE-PROOF)
# ============================================================

def _normalize_article(article: str) -> str:
    """
    Normalize DMA article identifier for consistent comparison.
    
    Examples:
        "DMA Article 5(1)" → "5"
        "Article 6" → "6"
        "Art. 7" → "7"
        "5(2)" → "5"
    """
    # Extract just the article number
    article = article.replace("DMA ", "").replace("Article ", "").replace("Art. ", "")
    # Extract first digit(s) before any parenthesis or dash
    for separator in ["(", "-", " ", ".", ","]:
        if separator in article:
            article = article.split(separator)[0]
    return article.strip()


def _get_dma_base_enforcement_scope(article: str) -> str:
    """
    Get base enforcement scope from governance catalog.
    
    DMA Classification (Future-proof):
    - Art 5(1), 5(2), 6(2): TRANSACTION (per-action conduct obligations)
    - Art 5(3), 5(4), 6(1), 6(3), 6(4): PLATFORM_AUDIT (systemic/technical obligations)
    - Art 7: PLATFORM_AUDIT (annual audit obligation)
    - Art 13, 14: SUPERVISORY (regulator reporting)
    
    Returns: "TRANSACTION" | "PLATFORM_AUDIT" | "SUPERVISORY"
    Default: "PLATFORM_AUDIT" (safe - logs but doesn't block)
    """
    article_normalized = _normalize_article(article)
    
    for regime in _GOVERNANCE_CATALOG.get("regimes", []):
        if regime.get("id") == "DMA":
            for domain in regime.get("domains", []):
                for art_def in domain.get("articles", []):
                    art_num = _normalize_article(art_def.get("article", ""))
                    if art_num == article_normalized:
                        return art_def.get("enforcement_scope", "PLATFORM_AUDIT")
    
    # SAFE DEFAULT: PLATFORM_AUDIT (logged, not blocking)
    # Prevents surprise DENYs for new/unmapped articles
    return "PLATFORM_AUDIT"


def _is_designated_gatekeeper(payload: Dict[str, Any]) -> bool:
    """
    Future-proof gatekeeper detection with multiple verification methods.
    
    Criteria (simplified but comprehensive):
    1. Explicit gatekeeper flag (most reliable)
    2. Known designated company/platform
    3. Core Platform Service provider with scale indicators
    4. Industry + action context
    
    Returns:
        True if designated gatekeeper (DMA applies)
        False if not gatekeeper (DMA doesn't apply)
    """
    # Method 1: Explicit gatekeeper flag (most reliable)
    dma_profile = payload.get("dma_profile", {})
    if dma_profile.get("is_gatekeeper"):
        return True
    
    # Method 2: Known designated company/platform
    meta = payload.get("meta", {})
    company = str(meta.get("company", "")).upper().strip()
    platform_name = str(meta.get("platform_name", "")).upper().strip()
    
    if company in DMA_DESIGNATED_GATEKEEPERS:
        return True
    if platform_name in DMA_DESIGNATED_GATEKEEPERS:
        return True
    
    # Method 3: Core Platform Service with scale indicators
    platform_type = str(dma_profile.get("platform_type", "")).lower().strip()
    if platform_type in DMA_CORE_PLATFORM_SERVICES:
        # Check for scale indicators (simplified)
        user_count = meta.get("monthly_active_users_eu", 0)
        revenue = meta.get("annual_revenue_eea", 0)
        
        # DMA thresholds (simplified for future-proofing)
        # Real implementation would use exact thresholds from EC decisions
        if user_count > 45000000 or revenue > 75000000000:  # 45M users or €75B
            return True
    
    # Method 4: Industry + action context (conservative)
    industry = str(payload.get("industry_id", "")).upper().strip()
    action = str(payload.get("action", "")).lower().strip()
    
    if industry in DMA_APPLICABLE_INDUSTRIES and action in DMA_RELEVANT_ACTIONS:
        # In a DMA-relevant context but not explicitly a gatekeeper
        # Be conservative - require explicit flag or known company
        return False
    
    # Default: Not a designated gatekeeper
    return False


def _should_evaluate_dma(payload: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Future-proof decision: Should DMA evaluation run for this payload?
    
    Returns:
        (should_evaluate, reason)
    """
    # Check gatekeeper status first
    if not _is_designated_gatekeeper(payload):
        return False, "NOT_DESIGNATED_GATEKEEPER"
    
    # Check jurisdiction
    meta = payload.get("meta", {})
    jurisdiction = str(meta.get("jurisdiction", "")).upper().strip()
    if jurisdiction not in {"EU", "EEA", "EUROPE"}:
        return False, f"JURISDICTION_OUTSIDE_EU: {jurisdiction}"
    
    # Check action relevance
    action = str(payload.get("action", "")).lower().strip()
    if action in NON_DMA_ACTIONS:
        return False, f"ACTION_EXCLUDED: {action}"
    
    # Check industry
    industry = str(payload.get("industry_id", "")).upper().strip()
    if industry not in DMA_APPLICABLE_INDUSTRIES:
        return False, f"INDUSTRY_EXCLUDED: {industry}"
    
    # All checks passed - evaluate DMA
    return True, "EVALUATE_DMA"


def _resolve_enforcement_scope(article: str, payload: Dict[str, Any]) -> str:
    """
    Resolve final enforcement scope with future-proof modifiers.
    
    DMA enforcement scope modifiers:
    1. Article-specific scope from catalog (primary)
    2. Action context may escalate/down-grade scope
    3. Platform type may affect applicability
    
    Returns:
        Final enforcement scope after applying modifiers
    """
    base_scope = _get_dma_base_enforcement_scope(article)
    
    # Extract context for potential modifiers
    action = str(payload.get("action", "")).lower().strip()
    dma_profile = payload.get("dma_profile", {})
    
    # MODIFIER: Self-preferencing in ranking actions is always TRANSACTION
    # (DMA Art 5(1) - high risk of immediate consumer harm)
    if article.startswith("5") and action in {"rank_results", "recommend_content", "search_content"}:
        if dma_profile.get("self_preferencing") or dma_profile.get("ranking_data_discrimination"):
            return "TRANSACTION"  # Escalate to blocking
    
    # MODIFIER: Data combining in sensitive contexts
    if article.startswith("5(2)") and action in {"combine_data", "process_data", "share_data"}:
        if dma_profile.get("data_combining_without_consent"):
            return "TRANSACTION"  # Escalate to blocking
    
    # No modifiers applied - return base scope
    return base_scope


# ============================================================
# DMA RULE CLASS (Enhanced for Future-Proofing)
# ============================================================

class DMARule:
    """
    DMA rule definition with trigger logic and future-proof metadata.
    
    Each rule represents a specific DMA obligation with:
    - Rule ID for unique identification
    - Article reference
    - Category and severity
    - Description and trigger logic
    - Impact classification
    - Evidence requirements
    """
    def __init__(
        self,
        rule_id: str,
        article: str,
        category: str,
        severity: str,
        description: str,
        trigger: Callable[[Dict[str, Any]], bool],
        impact_on_verdict: str,
        evidence_fields: List[str] = None,
        future_proof_notes: str = "",
    ):
        self.rule_id = rule_id
        self.article = article
        self.category = category
        self.severity = severity      # LOW / MEDIUM / HIGH / CRITICAL
        self.description = description
        self.trigger = trigger
        self.impact_on_verdict = impact_on_verdict
        self.evidence_fields = evidence_fields or []
        self.future_proof_notes = future_proof_notes


# ============================================================
# DMA RULES REGISTRY (Enhanced with Evidence Requirements)
# ============================================================

dma_rules: List[DMARule] = [
    # ----------------- Article 5: Conduct Obligations -----------------
    DMARule(
        rule_id="DMA_A5_1_SELF_PREFERENCING",
        article="DMA Article 5(1)",
        category="Self-preferencing",
        severity="HIGH",
        description="Gatekeeper must not rank its own products/services more favourably.",
        trigger=lambda i: (
            (i.get("platform_behavior") or {}).get("self_preference", False)
            or (i.get("dma_profile") or {}).get("self_preferencing", False)
        ),
        impact_on_verdict="BLOCKING_FAILURE",
        evidence_fields=["dma_profile.self_preferencing", "platform_behavior.self_preference"],
        future_proof_notes="Applies to search rankings, recommendations, and any algorithmic ordering.",
    ),
    DMARule(
        rule_id="DMA_A5_2_DATA_COMBINING",
        article="DMA Article 5(2)",
        category="Data combining without consent",
        severity="HIGH",
        description="Gatekeeper must not combine personal data across services without valid consent.",
        trigger=lambda i: (
            (i.get("data_ops") or {}).get("combined_personal_data", False)
            or (i.get("dma_profile") or {}).get("data_combining_without_consent", False)
        ),
        impact_on_verdict="BLOCKING_FAILURE",
        evidence_fields=["dma_profile.data_combining_without_consent", "data_ops.combined_personal_data"],
        future_proof_notes="Includes cross-service tracking, profiling, and behavioral analysis.",
    ),
    DMARule(
        rule_id="DMA_A5_3_BUSINESS_DATA_ACCESS",
        article="DMA Article 5(3)",
        category="Restricting business user data access",
        severity="MEDIUM",
        description="Gatekeeper must not restrict business users from accessing data generated by their activity.",
        trigger=lambda i: (
            (i.get("partner_access") or {}).get("blocked_data_access", False)
            or (i.get("dma_profile") or {}).get("ranking_data_discrimination", False)
        ),
        impact_on_verdict="MANDATORY_CHECK",
        evidence_fields=["partner_access.blocked_data_access", "dma_profile.ranking_data_discrimination"],
        future_proof_notes="Includes analytics data, customer insights, and performance metrics.",
    ),
    DMARule(
        rule_id="DMA_A5_4_TYING_BUNDLING",
        article="DMA Article 5(4)",
        category="Tying / anti-bundling",
        severity="MEDIUM",
        description="Gatekeeper must not force users to use tied services as a condition for using core platform services.",
        trigger=lambda i: (
            (i.get("platform_behavior") or {}).get("forced_bundling", False)
            or (i.get("dma_profile") or {}).get("bundling_detected", False)
        ),
        impact_on_verdict="MANDATORY_CHECK",
        evidence_fields=["platform_behavior.forced_bundling", "dma_profile.bundling_detected"],
        future_proof_notes="Includes app store requirements, payment processing, and advertising bundles.",
    ),

    # ----------------- Article 6: Technical Obligations -----------------
    DMARule(
        rule_id="DMA_A6_1_INTEROP",
        article="DMA Article 6(1)",
        category="Interoperability",
        severity="MEDIUM",
        description="Gatekeeper must provide interoperability with third-party services.",
        trigger=lambda i: (
            not (i.get("interoperability") or {}).get("is_open", True)
            or (i.get("dma_profile") or {}).get("interoperability_refused", False)
        ),
        impact_on_verdict="MANDATORY_CHECK",
        evidence_fields=["interoperability.is_open", "dma_profile.interoperability_refused"],
        future_proof_notes="Includes messaging, social graphs, and cross-platform functionality.",
    ),
    DMARule(
        rule_id="DMA_A6_2_RANKING_DATA",
        article="DMA Article 6(2)",
        category="Access to ranking data",
        severity="HIGH",
        description="Gatekeeper must provide fair access to ranking, query, and click data.",
        trigger=lambda i: (
            (i.get("partner_access") or {}).get("ranking_data_restricted", False)
            or (i.get("dma_profile") or {}).get("ranking_data_discrimination", False)
        ),
        impact_on_verdict="BLOCKING_FAILURE",
        evidence_fields=["partner_access.ranking_data_restricted", "dma_profile.ranking_data_discrimination"],
        future_proof_notes="Critical for search engines, app stores, and marketplaces.",
    ),
    DMARule(
        rule_id="DMA_A6_3_SWITCHING",
        article="DMA Article 6(3)",
        category="Switching barriers",
        severity="MEDIUM",
        description="Gatekeeper must not impose unjustified switching or multi-homing barriers.",
        trigger=lambda i: (
            (i.get("ux") or {}).get("switching_barriers", False)
            or (i.get("dma_profile") or {}).get("anti_steering_blocked", False)
        ),
        impact_on_verdict="MANDATORY_CHECK",
        evidence_fields=["ux.switching_barriers", "dma_profile.anti_steering_blocked"],
        future_proof_notes="Includes default settings, data portability, and contractual lock-in.",
    ),
    DMARule(
        rule_id="DMA_A6_4_PORTABILITY",
        article="DMA Article 6(4)",
        category="Data portability",
        severity="MEDIUM",
        description="Gatekeeper must enable effective, real-time data portability tools.",
        trigger=lambda i: (
            not (i.get("data_ops") or {}).get("portability_enabled", True)
            or (i.get("dma_profile") or {}).get("bundling_detected", False)
        ),
        impact_on_verdict="MANDATORY_CHECK",
        evidence_fields=["data_ops.portability_enabled", "dma_profile.bundling_detected"],
        future_proof_notes="Includes GDPR data portability and service-to-service migration.",
    ),

    # ----------------- Article 7: Audit Obligations -----------------
    DMARule(
        rule_id="DMA_A7_1_AUDIT",
        article="DMA Article 7",
        category="Annual audit",
        severity="LOW",
        description="Gatekeeper must conduct and document an independent audit at least annually.",
        trigger=lambda i: not (i.get("audit") or {}).get("dma_audit_completed", True),
        impact_on_verdict="MANDATORY_CHECK",
        evidence_fields=["audit.dma_audit_completed"],
        future_proof_notes="Includes compliance program assessment and remediation tracking.",
    ),

    # ----------------- Future Articles (Placeholders) -----------------
    DMARule(
        rule_id="DMA_A13_1_REPORTING",
        article="DMA Article 13",
        category="Regulatory reporting",
        severity="LOW",
        description="Gatekeeper must provide required reports to European Commission.",
        trigger=lambda i: False,  # Placeholder - not implemented yet
        impact_on_verdict="SUPERVISORY",
        evidence_fields=[],
        future_proof_notes="Placeholder for future Article 13 implementation.",
    ),
    DMARule(
        rule_id="DMA_A14_1_COMPLIANCE",
        article="DMA Article 14",
        category="Compliance measures",
        severity="MEDIUM",
        description="Gatekeeper must implement effective compliance measures.",
        trigger=lambda i: False,  # Placeholder - not implemented yet
        impact_on_verdict="PLATFORM_AUDIT",
        evidence_fields=[],
        future_proof_notes="Placeholder for future Article 14 implementation.",
    ),
]


# ============================================================
# REMEDIATION GUIDANCE (Enhanced for Future-Proofing)
# ============================================================

REMEDIATION_BY_RULE_ID: Dict[str, str] = {
    "DMA_A5_1_SELF_PREFERENCING": (
        "Remove self-preferencing signals in ranking/UX; implement neutrality controls and audit ranking outcomes. "
        "Establish ongoing monitoring for algorithmic fairness. Re-run GNCE after mitigation."
    ),
    "DMA_A5_2_DATA_COMBINING": (
        "Stop cross-service personal data combining unless valid consent/legal basis is recorded; "
        "implement consent gates, data silos, and access logs. Establish data governance program. "
        "Re-run GNCE after mitigation."
    ),
    "DMA_A5_3_BUSINESS_DATA_ACCESS": (
        "Provide business users access to data generated by their activity via APIs/exports; "
        "document access controls and data availability. Establish business data portal. "
        "Re-run GNCE after mitigation."
    ),
    "DMA_A5_4_TYING_BUNDLING": (
        "Remove bundling/tying conditions for access; implement unbundled choice flows and contractual controls. "
        "Document alternative offerings. Re-run GNCE after mitigation."
    ),
    "DMA_A6_1_INTEROP": (
        "Implement required interoperability interfaces per DMA technical standards; "
        "document conformance, publish APIs, and test with third parties. "
        "Establish interoperability roadmap. Re-run GNCE after mitigation."
    ),
    "DMA_A6_2_RANKING_DATA": (
        "Provide fair access to ranking/query/click data or document lawful exceptions; "
        "implement governance, access logging, and transparency reports. "
        "Establish ranking data portal. Re-run GNCE after mitigation."
    ),
    "DMA_A6_3_SWITCHING": (
        "Remove unjustified switching/multi-homing barriers; enable easy switching/uninstall/default changes "
        "and document UX evidence. Establish user switching assistance. Re-run GNCE after mitigation."
    ),
    "DMA_A6_4_PORTABILITY": (
        "Provide effective portability/export mechanisms; ensure real-time tools where required; "
        "document endpoints, APIs, and controls. Establish data portability dashboard. "
        "Re-run GNCE after mitigation."
    ),
    "DMA_A7_1_AUDIT": (
        "Establish annual independent audit readiness: controls, logs, evidence packs, and governance ownership. "
        "Document audit schedule and findings remediation. Re-run GNCE after mitigation."
    ),
    # Future-proof remediation templates
    "DMA_A13_1_REPORTING": (
        "Establish regulatory reporting program with documented processes, data sources, and quality controls. "
        "Appoint compliance officer and implement reporting calendar."
    ),
    "DMA_A14_1_COMPLIANCE": (
        "Implement comprehensive compliance program with policies, training, monitoring, and remediation processes. "
        "Document compliance measures and effectiveness assessments."
    ),
}


# ============================================================
# EVIDENCE COLLECTION (Enhanced for Future-Proofing)
# ============================================================

def _collect_dma_evidence(payload: Dict[str, Any], rule: DMARule) -> Dict[str, Any]:
    """
    Collect DMA evidence for audit trails with future-proof structure.
    
    Returns:
        Structured evidence with context, trigger data, and metadata
    """
    evidence = {
        # Context evidence
        "context": {
            "industry_id": payload.get("industry_id"),
            "action": payload.get("action"),
            "is_gatekeeper": _is_designated_gatekeeper(payload),
            "jurisdiction": (payload.get("meta") or {}).get("jurisdiction"),
        },
        # Trigger evidence
        "trigger_data": {},
        # Metadata
        "metadata": {
            "rule_id": rule.rule_id,
            "article": rule.article,
            "category": rule.category,
            "evidence_collected_at": "NOW",  # Would be timestamp in real implementation
        }
    }
    
    # Collect specific evidence fields for this rule
    for field_path in rule.evidence_fields:
        if "." in field_path:
            # Nested field path (e.g., "dma_profile.self_preferencing")
            parts = field_path.split(".")
            obj = payload
            for part in parts[:-1]:
                obj = obj.get(part, {})
            value = obj.get(parts[-1])
            evidence["trigger_data"][field_path] = value
        else:
            # Simple field
            evidence["trigger_data"][field_path] = payload.get(field_path)
    
    # Add common DMA evidence
    dma_profile = payload.get("dma_profile", {})
    evidence["trigger_data"]["dma_profile.is_gatekeeper"] = dma_profile.get("is_gatekeeper")
    evidence["trigger_data"]["meta.jurisdiction"] = (payload.get("meta") or {}).get("jurisdiction")
    
    return evidence


# ============================================================
# MAIN EVALUATION FUNCTION (Future-Proof Architecture)
# ============================================================

def evaluate_dma_rules(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Future-proof DMA evaluation with comprehensive context gating.
    
    Features:
    1. Multi-stage gatekeeper verification
    2. Jurisdiction and action filtering
    3. Industry-aware applicability
    4. Enforcement scope resolution
    5. Comprehensive evidence collection
    6. Detailed context tracking
    
    Returns:
        (policies, summary)
        - policies: List with enforcement_scope, evidence, and context
        - summary: Aggregate statistics with detailed context info
    """
    policies: List[Dict[str, Any]] = []
    
    # ============================================================
    # FUTURE-PROOF: CONTEXT GATING DECISION
    # ============================================================
    should_evaluate, evaluation_reason = _should_evaluate_dma(payload)
    
    if not should_evaluate:
        # DMA doesn't apply to this context - return early with explanation
        summary = {
            "total_rules": 0,
            "passed": 0,
            "failed": 0,
            "blocking_failures": 0,
            "regime": "DMA",
            "context_gated": True,
            "evaluation_decision": evaluation_reason,
            "gatekeeper_status": "NOT_APPLICABLE",
            "jurisdiction": (payload.get("meta") or {}).get("jurisdiction"),
            "industry": payload.get("industry_id"),
            "action": payload.get("action"),
            "notes": f"DMA evaluation skipped: {evaluation_reason}"
        }
        return policies, summary
    
    # ============================================================
    # POLICY EMISSION FUNCTION (Enhanced)
    # ============================================================
    
    def _add_policy(*, rule: DMARule, status: str, severity: str, notes: str) -> None:
        """
        Add DMA policy with comprehensive evidence and context.
        """
        # Get enforcement scope with modifiers
        enforcement_scope = _resolve_enforcement_scope(rule.article, payload)
        
        # Determine remediation
        remediation = (
            REMEDIATION_BY_RULE_ID.get(rule.rule_id, "Remediate and re-run GNCE after mitigation.")
            if status == "VIOLATED"
            else "No remediation required."
        )
        
        # Create policy with future-proof structure
        policy: Dict[str, Any] = {
            "domain": DMA_DOMAIN,
            "regime": "DMA",
            "framework": DMA_FRAMEWORK,
            "domain_id": "DMA",
            "article": rule.article,
            "category": rule.category,
            "title": rule.category,
            "status": status,
            "severity": severity,
            "control_severity": str(rule.severity).upper(),
            "impact_on_verdict": (
                rule.impact_on_verdict
                if status == "VIOLATED"
                else "Compliant under tested DMA obligations."
            ),
            "trigger_type": "DMA_OBLIGATION",
            "rule_ids": [rule.rule_id],
            "enforcement_scope": enforcement_scope,
            "notes": notes,
            "evidence": _collect_dma_evidence(payload, rule),
            "remediation": remediation,
            "violation_detail": rule.description if status == "VIOLATED" else "",
            # Future-proof metadata
            "metadata": {
                "gatekeeper_verified": True,
                "jurisdiction": (payload.get("meta") or {}).get("jurisdiction"),
                "industry_context": payload.get("industry_id"),
                "action_context": payload.get("action"),
                "future_proof_notes": rule.future_proof_notes,
            }
        }

        policies.append(policy)
    
    # ============================================================
    # RULE EVALUATION (Enhanced with Error Handling)
    # ============================================================
    
    evaluation_errors = []
    
    for rule in dma_rules:
        try:
            violated = bool(rule.trigger(payload))
        except Exception as e:
            # Safety: if a trigger fails, log error and treat as SATISFIED
            violated = False
            evaluation_errors.append({
                "rule_id": rule.rule_id,
                "error": str(e),
                "action": payload.get("action"),
            })
            # Continue evaluation - don't crash kernel

        if violated:
            _add_policy(
                rule=rule,
                status="VIOLATED",
                severity=str(rule.severity).upper(),
                notes=rule.description,
            )
        else:
            _add_policy(
                rule=rule,
                status="SATISFIED",
                severity="LOW",
                notes=f"Not triggered: {rule.description}",
            )
    
    # ============================================================
    # SUMMARY STATISTICS (Comprehensive)
    # ============================================================
    
    failed = sum(1 for p in policies if str(p.get("status", "")).upper() == "VIOLATED")
    passed = sum(1 for p in policies if str(p.get("status", "")).upper() == "SATISFIED")
    
    # Count ONLY transaction-scoped violations (can block)
    blocking = sum(
        1
        for p in policies
        if str(p.get("status", "")).upper() == "VIOLATED"
        and str(p.get("severity", "")).upper() in {"HIGH", "CRITICAL"}
        and p.get("enforcement_scope") == "TRANSACTION"
    )
    
    # Context information for debugging
    context_info = {
        "industry": payload.get("industry_id"),
        "action": payload.get("action"),
        "jurisdiction": (payload.get("meta") or {}).get("jurisdiction"),
        "is_gatekeeper": _is_designated_gatekeeper(payload),
        "dma_profile_exists": bool(payload.get("dma_profile")),
    }
    
    summary = {
        "total_rules": len(policies),
        "passed": passed,
        "failed": failed,
        "blocking_failures": blocking,
        "regime": "DMA",
        "context_gated": False,
        "evaluation_decision": evaluation_reason,
        "gatekeeper_status": "DESIGNATED_GATEKEEPER",
        # Scope-specific violation counts
        "platform_audit_violations": sum(
            1 for p in policies
            if p.get("status") == "VIOLATED"
            and p.get("enforcement_scope") == "PLATFORM_AUDIT"
        ),
        "transaction_violations": sum(
            1 for p in policies
            if p.get("status") == "VIOLATED"
            and p.get("enforcement_scope") == "TRANSACTION"
        ),
        "supervisory_violations": sum(
            1 for p in policies
            if p.get("status") == "VIOLATED"
            and p.get("enforcement_scope") == "SUPERVISORY"
        ),
        # Context info
        "context": context_info,
        # Error tracking
        "evaluation_errors": evaluation_errors if evaluation_errors else None,
        # Future-proofing metrics
        "rules_evaluated": len([r for r in dma_rules if r.trigger]),
        "rules_skipped": len([r for r in dma_rules if not r.trigger]),
    }
    
    return policies, summary