# gnce/gn_kernel/rules/dsa_rules.py
"""
DSA Rule Evaluator with Constitutional Binding (v0.7.2-RC-FIXED)

CRITICAL FIXES APPLIED:
1. DSA content safety PROPERLY gated - excludes non-content actions (e-commerce, financial, healthcare)
2. Illegal signal limited to DSA-specific categories (not FINTECH fraud)
3. Article normalization consistent between input and catalog
4. Safe defaults for missing catalog entries
5. NO EARLY RETURNS - let constitutional veto handle blocking decisions
6. Future-proof action classification with industry-aware logic

Key features:
- Loads enforcement_scope from governance catalog
- VLOP escalation: PLATFORM_AUDIT → TRANSACTION for VLOPs
- Illegal signal escalation: CONDITIONAL → TRANSACTION (DSA-specific only)
- Harmful content blocks ONLY in true content/platform contexts
- Cross-domain safe: won't misfire on FINTECH/ECOMMERCE/HEALTHCARE payloads
- Industry-aware context detection
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple, Set

# Load governance catalog for enforcement scope classification
from gnce.gn_kernel.constitution.constitution_catalog import load_governance_catalog_v05

# ============================================================
# MODULE CONSTANTS
# ============================================================

DSA_DOMAIN = "EU Digital Services Act (DSA)"
DSA_FRAMEWORK = "I. Digital Sovereignty & Platform Law"

# Load catalog once at module level (performance)
_GOVERNANCE_CATALOG = load_governance_catalog_v05()

# DSA-specific illegal content categories (don't include FINTECH fraud!)
DSA_ILLEGAL_CONTENT_CATEGORIES: Set[str] = {
    "extremism",
    "csam",
    "child_sexual_abuse_material",
    "terrorism",
    "violent_extremism",
    "hate_speech",
    "illegal_content",
    "child_abuse",
    "human_trafficking",
    "incitement_to_violence",
    "illegal_drugs",
    "weapons_trafficking",
    "harmful_content",  # Added to catch general harmful content
}

# NON-DSA categories (should NOT trigger DSA content safety)
NON_DSA_CATEGORIES: Set[str] = {
    "fraud_high_risk",
    "fraud_suspected", 
    "refund_abuse",
    "aml_suspicious",
    "transaction_risk",
    "prohibited_listing",  # E-commerce specific, NOT DSA
    "counterfeit_goods",
    "intellectual_property",
    "unauthorized_sales",
    "medical_compliance",  # Healthcare specific
    "hipaa_violation",
    "data_breach",
    "security_incident",
}

# Context types where DSA content safety applies
DSA_CONTENT_CONTEXTS: Set[str] = {
    "post_content",
    "upload_media",
    "publish_article",
    "share_content",
    "comment",
    "message",
    "broadcast",
    "stream",
    "platform_action",
    "moderate_content",
    "flag_content",
    "report_content",
    "create_community",
    "create_channel",
    "live_stream",
}

# NON-CONTEXT actions where DSA should NOT apply (future-proof list)
NON_DSA_ACTIONS: Set[str] = {
    # E-commerce actions
    "list_product",
    "create_order", 
    "process_payment",
    "refund",
    "ship_product",
    "cancel_order",
    "update_inventory",
    "create_listing",  # E-commerce listing, not content listing
    "manage_cart",
    "apply_coupon",
    
    # Financial actions
    "execute_financial_transaction",
    "wire_transfer",
    "process_loan",
    "check_credit",
    "fraud_check",
    "aml_screening",
    
    # Healthcare actions
    "access_medical_record",
    "process_healthcare_claim",
    "schedule_appointment",
    "prescribe_medication",
    "medical_diagnosis",
    
    # B2B/Enterprise actions
    "process_invoice",
    "manage_contract",
    "audit_log",
    "generate_report",
    "system_maintenance",
    
    # Generic non-content actions
    "login",
    "logout",
    "update_profile",
    "change_settings",
    "request_data",
    "delete_account",
}

# Industries where DSA content safety should apply
DSA_CONTENT_INDUSTRIES: Set[str] = {
    "SOCIAL_MEDIA",
    "UGC",
    "PLATFORM",
    "MEDIA",
    "NEWS",
    "ENTERTAINMENT",
    "GAMING",
}

# ============================================================
# ENFORCEMENT SCOPE RESOLUTION (CONSTITUTIONAL BINDING)
# ============================================================

def _normalize_article(article: str) -> str:
    """
    Normalize article identifier for consistent comparison.
    
    Examples:
        "DSA Art. 34" → "34"
        "Art. 34" → "34"
        "34" → "34"
    """
    return article.replace("DSA ", "").replace("Art. ", "").replace(".", "").strip()


def _get_dsa_base_enforcement_scope(article: str) -> str:
    """
    Get base enforcement scope from governance catalog.
    
    Returns:
        - "TRANSACTION": May block individual requests
        - "PLATFORM_AUDIT": Platform-level compliance (quarterly reports, etc.)
        - "CONDITIONAL": Context-dependent escalation
        - "SUPERVISORY": Regulator-facing only
    
    Default: "PLATFORM_AUDIT" (safe - logs but doesn't block unknown articles)
    
    IMPORTANT: Default changed from TRANSACTION to PLATFORM_AUDIT to avoid
    surprise blocks when articles are missing from catalog.
    """
    # Normalize article format (both input and catalog)
    article_normalized = _normalize_article(article)
    
    for regime in _GOVERNANCE_CATALOG.get("regimes", []):
        if regime.get("id") == "DSA":
            for domain in regime.get("domains", []):
                for art_def in domain.get("articles", []):
                    # Normalize catalog article too
                    art_num = _normalize_article(art_def.get("article", ""))
                    if art_num == article_normalized:
                        scope = art_def.get("enforcement_scope", "PLATFORM_AUDIT")
                        return scope
    
    # SAFE DEFAULT: Unknown articles are PLATFORM_AUDIT (logged, not blocking)
    # This prevents surprise DENYs when catalog is incomplete
    return "PLATFORM_AUDIT"


def _is_dsa_content_context(payload: Dict[str, Any]) -> bool:
    """
    Check if this payload is in a DSA-relevant content/platform context.
    
    FUTURE-PROOF LOGIC:
    1. Check action type - exclude known non-content actions
    2. Check industry - only apply DSA to content industries
    3. Check for content field presence
    4. Check meta/platform signals
    
    DSA applies to:
    - Content posting/uploading/sharing in SOCIAL_MEDIA, MEDIA, PLATFORM industries
    - Platform actions (moderation, recommendations) for content platforms
    - User-generated content distribution
    
    DSA does NOT apply to:
    - E-commerce listings (LIST_PRODUCT) - even with "create_listing" in content
    - Financial transactions (FINTECH domain)
    - Healthcare records (HIPAA domain)
    - B2B SaaS operations
    
    Returns:
        True if DSA content safety rules should apply
        False if this is non-content context
    """
    # 1. Check explicit action type - EXCLUDE known non-content actions FIRST
    action = str(payload.get("action", "")).lower().strip()
    
    if action in NON_DSA_ACTIONS:
        return False  # Definitely NOT a DSA content context
    
    # 2. Check industry context - DSA only applies to content industries
    industry = str(payload.get("industry_id", "")).upper().strip()
    
    if industry not in DSA_CONTENT_INDUSTRIES:
        # Not a content industry, but might still be content action
        # Check if this looks like a content action anyway
        if action in DSA_CONTENT_CONTEXTS:
            # It's a content action in a non-content industry
            # This could be edge case - e.g., "post_content" in ECOMMERCE
            # We'll be conservative and return False
            return False
    
    # 3. Industry is content-related, now check action
    if action in DSA_CONTENT_CONTEXTS:
        return True
    
    # 4. Check if content field is present AND significant
    content = payload.get("content", "")
    if content and isinstance(content, str) and len(content.strip()) > 10:
        # Has meaningful content text
        # Check if this is NOT a transaction/listing
        if not payload.get("transaction_amount") and not payload.get("listing"):
            return True
    
    # 5. Check meta/platform classification
    meta = payload.get("meta", {})
    platform_class = str(meta.get("platform_classification", "")).upper()
    if platform_class in {"SOCIAL_NETWORK", "CONTENT_PLATFORM", "UGC_PLATFORM"}:
        return True
    
    # 6. Default: not a DSA content context
    return False


def _has_dsa_illegal_signal(payload: Dict[str, Any]) -> bool:
    """
    Check if DSA-specific illegal content signal is present.
    
    FUTURE-PROOF LOGIC:
    1. Check harmful content flag + context
    2. Check violation category - must be DSA-specific
    3. Check for non-DSA categories and exclude them
    
    CRITICAL: Only checks DSA-relevant categories, NOT other domain signals.
    
    Returns:
        True if DSA-specific illegal content detected
        False otherwise (including other domain violations)
    """
    risk_indicators = payload.get("risk_indicators", {})
    
    # 1. Check violation category FIRST (most specific)
    violation_cat = str(risk_indicators.get("violation_category", "")).lower().strip()
    
    # EXCLUDE non-DSA categories immediately
    if violation_cat in NON_DSA_CATEGORIES:
        return False  # Not a DSA concern
    
    # Check if it's a DSA category
    if violation_cat in DSA_ILLEGAL_CONTENT_CATEGORIES:
        return True
    
    # 2. Check harmful content flag (context-dependent)
    if risk_indicators.get("harmful_content_flag"):
        # Verify this is actually a content context
        if _is_dsa_content_context(payload):
            return True
    
    # 3. Check content itself for DSA-specific keywords (future-proofing)
    content = str(payload.get("content", "")).lower()
    dsa_keywords = {
        "terrorism", "extremist", "hate speech", "child abuse", "csam",
        "human trafficking", "violent extremism", "incitement to violence"
    }
    
    if any(keyword in content for keyword in dsa_keywords):
        return True
    
    # No DSA illegal signal found
    return False


def _resolve_enforcement_scope(article: str, payload: Dict[str, Any]) -> str:
    """
    Resolve final enforcement scope with contextual modifiers.
    
    FUTURE-PROOF MODIFIERS:
    1. VLOP escalation: PLATFORM_AUDIT → TRANSACTION for VLOPs
    2. Illegal content escalation: CONDITIONAL → TRANSACTION (DSA-specific only)
    3. Harmful content in content context: always TRANSACTION
    4. Content industry modifier: stricter enforcement for content platforms
    
    CROSS-DOMAIN SAFETY:
    - Only escalates for DSA-relevant signals
    - Won't misfire on other domain violations
    """
    base_scope = _get_dsa_base_enforcement_scope(article)
    
    # Extract context
    meta = payload.get("meta", {})
    is_vlop = bool(meta.get("is_vlop"))
    
    # Check for DSA-specific illegal signal
    has_dsa_illegal = _has_dsa_illegal_signal(payload)
    
    # Check if this is a content industry
    industry = str(payload.get("industry_id", "")).upper().strip()
    is_content_industry = industry in DSA_CONTENT_INDUSTRIES
    
    # MODIFIER 1: VLOP escalation
    # Platform-level obligations become transactional for VLOPs
    if base_scope == "PLATFORM_AUDIT" and is_vlop:
        return "TRANSACTION"
    
    # MODIFIER 2: DSA illegal content escalation
    # Conditional obligations become mandatory when DSA illegal content detected
    if base_scope == "CONDITIONAL" and has_dsa_illegal:
        return "TRANSACTION"
    
    # MODIFIER 3: Content industry strictness
    # In content industries, be more strict with enforcement
    if base_scope == "CONDITIONAL" and is_content_industry:
        return "PLATFORM_AUDIT"  # Escalate conditional in content industries
    
    # No modifiers applied - return base scope
    return base_scope


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _risk_level(payload: Dict[str, Any]) -> str:
    """Normalize overall risk level on the payload."""
    level = str(payload.get("risk_level", "LOW")).upper()
    if level not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
        level = "LOW"
    return level


def _add_policy(
    policies: List[Dict[str, Any]],
    *,
    article: str,
    category: str,
    status: str,
    severity: str,
    impact: str,
    trigger_type: str,
    rule_ids: List[str],
    enforcement_scope: str,
    notes: str = "",
    evidence: Dict[str, Any] = None,
) -> None:
    """
    Add a policy evaluation result with constitutional binding.
    
    FUTURE-PROOF: Include evidence field for detailed tracing.
    """
    policy = {
        "domain": DSA_DOMAIN,
        "regime": "DSA",
        "framework": DSA_FRAMEWORK,
        "domain_id": "DSA",
        "article": article,
        "category": category,
        "status": status,
        "severity": severity,
        "impact_on_verdict": impact,
        "trigger_type": trigger_type,
        "rule_ids": rule_ids,
        "enforcement_scope": enforcement_scope,
        "notes": notes,
    }
    
    if evidence:
        policy["evidence"] = evidence
    
    policies.append(policy)


def _bump_severity(base: str, risk: str) -> str:
    """Escalate severity when global risk is HIGH/CRITICAL."""
    if risk in {"HIGH", "CRITICAL"} and base in {"LOW", "MEDIUM"}:
        return "HIGH"
    return base


# ============================================================
# MAIN EVALUATION FUNCTION
# ============================================================

def evaluate_dsa_rules(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Evaluate all DSA-related rules for this ADRA.
    
    FUTURE-PROOF ARCHITECTURE:
    1. Context detection first (industry + action)
    2. Illegal content check (context-aware)
    3. Platform obligations evaluation
    4. NO EARLY RETURNS - let constitutional system handle veto
    
    CROSS-DOMAIN SAFETY:
    - Won't misfire on non-content domains
    - Industry-aware logic
    - Proper category filtering
    
    Returns:
        (policies, summary)
        - policies: List of policy evaluation results with enforcement_scope
        - summary: Aggregate statistics with domain context info
    """
    dsa: Dict[str, Any] = payload.get("dsa", {}) or {}
    risk = _risk_level(payload)
    policies: List[Dict[str, Any]] = []
    
    # ============================================================
    # CONTEXT DETECTION (FUTURE-PROOF)
    # ============================================================
    is_content_context = _is_dsa_content_context(payload)
    has_dsa_illegal = _has_dsa_illegal_signal(payload)
    industry = str(payload.get("industry_id", "")).upper().strip()
    
    # ============================================================
    # DSA Art. 34 - Illegal/Harmful Content Detection
    # ============================================================
    # FUTURE-PROOF: Create policy but DON'T return early
    # Let constitutional veto handle blocking decisions
    
    if is_content_context and has_dsa_illegal:
        # DSA illegal content in content context - create VIOLATED policy
        risk_indicators = payload.get("risk_indicators", {})
        violation_cat = str(risk_indicators.get("violation_category", "")).lower()
        previous_violations = risk_indicators.get("previous_violations", 0)
        
        _add_policy(
            policies,
            article="DSA Art. 34",
            category="Illegal/harmful content",
            status="VIOLATED",
            severity="CRITICAL",
            impact="BLOCKING - DSA illegal content detected in platform context. Hard DENY.",
            trigger_type="CONTENT_SAFETY",
            rule_ids=["DSA_ART34_HARMFUL_CONTENT_BLOCK"],
            enforcement_scope="TRANSACTION",  # ALWAYS blocks illegal content
            notes=f"DSA illegal content detected: {violation_cat or 'general harm'}. "
                  f"Previous violations: {previous_violations}. "
                  f"Context: industry={industry}, action={payload.get('action')}.",
            evidence={
                "harmful_content_flag": risk_indicators.get("harmful_content_flag"),
                "violation_category": violation_cat,
                "previous_violations": previous_violations,
                "context_industry": industry,
                "is_content_context": is_content_context,
            }
        )
    
    # ============================================================
    # SYSTEMIC & PLATFORM OBLIGATIONS (Art. 34-42)
    # These have dynamic enforcement scope based on context
    # ============================================================
    
    # -------------------------------------------------------------
    # Art. 34 – Systemic risk assessment & mitigation
    # -------------------------------------------------------------
    if dsa.get("systemic_risk_assessed", False) and dsa.get("mitigation_measures_in_place", False):
        status = "SATISFIED"
        severity = "LOW"
        impact = "Compliant systemic risk programme; supports ALLOW."
        notes = "Periodic risk assessments and mitigation measures in place."
    else:
        status = "VIOLATED"
        severity = _bump_severity("HIGH", risk)
        impact = "Systemic risk obligations not met. VLOP platforms: may block execution."
        notes = "No adequate systemic risk assessment and/or mitigation measures."
    
    _add_policy(
        policies,
        article="DSA Art. 34",
        category="Systemic risk mitigation",
        status=status,
        severity=severity,
        impact=impact,
        trigger_type="DUTY_OF_CARE",
        rule_ids=["DSA_ART34_SYSTEMIC_RISK"],
        enforcement_scope=_resolve_enforcement_scope("Art. 34", payload),
        notes=notes,
    )
    
    # -------------------------------------------------------------
    # Art. 35 – Independent audits
    # -------------------------------------------------------------
    if dsa.get("independent_audit_last_12m", False):
        status = "SATISFIED"
        severity = "LOW"
        impact = "Audit obligations met for this period."
        notes = "Recent independent audit and remediation plan."
    else:
        status = "VIOLATED"
        severity = _bump_severity("MEDIUM", risk)
        impact = "Audit obligations not met. VLOP platforms: contributes to enforcement action."
        notes = "No recent independent audit or audit deemed ineffective."
    
    _add_policy(
        policies,
        article="DSA Art. 35",
        category="Independent audits",
        status=status,
        severity=severity,
        impact=impact,
        trigger_type="AUDIT_EVIDENCE",
        rule_ids=["DSA_ART35_AUDIT"],
        enforcement_scope=_resolve_enforcement_scope("Art. 35", payload),
        notes=notes,
    )
    
    # -------------------------------------------------------------
    # Art. 36 – Risk mitigation measures (crisis protocols)
    # -------------------------------------------------------------
    if dsa.get("crisis_protocol_defined", False) and dsa.get("crisis_protocol_tested", False):
        status = "SATISFIED"
        severity = "LOW"
        impact = "Crisis protocols defined and tested; reduces residual risk."
        notes = "Crisis response procedures documented and tested."
    else:
        status = "VIOLATED"
        severity = _bump_severity("HIGH", risk)
        impact = "No effective crisis protocol; materially increases systemic risk."
        notes = "Crisis protocol missing or not adequately tested."
    
    _add_policy(
        policies,
        article="DSA Art. 36",
        category="Crisis protocol & mitigation",
        status=status,
        severity=severity,
        impact=impact,
        trigger_type="CRISIS_PROTOCOL",
        rule_ids=["DSA_ART36_CRISIS_PROTOCOL"],
        enforcement_scope=_resolve_enforcement_scope("Art. 36", payload),
        notes=notes,
    )
    
    # -------------------------------------------------------------
    # Art. 37 – Data access for regulators & vetted researchers
    # -------------------------------------------------------------
    access = str(dsa.get("researcher_data_access", "NONE")).upper()
    if access == "FULL":
        status = "SATISFIED"
        severity = "LOW"
        impact = "Data access conditions satisfied for regulators/vetted researchers."
        notes = "Full data access provided to authorized entities."
    elif access == "PARTIAL":
        status = "VIOLATED"
        severity = _bump_severity("MEDIUM", risk)
        impact = "Partial data access; non-blocking but raises medium concern."
        notes = "Partial data access granted; some restrictions remain."
    else:  # NONE / unknown
        status = "VIOLATED"
        severity = _bump_severity("HIGH", risk)
        impact = "VLOP platforms: may block; regulators cannot access required data."
        notes = "No data access provided to regulators/researchers."
    
    _add_policy(
        policies,
        article="DSA Art. 37",
        category="Data access for regulators & researchers",
        status=status,
        severity=severity,
        impact=impact,
        trigger_type="DATA_ACCESS",
        rule_ids=["DSA_ART37_DATA_ACCESS"],
        enforcement_scope=_resolve_enforcement_scope("Art. 37", payload),
        notes=notes,
    )
    
    # -------------------------------------------------------------
    # Art. 38 – Non-profiling / recommender choice
    # -------------------------------------------------------------
    if dsa.get("non_profiling_option_exposed", False):
        status = "SATISFIED"
        severity = "LOW"
        impact = "Non-profiling recommender option exposed to users."
        notes = "Users can choose non-profiling content recommendation."
    else:
        status = "VIOLATED"
        severity = _bump_severity("MEDIUM", risk)
        impact = "Users lack non-profiling option; VLOP platforms: may escalate."
        notes = "No non-profiling recommender option available to users."
    
    _add_policy(
        policies,
        article="DSA Art. 38",
        category="Non-profiling recommender option",
        status=status,
        severity=severity,
        impact=impact,
        trigger_type="UI_CONFIG",
        rule_ids=["DSA_ART38_NON_PROFILING"],
        enforcement_scope=_resolve_enforcement_scope("Art. 38", payload),
        notes=notes,
    )
    
    # -------------------------------------------------------------
    # Art. 39 – Protection of minors
    # -------------------------------------------------------------
    if dsa.get("minors_risk_programme", False) and dsa.get("age_assurance_controls", False):
        status = "SATISFIED"
        severity = "LOW"
        impact = "Specific risk mitigation for minors is in place."
        notes = "Age verification and minors protection programme operational."
    else:
        status = "VIOLATED"
        severity = _bump_severity("CRITICAL", risk)
        impact = "Critical when service targets/has significant minors – can hard-block to DENY."
        notes = "Insufficient minors protection measures. HIGH PRIORITY."
    
    _add_policy(
        policies,
        article="DSA Art. 39",
        category="Protection of minors",
        status=status,
        severity=severity,
        impact=impact,
        trigger_type="MINORS_PROTECTION",
        rule_ids=["DSA_ART39_MINORS"],
        enforcement_scope=_resolve_enforcement_scope("Art. 39", payload),
        notes=notes,
    )
    
    # -------------------------------------------------------------
    # Art. 40 – Transparency reporting
    # -------------------------------------------------------------
    if dsa.get("transparency_report_published", False):
        status = "SATISFIED"
        severity = "LOW"
        impact = "Transparency reporting obligations met."
        notes = "Bi-annual transparency report published."
    else:
        status = "VIOLATED"
        severity = _bump_severity("MEDIUM", risk)
        impact = "Missing/late transparency reporting; VLOP platforms: adds compliance risk."
        notes = "Transparency report overdue or not published."
    
    _add_policy(
        policies,
        article="DSA Art. 40",
        category="Transparency reporting",
        status=status,
        severity=severity,
        impact=impact,
        trigger_type="REPORTING",
        rule_ids=["DSA_ART40_REPORTING"],
        enforcement_scope=_resolve_enforcement_scope("Art. 40", payload),
        notes=notes,
    )
    
    # -------------------------------------------------------------
    # Art. 41 – Internal complaint-handling system
    # -------------------------------------------------------------
    if dsa.get("internal_complaint_system_available", False):
        status = "SATISFIED"
        severity = "LOW"
        impact = "Internal complaint-handling system compliant with DSA."
        notes = "Complaint mechanism accessible and responsive."
    else:
        status = "VIOLATED"
        severity = _bump_severity("MEDIUM", risk)
        impact = "No compliant internal complaint-handling system."
        notes = "Internal complaint mechanism missing or non-compliant."
    
    _add_policy(
        policies,
        article="DSA Art. 41",
        category="Internal complaint-handling",
        status=status,
        severity=severity,
        impact=impact,
        trigger_type="COMPLAINTS",
        rule_ids=["DSA_ART41_COMPLAINTS"],
        enforcement_scope=_resolve_enforcement_scope("Art. 41", payload),
        notes=notes,
    )
    
    # -------------------------------------------------------------
    # Art. 42 – Out-of-court dispute settlement
    # -------------------------------------------------------------
    if dsa.get("out_of_court_body_recognised", False):
        status = "SATISFIED"
        severity = "LOW"
        impact = "Out-of-court dispute mechanisms recognised and integrated."
        notes = "Certified out-of-court dispute resolution available."
    else:
        status = "VIOLATED"
        severity = _bump_severity("MEDIUM", risk)
        impact = "Users lack effective out-of-court dispute settlement options."
        notes = "No certified dispute resolution mechanism."
    
    _add_policy(
        policies,
        article="DSA Art. 42",
        category="Out-of-court dispute settlement",
        status=status,
        severity=severity,
        impact=impact,
        trigger_type="DISPUTE_RESOLUTION",
        rule_ids=["DSA_ART42_DISPUTE"],
        enforcement_scope=_resolve_enforcement_scope("Art. 42", payload),
        notes=notes,
    )
    
    # -------------------------------------------------------------
    # Art. 43–62 (stubs for future implementation)
    # -------------------------------------------------------------
    stub_articles = [
        "DSA Art. 43", "DSA Art. 44", "DSA Art. 45", "DSA Art. 46",
        "DSA Art. 47", "DSA Art. 48", "DSA Art. 49", "DSA Art. 50",
        "DSA Art. 51", "DSA Art. 52", "DSA Art. 53", "DSA Art. 54",
        "DSA Art. 55", "DSA Art. 56", "DSA Art. 57", "DSA Art. 58",
        "DSA Art. 59", "DSA Art. 60", "DSA Art. 61", "DSA Art. 62",
    ]
    for art in stub_articles:
        _add_policy(
            policies,
            article=art,
            category="Stub – wiring placeholder",
            status="NOT_APPLICABLE",
            severity="LOW",
            impact="Stub article – currently neutral; does not affect verdict.",
            trigger_type="STUB",
            rule_ids=[art.replace(" ", "_").replace(".", "").upper() + "_STUB"],
            enforcement_scope="SUPERVISORY",  # Stubs don't block
            notes="Extend with real rule logic when ready.",
        )
    
    # ============================================================
    # SUMMARY STATISTICS (FUTURE-PROOF)
    # ============================================================
    total_rules = len(policies)
    failed = sum(1 for p in policies if p.get("status") == "VIOLATED")
    passed = sum(1 for p in policies if p.get("status") == "SATISFIED")
    
    # Count ONLY transaction-scoped violations (these can block)
    blocking_failures = sum(
        1
        for p in policies
        if p.get("status") == "VIOLATED"
        and str(p.get("severity", "")).upper() in {"HIGH", "CRITICAL"}
        and p.get("enforcement_scope") == "TRANSACTION"
    )
    
    # Count context-specific violations
    illegal_content_violations = sum(
        1 for p in policies 
        if p.get("article") == "DSA Art. 34" 
        and p.get("status") == "VIOLATED"
        and p.get("trigger_type") == "CONTENT_SAFETY"
    )
    
    summary = {
        "total_rules": total_rules,
        "passed": passed,
        "failed": failed,
        "blocking_failures": blocking_failures,
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
        "illegal_content_violations": illegal_content_violations,
        "context_industry": industry,
        "is_content_context": is_content_context,
        "has_dsa_illegal_signal": has_dsa_illegal,
        "context_gated": illegal_content_violations > 0,
    }
    
    return policies, summary