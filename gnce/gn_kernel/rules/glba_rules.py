# gnce/gn_kernel/rules/glba_rules.py
"""
Gramm-Leach-Bliley Act (GLBA) Rule Evaluator with Constitutional Binding (v0.7.2-RC-FUTUREPROOF)

CRITICAL UPDATES FOR FUTURE-PROOFING:
1. Comprehensive financial institution detection with multi-method verification
2. Non-Public Personal Information (NPI) handling detection
3. Jurisdiction-aware applicability (US financial institutions)
4. Industry and action filtering for financial privacy contexts
5. Enhanced enforcement scope resolution (Safeguards vs Privacy vs Pretexting)
6. Comprehensive evidence collection for audit trails
7. Cross-domain safety (won't misfire on non-financial entities)
8. Future GLBA rules ready for implementation

GLBA Reality (Future-Proof):
- Safeguards Rule (16 CFR Part 314): Technical safeguards for NPI (TRANSACTION/POSTURE)
- Privacy Rule (§6802-6803): Disclosure and opt-out requirements (TRANSACTION)
- Pretexting Provisions (§6821-6827): Anti-social engineering (TRANSACTION)
- Applies to "financial institutions" broadly defined (banks, insurers, investment advisors, etc.)
- Covers Non-Public Personal Information (NPI) of consumers
- US jurisdiction primarily, but may apply extraterritorially
"""

from typing import Dict, Any, List, Tuple, Set

# Load governance catalog for enforcement scope classification
from gnce.gn_kernel.constitution.constitution_catalog import load_governance_catalog_v05

# ============================================================
# MODULE CONSTANTS (FUTURE-PROOF)
# ============================================================

GLBA_FRAMEWORK = "US Financial Privacy"
GLBA_REGIME_ID = "GLBA"

# Load catalog once at module level (performance)
_GOVERNANCE_CATALOG = load_governance_catalog_v05()

# ============================================================
# FINANCIAL INSTITUTION DETECTION (FUTURE-PROOF)
# ============================================================

# GLBA-defined financial institutions (broad definition)
GLBA_FINANCIAL_INSTITUTIONS: Set[str] = {
    "BANK",
    "CREDIT_UNION",
    "INSURANCE_COMPANY",
    "SECURITIES_FIRM",
    "INVESTMENT_ADVISOR",
    "MORTGAGE_LENDER",
    "LOAN_BROKER",
    "PAYMENT_PROCESSOR",
    "FINANCIAL_ADVISOR",
    "CHECK_CASHING_BUSINESS",
    "CREDIT_COUNSELING",
    "DEBT_COLLECTOR",
    "FINTECH",
    "WEALTH_MANAGEMENT",
    "ASSET_MANAGEMENT",
    "TRUST_COMPANY",
}

# Non-Public Personal Information (NPI) types
NPI_TYPES: Set[str] = {
    "social_security_number",
    "bank_account_number",
    "credit_card_number",
    "financial_account_credentials",
    "credit_history",
    "income_information",
    "credit_score",
    "loan_application_data",
    "insurance_application_data",
    "investment_portfolio_details",
    "tax_return_information",
    "debt_information",
}

# Industries where GLBA typically applies
GLBA_INDUSTRIES: Set[str] = {
    "FINTECH",
    "INSURANCE",
    "BANKING",
    "INVESTMENT_BANKING",
    "WEALTH_MANAGEMENT",
    "ASSET_MANAGEMENT",
    "PAYMENTS",
    "LENDING",
    "CREDIT",
    "MORTGAGE",
    "REAL_ESTATE_FINANCE",
    "DEBT_COLLECTION",
}

# Jurisdictions where GLBA applies
GLBA_JURISDICTIONS: Set[str] = {
    "US",
    "USA",
    "UNITED_STATES",
    "US-NY",  # New York
    "US-CA",  # California
    "US-TX",  # Texas
    "US-IL",  # Illinois
    # Potentially applies extraterritorially for US consumers
    "GLOBAL_US_CONSUMERS",
}

# Actions where GLBA obligations are relevant
GLBA_RELEVANT_ACTIONS: Set[str] = {
    # Customer data handling
    "collect_customer_data",
    "store_customer_data",
    "process_customer_data",
    "transmit_customer_data",
    "share_customer_data",
    "analyze_customer_data",
    
    # Financial operations
    "open_account",
    "close_account",
    "process_payment",
    "approve_loan",
    "underwrite_insurance",
    "manage_investment",
    
    # Privacy operations
    "provide_privacy_notice",
    "process_opt_out",
    "disclose_to_affiliates",
    "disclose_to_nonaffiliates",
    
    # Security operations
    "authenticate_customer",
    "authorize_access",
    "encrypt_data",
    "audit_access",
    "detect_intrusion",
}

# Actions where GLBA likely doesn't apply (future-proof exclusions)
NON_GLBA_ACTIONS: Set[str] = {
    # Non-financial actions
    "login",
    "logout",
    "view_content",
    "download_file",
    "print_document",
    
    # Simple data operations (non-NPI)
    "store_log_data",
    "retrieve_public_data",
    "delete_temporary_data",
    
    # System management
    "system_backup",
    "update_software",
    "monitor_performance",
    "generate_report",
}

# GLBA Rule Components
GLBA_SAFEGUARDS_RULE = "16 CFR Part 314"
GLBA_PRIVACY_RULE = "15 U.S.C. §6802-6803"
GLBA_PRETEXTING_PROVISIONS = "15 U.S.C. §6821-6827"
GLBA_DISPOSAL_RULE = "16 CFR Part 682"

# ============================================================
# FINANCIAL INSTITUTION & NPI DETECTION (FUTURE-PROOF)
# ============================================================

def _detect_financial_institution(payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Future-proof financial institution detection with comprehensive verification.
    
    Returns:
        (is_financial_institution, detection_evidence)
    """
    detection_evidence = {
        "methods_used": [],
        "indicators_found": [],
        "confidence": "LOW",
    }
    
    glba_profile = payload.get("glba_profile", {})
    meta = payload.get("meta", {})
    
    # Method 1: Explicit financial institution flag
    if glba_profile.get("financial_institution") or glba_profile.get("is_financial_institution"):
        detection_evidence["methods_used"].append("EXPLICIT_FLAG")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["indicators_found"].append("explicit_fi_flag")
        return True, detection_evidence
    
    # Method 2: Industry classification
    industry = str(payload.get("industry_id", "")).upper().strip()
    if industry in GLBA_FINANCIAL_INSTITUTIONS:
        detection_evidence["methods_used"].append("INDUSTRY_CLASSIFICATION")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["indicators_found"].append(f"industry:{industry}")
        return True, detection_evidence
    
    # Method 3: Regulatory registrations
    reg_status = str(glba_profile.get("regulatory_status", "")).upper().strip()
    if any(fi_term in reg_status for fi_term in ["BANK", "INSURANCE", "SECURITIES", "FINANCIAL"]):
        detection_evidence["methods_used"].append("REGULATORY_STATUS")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["indicators_found"].append(f"regulatory_status:{reg_status}")
        return True, detection_evidence
    
    # Method 4: Business activities
    activities = glba_profile.get("business_activities", [])
    if isinstance(activities, list):
        fi_activities = [a for a in activities if any(fi_term in str(a).lower() 
                        for fi_term in ["banking", "lending", "insurance", "investment", "financial"])]
        if fi_activities:
            detection_evidence["methods_used"].append("BUSINESS_ACTIVITIES")
            detection_evidence["confidence"] = "MEDIUM"
            detection_evidence["indicators_found"].extend([f"activity:{a}" for a in fi_activities[:3]])
            return True, detection_evidence
    
    # Method 5: Customer type handling
    customer_type = str(glba_profile.get("customer_type", "")).lower()
    if "consumer" in customer_type or "retail" in customer_type:
        # Combined with other indicators
        detection_evidence["methods_used"].append("CUSTOMER_TYPE")
        detection_evidence["indicators_found"].append(f"customer_type:{customer_type}")
    
    # Method 6: Meta/platform signals
    platform_type = str(meta.get("platform_type", "")).lower()
    if any(fi_term in platform_type for fi_term in ["bank", "insurance", "lending", "financial"]):
        detection_evidence["methods_used"].append("PLATFORM_SIGNAL")
        detection_evidence["confidence"] = "MEDIUM"
        detection_evidence["indicators_found"].append(f"platform_type:{platform_type}")
        return True, detection_evidence
    
    # No financial institution detected with sufficient confidence
    if detection_evidence["confidence"] == "LOW":
        return False, detection_evidence
    
    return True, detection_evidence


def _detect_npi_handling(payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Detect if Non-Public Personal Information (NPI) is handled.
    
    Returns:
        (handles_npi, detection_evidence)
    """
    detection_evidence = {
        "methods_used": [],
        "npi_types_detected": [],
        "confidence": "LOW",
    }
    
    glba_profile = payload.get("glba_profile", {})
    
    # Method 1: Explicit NPI handling flag
    if glba_profile.get("handles_npi"):
        detection_evidence["methods_used"].append("EXPLICIT_NPI_FLAG")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["npi_types_detected"].append("explicit_npi_handling")
        return True, detection_evidence
    
    # Method 2: Specific NPI types declared
    npi_types = glba_profile.get("npi_types", [])
    if isinstance(npi_types, list) and npi_types:
        detection_evidence["methods_used"].append("NPI_TYPES_DECLARED")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["npi_types_detected"].extend(npi_types[:5])
        return True, detection_evidence
    
    # Method 3: Data classification
    data_classes = glba_profile.get("data_classification", [])
    if isinstance(data_classes, list) and any("confidential" in str(c).lower() 
                                              or "restricted" in str(c).lower() 
                                              or "sensitive" in str(c).lower() 
                                              for c in data_classes):
        detection_evidence["methods_used"].append("DATA_CLASSIFICATION")
        detection_evidence["confidence"] = "MEDIUM"
        detection_evidence["npi_types_detected"].append("classified_sensitive_data")
        return True, detection_evidence
    
    # Method 4: Business context (financial institution + consumer data)
    is_fi, fi_evidence = _detect_financial_institution(payload)
    if is_fi:
        # Financial institutions handling consumer data likely handle NPI
        customer_type = str(glba_profile.get("customer_type", "")).lower()
        if "consumer" in customer_type or "retail" in customer_type:
            detection_evidence["methods_used"].append("CONTEXTUAL_INFERENCE")
            detection_evidence["confidence"] = "MEDIUM"
            detection_evidence["npi_types_detected"].append("consumer_financial_data")
            return True, detection_evidence
    
    return False, detection_evidence


def _should_evaluate_glba(payload: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Future-proof decision: Should GLBA evaluation run for this payload?
    
    Returns:
        (should_evaluate, evaluation_reason, context_evidence)
    """
    context_evidence = {
        "financial_institution_detection": {},
        "npi_handling_detection": {},
        "jurisdiction_check": {},
        "context_checks": {},
    }
    
    # Check 1: Financial institution detection
    is_fi, fi_evidence = _detect_financial_institution(payload)
    context_evidence["financial_institution_detection"] = fi_evidence
    
    if not is_fi:
        return False, "NOT_FINANCIAL_INSTITUTION", context_evidence
    
    # Check 2: NPI handling detection
    handles_npi, npi_evidence = _detect_npi_handling(payload)
    context_evidence["npi_handling_detection"] = npi_evidence
    
    if not handles_npi:
        return False, "NOT_HANDLING_NPI", context_evidence
    
    # Check 3: Jurisdiction
    meta = payload.get("meta", {})
    jurisdiction = str(meta.get("jurisdiction", "")).upper().strip()
    context_evidence["jurisdiction_check"]["jurisdiction"] = jurisdiction
    
    if jurisdiction not in GLBA_JURISDICTIONS:
        # GLBA primarily US, but may apply for US consumers globally
        consumer_location = str(meta.get("consumer_location", "")).upper().strip()
        if consumer_location not in {"US", "USA", "UNITED_STATES"}:
            return False, f"JURISDICTION_OUTSIDE_US: {jurisdiction}", context_evidence
    
    # Check 4: Action relevance
    action = str(payload.get("action", "")).lower().strip()
    context_evidence["context_checks"]["action"] = action
    
    if action in NON_GLBA_ACTIONS:
        return False, f"ACTION_EXCLUDED: {action}", context_evidence
    
    # All checks passed - evaluate GLBA
    return True, "EVALUATE_GLBA", context_evidence


# ============================================================
# ENFORCEMENT SCOPE RESOLUTION (FUTURE-PROOF)
# ============================================================

def _normalize_article(article: str) -> str:
    """
    Normalize GLBA article/rule identifier for consistent comparison.
    
    Future-proof examples:
        "15 U.S.C. §6801(b)" → "6801"
        "16 CFR Part 314" → "CFR314"
        "GLBA Safeguards Rule" → "SAFEGUARDS"
        "Privacy Rule" → "PRIVACY"
    """
    if not article:
        return ""
    
    article = article.upper().strip()
    
    # Extract USC section numbers
    import re
    usc_match = re.search(r"§?(\d+)[A-Z]?", article)
    if usc_match:
        return usc_match.group(1)
    
    # Extract CFR parts
    cfr_match = re.search(r"CFR\s*PART?\s*(\d+)", article)
    if cfr_match:
        return f"CFR{cfr_match.group(1)}"
    
    # Common rule names
    if "SAFEGUARD" in article:
        return "SAFEGUARDS"
    elif "PRIVACY" in article:
        return "PRIVACY"
    elif "PRETEXT" in article:
        return "PRETEXTING"
    elif "DISPOSAL" in article:
        return "DISPOSAL"
    
    # Return cleaned string
    return article.replace(" ", "_").replace(".", "").replace("§", "")


def _get_glba_base_enforcement_scope(article: str) -> str:
    """
    Get base enforcement scope from governance catalog.
    
    Future-proof GLBA Classification:
    - Safeguards Rule (CFR 314): TRANSACTION/POSTURE for security controls
    - Privacy Rule (USC 6802-6803): TRANSACTION for disclosures
    - Pretexting Provisions: TRANSACTION for anti-fraud
    - Disposal Rule: TRANSACTION/POSTURE for data destruction
    
    Returns: "TRANSACTION" | "POSTURE" | "PLATFORM_AUDIT" | "SUPERVISORY"
    Default: "TRANSACTION" (safe - financial privacy rules often block)
    """
    article_normalized = _normalize_article(article)
    
    for regime in _GOVERNANCE_CATALOG.get("regimes", []):
        if regime.get("id") == GLBA_REGIME_ID:
            for domain in regime.get("domains", []):
                for art_def in domain.get("articles", []):
                    art_num = _normalize_article(art_def.get("article", ""))
                    if art_num == article_normalized:
                        return art_def.get("enforcement_scope", "TRANSACTION")
    
    # Default based on rule type
    if article_normalized == "SAFEGUARDS":
        return "POSTURE"  # Safeguards are often ongoing programs
    elif article_normalized == "PRIVACY":
        return "TRANSACTION"  # Privacy notices are per-interaction
    else:
        return "TRANSACTION"  # Conservative default


def _resolve_enforcement_scope(article: str, payload: Dict[str, Any]) -> str:
    """
    Resolve final enforcement scope with future-proof modifiers.
    
    GLBA enforcement scope modifiers:
    1. Base scope from catalog
    2. Data sensitivity modifiers
    3. Action-specific considerations
    4. Customer impact considerations
    
    Returns:
        Final enforcement scope after applying modifiers
    """
    base_scope = _get_glba_base_enforcement_scope(article)
    article_normalized = _normalize_article(article)
    
    # Extract context for modifiers
    action = str(payload.get("action", "")).lower().strip()
    glba_profile = payload.get("glba_profile", {})
    
    # MODIFIER 1: High-sensitivity NPI escalates to TRANSACTION
    npi_types = glba_profile.get("npi_types", [])
    high_sensitivity_types = {"social_security_number", "bank_account_number", "credit_card_number"}
    
    if any(npi_type in high_sensitivity_types for npi_type in npi_types):
        if base_scope == "POSTURE":
            # High-sensitivity NPI needs immediate enforcement
            return "TRANSACTION"
    
    # MODIFIER 2: Real-time customer interactions
    real_time_actions = {"authenticate_customer", "process_payment", "approve_loan"}
    if action in real_time_actions and base_scope == "POSTURE":
        return "TRANSACTION"
    
    # MODIFIER 3: Large volume data handling
    if glba_profile.get("large_scale_data_processing") and base_scope == "PLATFORM_AUDIT":
        return "TRANSACTION"
    
    # No modifiers applied
    return base_scope


# ============================================================
# EVIDENCE COLLECTION (Enhanced for Future-Proofing)
# ============================================================

def _collect_glba_evidence(payload: Dict[str, Any], rule_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect comprehensive GLBA evidence for audit trails.
    
    Returns:
        Structured evidence with context, rule data, and metadata
    """
    evidence = {
        # Context evidence
        "context": {
            "industry_id": payload.get("industry_id"),
            "action": payload.get("action"),
            "jurisdiction": (payload.get("meta") or {}).get("jurisdiction"),
            "financial_institution_detected": True,
            "npi_handling_detected": True,
        },
        # Rule-specific evidence
        "rule_data": rule_data,
        # GLBA-specific information
        "glba_info": {},
        # Metadata
        "metadata": {
            "evidence_collected_at": "NOW",  # Would be timestamp in real implementation
        }
    }
    
    # Collect GLBA-specific information
    glba_profile = payload.get("glba_profile", {})
    evidence["glba_info"] = {
        "npi_types": glba_profile.get("npi_types", []),
        "consumer_count": glba_profile.get("consumer_count"),
        "data_volume": glba_profile.get("data_volume"),
        "regulatory_status": glba_profile.get("regulatory_status"),
    }
    
    return evidence


# ============================================================
# GLBA RULE DEFINITIONS (Enhanced with Future Rules)
# ============================================================

# Core GLBA rules with comprehensive metadata
GLBA_RULES = [
    {
        "article": "15 U.S.C. §6801(b)",
        "title": "Safeguards Rule - Information Security Program",
        "description": "Financial institutions must implement a comprehensive information security program.",
        "field": "information_security_program",
        "severity": "HIGH",
        "rule_id": "GLBA_SAFEGUARDS_PROGRAM",
        "enforcement_scope_default": "POSTURE",
        "future_proof_notes": "Must include risk assessment, safeguards, testing, and oversight.",
        "evidence_fields": ["glba_profile.information_security_program", "glba_profile.risk_assessment"],
    },
    {
        "article": "16 CFR Part 314",
        "title": "Access Controls for NPI",
        "description": "Customer non-public personal information must be protected by access controls.",
        "field": "access_controls",
        "severity": "HIGH",
        "rule_id": "GLBA_ACCESS_CONTROLS",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Role-based access control (RBAC), least privilege, authentication required.",
        "evidence_fields": ["glba_profile.access_controls", "glba_profile.authentication_required"],
    },
    {
        "article": "16 CFR Part 314",
        "title": "Incident Response Program",
        "description": "Financial institutions must have an incident response capability for security breaches.",
        "field": "incident_response",
        "severity": "MEDIUM",
        "rule_id": "GLBA_INCIDENT_RESPONSE",
        "enforcement_scope_default": "POSTURE",
        "future_proof_notes": "Must include detection, response, notification, and recovery procedures.",
        "evidence_fields": ["glba_profile.incident_response", "glba_profile.breach_notification_procedures"],
    },
    {
        "article": "15 U.S.C. §6802",
        "title": "Privacy Notice - Initial Disclosure",
        "description": "Financial institutions must provide initial privacy notice to consumers.",
        "field": "privacy_notice_provided",
        "severity": "MEDIUM",
        "rule_id": "GLBA_PRIVACY_NOTICE",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Must be clear, conspicuous, and provided at time of establishing relationship.",
        "evidence_fields": ["glba_profile.privacy_notice_provided", "glba_profile.notice_timing"],
        "future_implementation": True,
    },
    {
        "article": "15 U.S.C. §6802(b)",
        "title": "Privacy Notice - Annual Disclosure",
        "description": "Financial institutions must provide annual privacy notice to customers.",
        "field": "annual_privacy_notice",
        "severity": "MEDIUM",
        "rule_id": "GLBA_ANNUAL_NOTICE",
        "enforcement_scope_default": "POSTURE",
        "future_proof_notes": "Must be provided at least once per calendar year.",
        "evidence_fields": ["glba_profile.annual_privacy_notice", "glba_profile.last_notice_date"],
        "future_implementation": True,
    },
    {
        "article": "15 U.S.C. §6802(c)",
        "title": "Opt-Out Right for Nonaffiliate Sharing",
        "description": "Consumers must have right to opt-out of sharing with nonaffiliated third parties.",
        "field": "opt_out_mechanism",
        "severity": "HIGH",
        "rule_id": "GLBA_OPT_OUT",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Must provide clear opt-out method and honor requests.",
        "evidence_fields": ["glba_profile.opt_out_mechanism", "glba_profile.opt_out_requests_honored"],
        "future_implementation": True,
    },
    {
        "article": "15 U.S.C. §6821",
        "title": "Pretexting Protection",
        "description": "Prohibits obtaining customer information under false pretenses.",
        "field": "pretexting_protections",
        "severity": "HIGH",
        "rule_id": "GLBA_PRETEXTING",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Must implement controls to prevent social engineering attacks.",
        "evidence_fields": ["glba_profile.pretexting_protections", "glba_profile.social_engineering_training"],
        "future_implementation": True,
    },
    {
        "article": "16 CFR Part 682",
        "title": "Disposal Rule",
        "description": "Proper disposal of consumer information to prevent unauthorized access.",
        "field": "secure_disposal",
        "severity": "MEDIUM",
        "rule_id": "GLBA_DISPOSAL",
        "enforcement_scope_default": "POSTURE",
        "future_proof_notes": "Must destroy or erase electronic and physical records containing NPI.",
        "evidence_fields": ["glba_profile.secure_disposal", "glba_profile.disposal_procedures"],
        "future_implementation": True,
    },
    {
        "article": "16 CFR Part 314",
        "title": "Employee Training",
        "description": "Train employees on information security and GLBA compliance.",
        "field": "employee_training",
        "severity": "MEDIUM",
        "rule_id": "GLBA_EMPLOYEE_TRAINING",
        "enforcement_scope_default": "POSTURE",
        "future_proof_notes": "Regular training on safeguards, privacy, and incident response.",
        "evidence_fields": ["glba_profile.employee_training", "glba_profile.training_frequency"],
        "future_implementation": True,
    },
    {
        "article": "16 CFR Part 314",
        "title": "Service Provider Oversight",
        "description": "Oversee service providers that handle NPI through due diligence and contracts.",
        "field": "service_provider_oversight",
        "severity": "MEDIUM",
        "rule_id": "GLBA_SERVICE_PROVIDER",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Contractual requirements and regular oversight of third parties.",
        "evidence_fields": ["glba_profile.service_provider_oversight", "glba_profile.third_party_contracts"],
        "future_implementation": True,
    },
]


# ============================================================
# MAIN EVALUATION FUNCTION (Future-Proof Architecture)
# ============================================================

def evaluate_glba_rules(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Future-proof GLBA evaluation with comprehensive context gating.
    
    Features:
    1. Multi-method financial institution detection
    2. NPI handling detection
    3. Jurisdiction and action filtering
    4. Industry-aware applicability
    5. Enhanced enforcement scope resolution
    6. Comprehensive evidence collection
    7. Detailed context tracking
    
    Returns:
        (policies, summary)
        - policies: List with enforcement_scope, evidence, and context
        - summary: Aggregate statistics with detailed context info
    """
    policies: List[Dict[str, Any]] = []
    
    # ============================================================
    # FUTURE-PROOF: CONTEXT GATING DECISION
    # ============================================================
    should_evaluate, evaluation_reason, context_evidence = _should_evaluate_glba(payload)
    
    if not should_evaluate:
        # GLBA doesn't apply to this context - return early with explanation
        summary = {
            "total_rules": 0,
            "passed": 0,
            "failed": 0,
            "blocking_failures": 0,
            "regime": "GLBA",
            "context_gated": True,
            "evaluation_decision": evaluation_reason,
            "context_evidence": context_evidence,
            "notes": f"GLBA evaluation skipped: {evaluation_reason}"
        }
        return policies, summary
    
    # ============================================================
    # RULE EVALUATION (Enhanced with Evidence Collection)
    # ============================================================
    
    evaluation_errors = []
    glba_profile = payload.get("glba_profile") or {}
    
    for rule_def in GLBA_RULES:
        # Skip future implementation rules if not ready
        if rule_def.get("future_implementation") and not glba_profile.get("enable_future_rules"):
            continue
        
        try:
            # Check if the required field exists and is compliant
            field_value = glba_profile.get(rule_def["field"])
            
            # Determine status based on field value
            if field_value is False:
                status = "VIOLATED"
            elif field_value is True:
                status = "SATISFIED"
            elif field_value is None:
                # Missing field - conservative approach
                status = "NOT_APPLICABLE"
            else:
                # Other values (e.g., strings, numbers) - treat as satisfied
                status = "SATISFIED"
            
            # Collect evidence for this rule
            rule_evidence = {}
            for evidence_field in rule_def.get("evidence_fields", []):
                if "." in evidence_field:
                    # Nested field
                    parts = evidence_field.split(".")
                    obj = payload
                    for part in parts[:-1]:
                        obj = obj.get(part, {})
                    rule_evidence[evidence_field] = obj.get(parts[-1])
                else:
                    # Simple field
                    rule_evidence[evidence_field] = payload.get(evidence_field)
            
            # Get enforcement scope
            enforcement_scope = _resolve_enforcement_scope(rule_def["article"], payload)
            
            # Determine impact on verdict
            if status == "VIOLATED" and rule_def["severity"] in {"HIGH", "CRITICAL"}:
                impact_on_verdict = "BLOCKING_FAILURE"
            elif status == "VIOLATED":
                impact_on_verdict = "NON_BLOCKING"
            else:
                impact_on_verdict = "COMPLIANT"
            
            # Create policy
            policy = {
                "domain": "Gramm-Leach-Bliley Act (GLBA)",
                "regime": "GLBA",
                "framework": GLBA_FRAMEWORK,
                "domain_id": "GLBA",
                "article": rule_def["article"],
                "category": rule_def["title"],
                "title": rule_def["title"],
                "status": status,
                "severity": rule_def["severity"] if status == "VIOLATED" else "LOW",
                "enforcement_scope": enforcement_scope,
                "impact_on_verdict": impact_on_verdict,
                "trigger_type": "GLBA_SAFEGUARD",
                "rule_ids": [rule_def["rule_id"]],
                "notes": rule_def["description"],
                "evidence": _collect_glba_evidence(payload, rule_evidence),
                "remediation": (
                    f"Implement {rule_def['title']} controls per GLBA requirements. "
                    "Document procedures and re-run GNCE after remediation."
                    if status == "VIOLATED" else "No remediation required."
                ),
                "violation_detail": rule_def["description"] if status == "VIOLATED" else "",
                "control_severity": rule_def["severity"] if status == "VIOLATED" else "LOW",
                # Future-proof metadata
                "metadata": {
                    "future_proof_notes": rule_def.get("future_proof_notes", ""),
                    "future_implementation": rule_def.get("future_implementation", False),
                }
            }
            
            policies.append(policy)
            
        except Exception as e:
            # Safety: if rule evaluation fails, log error and continue
            evaluation_errors.append({
                "rule": rule_def.get("article", "UNKNOWN"),
                "error": str(e),
                "action": payload.get("action"),
            })
            # Continue evaluation - don't crash kernel
    
    # ============================================================
    # SUMMARY STATISTICS (Comprehensive)
    # ============================================================
    
    failed = sum(p["status"] == "VIOLATED" for p in policies)
    passed = sum(p["status"] == "SATISFIED" for p in policies)
    
    # Count ONLY transaction-scoped violations (can block)
    blocking = sum(
        p["status"] == "VIOLATED" 
        and p["severity"] in {"HIGH", "CRITICAL"}
        and p.get("enforcement_scope") == "TRANSACTION"
        for p in policies
    )
    
    # Context information for debugging
    is_fi, fi_evidence = _detect_financial_institution(payload)
    handles_npi, npi_evidence = _detect_npi_handling(payload)
    
    context_info = {
        "industry": payload.get("industry_id"),
        "action": payload.get("action"),
        "jurisdiction": (payload.get("meta") or {}).get("jurisdiction"),
        "financial_institution_detected": is_fi,
        "npi_handling_detected": handles_npi,
        "glba_profile_exists": bool(payload.get("glba_profile")),
    }
    
    summary = {
        "regime": "GLBA",
        "applicable": True,
        "total_rules": len(policies),
        "passed": passed,
        "failed": failed,
        "blocking_failures": blocking,
        "context_gated": False,
        "evaluation_decision": evaluation_reason,
        # Scope-specific violation counts
        "posture_violations": sum(
            p["status"] == "VIOLATED"
            and p.get("enforcement_scope") == "POSTURE"
            for p in policies
        ),
        "platform_audit_violations": sum(
            p["status"] == "VIOLATED"
            and p.get("enforcement_scope") == "PLATFORM_AUDIT"
            for p in policies
        ),
        "transaction_violations": sum(
            p["status"] == "VIOLATED"
            and p.get("enforcement_scope") == "TRANSACTION"
            for p in policies
        ),
        # Context info
        "context": context_info,
        "context_evidence": context_evidence,
        # Detection evidence
        "financial_institution_detection": fi_evidence,
        "npi_handling_detection": npi_evidence,
        # Rule statistics
        "core_rules_evaluated": len([r for r in GLBA_RULES if not r.get("future_implementation")]),
        "future_rules_available": len([r for r in GLBA_RULES if r.get("future_implementation")]),
        "future_rules_evaluated": len([r for r in GLBA_RULES if r.get("future_implementation") 
                                      and glba_profile.get("enable_future_rules")]),
        # GLBA-specific statistics
        "safeguards_rules": sum(1 for r in GLBA_RULES if "SAFEGUARD" in r["rule_id"]),
        "privacy_rules": sum(1 for r in GLBA_RULES if "PRIVACY" in r["rule_id"] or "NOTICE" in r["rule_id"]),
        "security_rules": sum(1 for r in GLBA_RULES if "ACCESS" in r["rule_id"] or "INCIDENT" in r["rule_id"]),
        # Error tracking
        "evaluation_errors": evaluation_errors if evaluation_errors else None,
    }
    
    return policies, summary