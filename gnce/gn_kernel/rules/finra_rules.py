# gnce/gn_kernel/rules/finra_rules.py
"""
FINRA Rule Evaluator with Constitutional Binding (v0.7.2-RC-FUTUREPROOF)

CRITICAL UPDATES FOR FUTURE-PROOFING:
1. Comprehensive broker-dealer detection with multiple verification methods
2. Jurisdiction-aware FINRA applicability (US only)
3. Industry and action filtering for financial contexts
4. Enhanced enforcement scope resolution
5. Comprehensive evidence collection for audit trails
6. Cross-domain safety (won't misfire on non-financial entities)
7. Future FINRA rules ready for implementation

FINRA Reality (Future-Proof):
- All rules are TRANSACTION scope (financial compliance is strict)
- Only applies to registered broker-dealers in US jurisdiction
- No escalation logic (binary: broker-dealer or not)
- Strictest enforcement of all regimes
- SEC/FINRA dual regulation awareness
"""

from typing import Dict, Any, List, Tuple, Set

# Load governance catalog for enforcement scope classification
from gnce.gn_kernel.constitution.constitution_catalog import load_governance_catalog_v05

# ============================================================
# MODULE CONSTANTS (FUTURE-PROOF)
# ============================================================

FINRA_FRAMEWORK = "Financial / Markets Compliance"
FINRA_REGIME_ID = "FINRA"

# Load catalog once at module level (performance)
_GOVERNANCE_CATALOG = load_governance_catalog_v05()

# ============================================================
# BROKER-DEALER DETECTION (FUTURE-PROOF)
# ============================================================

# SEC/FINRA registration statuses (future-proof)
BROKER_DEALER_REGISTRATION_STATUSES: Set[str] = {
    "REGISTERED",
    "ACTIVE",
    "MEMBER_FIRM",
    "LICENSED",
    "AUTHORIZED",
    "APPROVED",
    "CLEARING_FIRM",
    "INTRODUCING_BROKER",
}

# Financial activities requiring broker-dealer registration
BROKER_DEALER_ACTIVITIES: Set[str] = {
    "execute_trade",
    "process_securities_order",
    "manage_customer_account",
    "provide_investment_advice",
    "underwrite_securities",
    "market_making",
    "clear_transactions",
    "custody_assets",
    "margin_lending",
    "corporate_financing",
}

# Industries where broker-dealer registration is typical
BROKER_DEALER_INDUSTRIES: Set[str] = {
    "FINTECH",
    "INVESTMENT_BANKING",
    "WEALTH_MANAGEMENT",
    "BROKERAGE",
    "ASSET_MANAGEMENT",
    "HEDGE_FUND",
    "PRIVATE_EQUITY",
    "VENTURE_CAPITAL",
    "INSURANCE_BROKERAGE",
}

# Jurisdictions where FINRA applies
FINRA_JURISDICTIONS: Set[str] = {
    "US",
    "USA",
    "UNITED_STATES",
    "US-NY",  # New York
    "US-CA",  # California
    "US-IL",  # Illinois
    "US-TX",  # Texas
}

# Actions where FINRA obligations are relevant
FINRA_RELEVANT_ACTIONS: Set[str] = {
    # Trading and execution
    "execute_trade",
    "place_order",
    "cancel_order",
    "modify_order",
    "route_order",
    
    # Customer management
    "open_account",
    "close_account",
    "update_account",
    "verify_customer",
    "screen_customer",
    
    # Compliance and reporting
    "report_transaction",
    "file_suspicious_activity",
    "audit_trail",
    "supervise_activity",
    "review_communication",
    
    # Financial operations
    "process_settlement",
    "clear_transaction",
    "custody_assets",
    "lend_margin",
    "calculate_commissions",
}

# Actions where FINRA likely doesn't apply (future-proof exclusions)
NON_FINRA_ACTIONS: Set[str] = {
    # Non-financial actions
    "login",
    "logout",
    "view_content",
    "download_file",
    "print_document",
    
    # Simple data operations
    "store_data",
    "retrieve_data",
    "delete_data",
    "list_records",
    
    # System management
    "system_backup",
    "update_software",
    "monitor_performance",
    "generate_report",
}

# ============================================================
# ENFORCEMENT SCOPE RESOLUTION (FUTURE-PROOF)
# ============================================================

def _normalize_article(article: str) -> str:
    """
    Normalize FINRA rule identifier for consistent comparison.
    
    Future-proof examples:
        "FINRA Rule 3110" → "3110"
        "Rule 4511(c)" → "4511"
        "FINRA 4370" → "4370"
        "SEC Rule 17a-4" → "17A4"
        "Regulation SHO" → "REGSHO"
    """
    if not article:
        return ""
    
    article = article.upper().strip()
    
    # Remove common prefixes
    article = article.replace("FINRA ", "").replace("RULE ", "").replace("SEC ", "")
    
    # Extract rule number (digits only, handle letters like "3110(b)")
    import re
    match = re.match(r"(\d+)[A-Z]?", article)
    if match:
        return match.group(1)
    
    # For SEC rules (e.g., "17a-4")
    match = re.search(r"(\d+)[A-Z]?[-]?(\d+)", article)
    if match:
        return f"{match.group(1)}A{match.group(2)}"
    
    # For regulations (e.g., "Regulation SHO")
    if "REGULATION" in article:
        # Extract regulation name
        reg_match = re.search(r"REGULATION\s+([A-Z]+)", article)
        if reg_match:
            return f"REG{reg_match.group(1)}"
    
    # Return cleaned string for non-standard rules
    return article.replace(" ", "_").replace("-", "")


def _get_finra_base_enforcement_scope(article: str) -> str:
    """
    Get base enforcement scope from governance catalog.
    
    Future-proof FINRA Classification:
    - ALL rules are TRANSACTION scope (financial compliance is strict)
    - No PLATFORM_AUDIT obligations in FINRA (all per-transaction)
    - Some supervisory rules may be PLATFORM_AUDIT but still enforce per-transaction
    
    Returns: "TRANSACTION" | "PLATFORM_AUDIT" | "SUPERVISORY"
    Default: "TRANSACTION" (safe - financial rules block violations)
    """
    article_normalized = _normalize_article(article)
    
    for regime in _GOVERNANCE_CATALOG.get("regimes", []):
        if regime.get("id") == FINRA_REGIME_ID:
            for domain in regime.get("domains", []):
                for art_def in domain.get("articles", []):
                    art_num = _normalize_article(art_def.get("article", ""))
                    if art_num == article_normalized:
                        return art_def.get("enforcement_scope", "TRANSACTION")
    
    # SAFE DEFAULT: TRANSACTION (financial rules block)
    # This is correct for FINRA - all obligations are transactional
    return "TRANSACTION"


def _detect_broker_dealer(payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Future-proof broker-dealer detection with comprehensive verification.
    
    Returns:
        (is_broker_dealer, detection_evidence)
    """
    detection_evidence = {
        "methods_used": [],
        "indicators_found": [],
        "confidence": "LOW",
    }
    
    profile = payload.get("finra_profile", {})
    meta = payload.get("meta", {})
    
    # Method 1: Explicit broker-dealer flag (most reliable)
    if profile.get("broker_dealer"):
        detection_evidence["methods_used"].append("EXPLICIT_FLAG")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["indicators_found"].append("explicit_bd_flag")
        return True, detection_evidence
    
    # Method 2: Registration status
    reg_status = str(profile.get("registration_status", "")).upper().strip()
    if reg_status in BROKER_DEALER_REGISTRATION_STATUSES:
        detection_evidence["methods_used"].append("REGISTRATION_STATUS")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["indicators_found"].append(f"registration_status:{reg_status}")
        return True, detection_evidence
    
    # Method 3: FINRA CRD number (Central Registration Depository)
    if profile.get("crd_number"):
        detection_evidence["methods_used"].append("CRD_NUMBER")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["indicators_found"].append("crd_number_present")
        return True, detection_evidence
    
    # Method 4: SEC registration as broker-dealer
    sec_registration = str(profile.get("sec_registration", "")).upper().strip()
    if "BROKER-DEALER" in sec_registration or "BD" == sec_registration:
        detection_evidence["methods_used"].append("SEC_REGISTRATION")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["indicators_found"].append(f"sec_registration:{sec_registration}")
        return True, detection_evidence
    
    # Method 5: Industry + activity context
    industry = str(payload.get("industry_id", "")).upper().strip()
    action = str(payload.get("action", "")).lower().strip()
    
    if industry in BROKER_DEALER_INDUSTRIES and action in BROKER_DEALER_ACTIVITIES:
        detection_evidence["methods_used"].append("CONTEXTUAL")
        detection_evidence["confidence"] = "MEDIUM"
        detection_evidence["indicators_found"].append(f"industry:{industry}")
        detection_evidence["indicators_found"].append(f"action:{action}")
        # Strong indicator but not definitive
        detection_evidence["confidence"] = "MEDIUM"
        return True, detection_evidence
    
    # Method 6: Meta/platform signals
    platform_type = str(meta.get("platform_type", "")).lower()
    if any(bd_term in platform_type for bd_term in ["brokerage", "trading", "securities", "investment"]):
        detection_evidence["methods_used"].append("PLATFORM_SIGNAL")
        detection_evidence["confidence"] = "MEDIUM"
        detection_evidence["indicators_found"].append(f"platform_type:{platform_type}")
        return True, detection_evidence
    
    # No broker-dealer detected
    return False, detection_evidence


def _should_evaluate_finra(payload: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Future-proof decision: Should FINRA evaluation run for this payload?
    
    Returns:
        (should_evaluate, evaluation_reason, context_evidence)
    """
    context_evidence = {
        "broker_dealer_detection": {},
        "jurisdiction_check": {},
        "context_checks": {},
    }
    
    # Check 1: Broker-dealer detection
    is_bd, bd_evidence = _detect_broker_dealer(payload)
    context_evidence["broker_dealer_detection"] = bd_evidence
    
    if not is_bd:
        return False, "NOT_BROKER_DEALER", context_evidence
    
    # Check 2: Jurisdiction
    meta = payload.get("meta", {})
    jurisdiction = str(meta.get("jurisdiction", "")).upper().strip()
    context_evidence["jurisdiction_check"]["jurisdiction"] = jurisdiction
    
    if jurisdiction not in FINRA_JURISDICTIONS:
        return False, f"JURISDICTION_OUTSIDE_US: {jurisdiction}", context_evidence
    
    # Check 3: Action relevance
    action = str(payload.get("action", "")).lower().strip()
    context_evidence["context_checks"]["action"] = action
    
    if action in NON_FINRA_ACTIONS:
        return False, f"ACTION_EXCLUDED: {action}", context_evidence
    
    # Check 4: Industry relevance
    industry = str(payload.get("industry_id", "")).upper().strip()
    context_evidence["context_checks"]["industry"] = industry
    
    if industry not in BROKER_DEALER_INDUSTRIES:
        # Not a typical broker-dealer industry, but might still be relevant
        # We'll evaluate anyway but note the industry
        pass
    
    # All checks passed - evaluate FINRA
    return True, "EVALUATE_FINRA", context_evidence


def _resolve_enforcement_scope(article: str, payload: Dict[str, Any]) -> str:
    """
    Resolve final enforcement scope with future-proof modifiers.
    
    FINRA enforcement scope modifiers:
    1. Base scope from catalog (usually TRANSACTION)
    2. Action-specific considerations
    3. Risk level modifiers
    
    Returns:
        Final enforcement scope after applying modifiers
    """
    base_scope = _get_finra_base_enforcement_scope(article)
    article_num = _normalize_article(article)
    
    # Extract context for potential modifiers
    action = str(payload.get("action", "")).lower().strip()
    profile = payload.get("finra_profile", {})
    
    # MODIFIER: Trading actions with high risk always TRANSACTION
    if base_scope == "PLATFORM_AUDIT" and action in {"execute_trade", "place_order", "route_order"}:
        # Trading actions need immediate enforcement
        return "TRANSACTION"
    
    # MODIFIER: Customer protection rules always TRANSACTION
    customer_protection_rules = {"2090", "2111", "4512"}
    if article_num in customer_protection_rules:
        # Customer protection rules block per-transaction
        return "TRANSACTION"
    
    # MODIFIER: High-risk financial activities
    if profile.get("high_risk_activity") and base_scope == "PLATFORM_AUDIT":
        # High-risk activities need immediate enforcement
        return "TRANSACTION"
    
    # No modifiers applied - return base scope
    return base_scope


# ============================================================
# EVIDENCE COLLECTION (Enhanced for Future-Proofing)
# ============================================================

def _collect_finra_evidence(payload: Dict[str, Any], rule_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect comprehensive FINRA evidence for audit trails.
    
    Returns:
        Structured evidence with context, rule data, and metadata
    """
    evidence = {
        # Context evidence
        "context": {
            "industry_id": payload.get("industry_id"),
            "action": payload.get("action"),
            "jurisdiction": (payload.get("meta") or {}).get("jurisdiction"),
            "broker_dealer_detected": True,  # We only evaluate if BD detected
        },
        # Rule-specific evidence
        "rule_data": rule_data,
        # Broker-dealer verification
        "broker_dealer_info": {},
        # Metadata
        "metadata": {
            "evidence_collected_at": "NOW",  # Would be timestamp in real implementation
        }
    }
    
    # Collect broker-dealer information
    profile = payload.get("finra_profile", {})
    evidence["broker_dealer_info"] = {
        "crd_number": profile.get("crd_number"),
        "registration_status": profile.get("registration_status"),
        "firm_name": profile.get("firm_name"),
        "sec_registration": profile.get("sec_registration"),
    }
    
    return evidence


# ============================================================
# FINRA RULE DEFINITIONS (Enhanced with Future Rules)
# ============================================================

# Core FINRA rules with comprehensive metadata
FINRA_RULES = [
    {
        "article": "FINRA Rule 3110",
        "title": "Supervision",
        "description": "Firms must establish and maintain a system to supervise the activities of each associated person.",
        "field": "supervision_program",
        "severity": "HIGH",
        "future_proof_notes": "Written supervisory procedures (WSPs) required. Includes review of correspondence.",
        "evidence_fields": ["finra_profile.supervision_program", "finra_profile.written_procedures"],
    },
    {
        "article": "FINRA Rule 4511",
        "title": "Books and Records",
        "description": "Member firms must create and preserve books and records as required by SEC rules.",
        "field": "records_retained",
        "severity": "HIGH",
        "future_proof_notes": "Tied to SEC Rule 17a-3/17a-4. Must retain for 6+ years.",
        "evidence_fields": ["finra_profile.records_retained", "finra_profile.retention_period"],
    },
    {
        "article": "FINRA Rule 4370",
        "title": "Business Continuity Planning",
        "description": "Firms must create and maintain a business continuity plan (BCP) with emergency contact information.",
        "field": "business_continuity_plan",
        "severity": "MEDIUM",
        "future_proof_notes": "BCP must be reviewed annually and updated as needed.",
        "evidence_fields": ["finra_profile.business_continuity_plan", "finra_profile.bcp_tested"],
    },
    {
        "article": "FINRA Rule 4512",
        "title": "Customer Account Information",
        "description": "Firms must maintain accurate and current customer account information.",
        "field": "customer_records",
        "severity": "MEDIUM",
        "future_proof_notes": "Must include tax ID, investment objectives, and employment information.",
        "evidence_fields": ["finra_profile.customer_records", "finra_profile.account_information_current"],
    },
    {
        "article": "FINRA Rule 2090",
        "title": "Know Your Customer (KYC)",
        "description": "Firms must use reasonable diligence to know the essential facts about each customer.",
        "field": "kyc_program",
        "severity": "HIGH",
        "future_proof_notes": "Part of AML program requirements. Must verify identity and assess risk.",
        "evidence_fields": ["finra_profile.kyc_program", "finra_profile.customer_identification"],
        "future_implementation": True,
    },
    {
        "article": "FINRA Rule 2111",
        "title": "Suitability",
        "description": "Firms must have a reasonable basis to believe a recommended transaction is suitable for the customer.",
        "field": "suitability_assessment",
        "severity": "HIGH",
        "future_proof_notes": "Must consider customer's investment profile: age, financial situation, risk tolerance.",
        "evidence_fields": ["finra_profile.suitability_assessment", "finra_profile.investment_profile"],
        "future_implementation": True,
    },
    {
        "article": "SEC Rule 17a-4",
        "title": "Electronic Recordkeeping",
        "description": "SEC rule requiring preservation of electronic records in non-rewriteable format.",
        "field": "electronic_records_compliant",
        "severity": "HIGH",
        "future_proof_notes": "WORM (Write Once Read Many) requirement for electronic storage.",
        "evidence_fields": ["finra_profile.electronic_records_compliant", "finra_profile.worm_compliant"],
        "future_implementation": True,
    },
    {
        "article": "FINRA Rule 2241",
        "title": "Research Analysts",
        "description": "Conflict of interest rules for research analysts and research reports.",
        "field": "research_analyst_compliance",
        "severity": "MEDIUM",
        "future_proof_notes": "Includes quiet periods, compensation disclosure, and supervisory procedures.",
        "evidence_fields": ["finra_profile.research_analyst_compliance"],
        "future_implementation": True,
    },
]


# ============================================================
# MAIN EVALUATION FUNCTION (Future-Proof Architecture)
# ============================================================

def evaluate_finra_rules(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Future-proof FINRA evaluation with comprehensive context gating.
    
    Features:
    1. Multi-method broker-dealer detection
    2. Jurisdiction and action filtering
    3. Industry-aware applicability
    4. Enhanced enforcement scope resolution
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
    should_evaluate, evaluation_reason, context_evidence = _should_evaluate_finra(payload)
    
    if not should_evaluate:
        # FINRA doesn't apply to this context - return early with explanation
        summary = {
            "total_rules": 0,
            "passed": 0,
            "failed": 0,
            "blocking_failures": 0,
            "regime": "FINRA",
            "context_gated": True,
            "evaluation_decision": evaluation_reason,
            "context_evidence": context_evidence,
            "notes": f"FINRA evaluation skipped: {evaluation_reason}"
        }
        return policies, summary
    
    # ============================================================
    # RULE EVALUATION (Enhanced with Evidence Collection)
    # ============================================================
    
    evaluation_errors = []
    profile = payload.get("finra_profile") or {}
    
    for rule_def in FINRA_RULES:
        # Skip future implementation rules if not ready
        if rule_def.get("future_implementation") and not profile.get("enable_future_rules"):
            continue
        
        try:
            # Check if the required field exists and is compliant
            field_value = profile.get(rule_def["field"])
            violated = field_value is False  # Explicit False is violation
            
            # Default to SATISFIED if field is missing (conservative)
            if field_value is None:
                violated = False
            
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
            
            # Create policy
            policy = {
                "domain": "FINRA Rules",
                "regime": "FINRA",
                "framework": FINRA_FRAMEWORK,
                "domain_id": "FINRA",
                "article": rule_def["article"],
                "category": rule_def["title"],
                "title": rule_def["title"],
                "status": "VIOLATED" if violated else "SATISFIED",
                "severity": rule_def["severity"] if violated else "LOW",
                "impact_on_verdict": "BLOCKING_FAILURE" if violated and rule_def["severity"] in {"HIGH", "CRITICAL"} else "NON_BLOCKING",
                "trigger_type": "FINRA_RULE",
                "rule_ids": [rule_def["article"]],
                "enforcement_scope": enforcement_scope,
                "notes": rule_def["description"],
                "evidence": _collect_finra_evidence(payload, rule_evidence),
                "remediation": (
                    f"Implement {rule_def['title']} controls per FINRA requirements. "
                    "Document procedures and re-run GNCE after remediation."
                    if violated else "No remediation required."
                ),
                "violation_detail": rule_def["description"] if violated else "",
                "control_severity": rule_def["severity"] if violated else "LOW",
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
    context_info = {
        "industry": payload.get("industry_id"),
        "action": payload.get("action"),
        "jurisdiction": (payload.get("meta") or {}).get("jurisdiction"),
        "broker_dealer_verified": True,
        "finra_profile_exists": bool(payload.get("finra_profile")),
    }
    
    summary = {
        "total_rules": len(policies),
        "passed": passed,
        "failed": failed,
        "blocking_failures": blocking,
        "regime": "FINRA",
        "context_gated": False,
        "evaluation_decision": evaluation_reason,
        "broker_dealer_status": "REGISTERED",
        # Scope-specific violation counts
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
        # Rule statistics
        "core_rules_evaluated": len([r for r in FINRA_RULES if not r.get("future_implementation")]),
        "future_rules_available": len([r for r in FINRA_RULES if r.get("future_implementation")]),
        "future_rules_evaluated": len([r for r in FINRA_RULES if r.get("future_implementation") and profile.get("enable_future_rules")]),
        # Error tracking
        "evaluation_errors": evaluation_errors if evaluation_errors else None,
    }
    
    return policies, summary