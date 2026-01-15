# gnce/gn_kernel/rules/nydfs_500_rules.py
"""
NYDFS Cybersecurity Regulation 23 NYCRR 500 Evaluator with Constitutional Binding (v0.7.2-RC-FUTUREPROOF)

CRITICAL UPDATES FOR FUTURE-PROOFING:
1. Comprehensive financial institution detection with multi-method verification
2. NYDFS institution classification with tiered requirements (Class A, B, C, Limited Exemptions)
3. Cybersecurity program requirements with evidence-based assessment
4. 72-hour breach notification with escalation triggers
5. Enhanced enforcement scope resolution with risk-aware escalation
6. Cross-framework alignment with NYDFS updates and federal regulations
7. Comprehensive evidence collection for audit trails
8. Cross-domain safety (won't misfire on non-NY financial institutions)
9. Future NYDFS amendments ready for implementation

NYDFS 500 Reality (Future-Proof):
- 23 NYCRR Part 500: Cybersecurity Requirements for Financial Services Companies
- Covers banks, insurance companies, financial services providers in New York
- Tiered requirements based on institution size and complexity
- 72-hour breach notification requirement
- Annual certification to NYDFS Superintendent
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple, Set, Optional
import re

# Load governance catalog for enforcement scope classification
from gnce.gn_kernel.constitution.constitution_catalog import load_governance_catalog_v05

# ============================================================
# MODULE CONSTANTS (FUTURE-PROOF)
# ============================================================

NYDFS_DOMAIN = "New York Department of Financial Services Cybersecurity (23 NYCRR 500)"
NYDFS_FRAMEWORK = "Financial Services Cybersecurity"
NYDFS_REGIME_ID = "NYDFS_500"

# Load catalog once at module level (performance)
_GOVERNANCE_CATALOG = load_governance_catalog_v05()

# ============================================================
# FINANCIAL INSTITUTION DETECTION (FUTURE-PROOF)
# ============================================================

# NYDFS-covered entity types
NYDFS_ENTITY_TYPES: Set[str] = {
    "BANK",
    "TRUST_COMPANY",
    "PRIVATE_BANKER",
    "SAVINGS_BANK",
    "SAVINGS_AND_LOAN_ASSOCIATION",
    "CREDIT_UNION",
    "INVESTMENT_COMPANY",
    "INSURANCE_COMPANY",
    "LIFE_INSURANCE_COMPANY",
    "PROPERTY_CASUALTY_INSURANCE_COMPANY",
    "HEALTH_INSURANCE_COMPANY",
    "REINSURANCE_COMPANY",
    "MORTGAGE_BANKER",
    "MORTGAGE_BROKER",
    "MONEY_TRANSMITTER",
    "CHECK_CASHER",
    "VIRTUAL_CURRENCY_BUSINESS",
    "CREDIT_REPORTING_AGENCY",
    "DEBT_COLLECTOR",
    "FINTECH",
}

# Financial services actions where NYDFS applies
NYDFS_FINANCIAL_ACTIONS: Set[str] = {
    "process_transaction",
    "transfer_funds",
    "open_account",
    "close_account",
    "issue_policy",
    "process_claim",
    "underwrite_risk",
    "manage_investment",
    "execute_trade",
    "clear_settlement",
    "verify_identity",
    "screen_transaction",
    "report_suspicious_activity",
    "file_regulatory_report",
    "conduct_kyc",
    "perform_aml_check",
    "manage_customer_data",
    "access_financial_records",
    "process_payment",
    "issue_loan",
}

# NYDFS jurisdiction (must be New York)
NYDFS_JURISDICTIONS: Set[str] = {
    "US-NY",
    "NEW_YORK",
    "NY",
    "US-NYC",  # New York City
    "US-NYS",  # New York State
}

# NYDFS institution classification (tiered requirements)
NYDFS_INSTITUTION_CLASSES = {
    "CLASS_A": {
        "description": "Large, complex institutions with significant resources and risk",
        "requirements": ["FULL_COMPLIANCE", "ANNUAL_CERTIFICATION", "INDEPENDENT_AUDIT"],
        "employee_threshold": 1000,
        "asset_threshold": 1000000000,  # $1B
        "revenue_threshold": 500000000,  # $500M
    },
    "CLASS_B": {
        "description": "Medium-sized institutions with moderate resources and risk",
        "requirements": ["FULL_COMPLIANCE", "ANNUAL_CERTIFICATION"],
        "employee_threshold": 100,
        "asset_threshold": 10000000,  # $10M
        "revenue_threshold": 5000000,  # $5M
    },
    "CLASS_C": {
        "description": "Small institutions with limited resources",
        "requirements": ["SCALED_COMPLIANCE", "ANNUAL_CERTIFICATION"],
        "employee_threshold": 10,
        "asset_threshold": 1000000,  # $1M
        "revenue_threshold": 500000,  # $500K
    },
    "LIMITED_EXEMPTION": {
        "description": "Entities qualifying for limited exemptions",
        "requirements": ["MINIMAL_COMPLIANCE"],
        "employee_threshold": 10,
        "asset_threshold": 5000000,  # $5M
        "revenue_threshold": 1000000,  # $1M
    },
}

# NYDFS 500 Cybersecurity Program Required Elements
NYDFS_REQUIRED_ELEMENTS = {
    "CYBERSECURITY_PROGRAM": {
        "section": "500.02",
        "description": "Comprehensive written cybersecurity program",
        "evidence_fields": ["nydfs_profile.cybersecurity_program", "nydfs_profile.program_documentation"],
    },
    "CYBERSECURITY_POLICY": {
        "section": "500.03",
        "description": "Written cybersecurity policy approved by board/senior officer",
        "evidence_fields": ["nydfs_profile.cybersecurity_policy", "nydfs_profile.policy_approval_date"],
    },
    "CHIEF_INFORMATION_SECURITY_OFFICER": {
        "section": "500.04",
        "description": "Designated CISO or qualified provider",
        "evidence_fields": ["nydfs_profile.ciso_appointed", "nydfs_profile.ciso_qualifications"],
    },
    "PENETRATION_TESTING": {
        "section": "500.05",
        "description": "Annual penetration testing and bi-annual vulnerability assessments",
        "evidence_fields": ["nydfs_profile.penetration_testing", "nydfs_profile.last_pen_test_date"],
    },
    "AUDIT_TRAIL": {
        "section": "500.06",
        "description": "Comprehensive audit trail system",
        "evidence_fields": ["nydfs_profile.audit_trail", "nydfs_profile.audit_log_retention"],
    },
    "ACCESS_CONTROLS": {
        "section": "500.07",
        "description": "Access privileges and periodic review",
        "evidence_fields": ["nydfs_profile.access_controls", "nydfs_profile.access_review_frequency"],
    },
    "APPLICATION_SECURITY": {
        "section": "500.08",
        "description": "Secure application development practices",
        "evidence_fields": ["nydfs_profile.application_security", "nydfs_profile.secure_sdlc"],
    },
    "RISK_ASSESSMENT": {
        "section": "500.09",
        "description": "Periodic risk assessment",
        "evidence_fields": ["nydfs_profile.risk_assessment", "nydfs_profile.last_risk_assessment"],
    },
    "CYBERSECURITY_PERSONNEL": {
        "section": "500.10",
        "description": "Qualified cybersecurity personnel",
        "evidence_fields": ["nydfs_profile.cybersecurity_personnel", "nydfs_profile.security_training"],
    },
    "THIRD_PARTY_SECURITY": {
        "section": "500.11",
        "description": "Third-party service provider security policy",
        "evidence_fields": ["nydfs_profile.third_party_security", "nydfs_profile.vendor_assessments"],
    },
    "MULTI_FACTOR_AUTHENTICATION": {
        "section": "500.12",
        "description": "MFA for remote access and privileged accounts",
        "evidence_fields": ["nydfs_profile.multi_factor_authentication", "nydfs_profile.mfa_implementation"],
    },
    "DATA_RETENTION": {
        "section": "500.13",
        "description": "Limitations on data retention",
        "evidence_fields": ["nydfs_profile.data_retention_limits", "nydfs_profile.retention_policies"],
    },
    "TRAINING_MONITORING": {
        "section": "500.14",
        "description": "Training and monitoring for authorized users",
        "evidence_fields": ["nydfs_profile.training_monitoring", "nydfs_profile.security_awareness_training"],
    },
    "ENCRYPTION": {
        "section": "500.15",
        "description": "Encryption of nonpublic information",
        "evidence_fields": ["nydfs_profile.data_encryption", "nydfs_profile.encryption_standards"],
    },
    "INCIDENT_RESPONSE": {
        "section": "500.16",
        "description": "Incident response plan",
        "evidence_fields": ["nydfs_profile.incident_response", "nydfs_profile.irp_testing"],
    },
    "BREACH_NOTIFICATION": {
        "section": "500.17",
        "description": "72-hour breach notification",
        "evidence_fields": ["nydfs_profile.breach_notification_procedures", "nydfs_profile.last_notification_drill"],
    },
}

# Actions where NYDFS likely doesn't apply
NON_NYDFS_ACTIONS: Set[str] = {
    "login",
    "logout",
    "view_dashboard",
    "generate_report",
    "system_backup",
    "update_software",
    "monitor_performance",
    "audit_logs",
    "manual_review",
    "human_decision",
}

# ============================================================
# FINANCIAL INSTITUTION DETECTION (FUTURE-PROOF)
# ============================================================

def _detect_nydfs_entity(payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Future-proof NYDFS entity detection with comprehensive verification.
    
    Returns:
        (is_nydfs_entity, detection_evidence)
    """
    detection_evidence = {
        "methods_used": [],
        "indicators_found": [],
        "confidence": "LOW",
    }
    
    # Method 1: Explicit NYDFS flags
    if payload.get("is_nydfs_covered") or payload.get("nydfs_regulated"):
        detection_evidence["methods_used"].append("EXPLICIT_FLAG")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["indicators_found"].append("explicit_nydfs_flag")
        return True, detection_evidence
    
    # Method 2: Entity type classification
    entity_type = str(payload.get("entity_type", "")).upper()
    if entity_type in NYDFS_ENTITY_TYPES:
        detection_evidence["methods_used"].append("ENTITY_TYPE")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["indicators_found"].append(f"entity_type:{entity_type}")
        return True, detection_evidence
    
    # Method 3: Industry classification
    industry = str(payload.get("industry_id", "")).upper()
    if industry in NYDFS_ENTITY_TYPES:
        detection_evidence["methods_used"].append("INDUSTRY_CLASSIFICATION")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["indicators_found"].append(f"industry:{industry}")
        return True, detection_evidence
    
    # Method 4: NYDFS profile detection
    nydfs_profile = payload.get("nydfs_profile", {})
    if nydfs_profile and nydfs_profile.get("covered_institution"):
        detection_evidence["methods_used"].append("NYDFS_PROFILE")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["indicators_found"].append("covered_institution_flag")
        return True, detection_evidence
    
    # Method 5: Action classification
    action = str(payload.get("action", "")).lower()
    if action in NYDFS_FINANCIAL_ACTIONS:
        detection_evidence["methods_used"].append("ACTION_CLASSIFICATION")
        detection_evidence["confidence"] = "MEDIUM"
        detection_evidence["indicators_found"].append(f"action:{action}")
        
        # Check jurisdiction for confirmation
        jurisdiction = str(payload.get("meta", {}).get("jurisdiction", "")).upper()
        if any(ny_jurisdiction in jurisdiction for ny_jurisdiction in NYDFS_JURISDICTIONS):
            detection_evidence["confidence"] = "HIGH"
            return True, detection_evidence
    
    # Method 6: Regulatory registrations
    registrations = payload.get("regulatory_registrations", [])
    if isinstance(registrations, list):
        nydfs_registrations = [reg for reg in registrations 
                              if any(ny_term in str(reg).upper() for ny_term in ["NYDFS", "NYCRR", "NEW_YORK_BANKING", "NY_INSURANCE"])]
        if nydfs_registrations:
            detection_evidence["methods_used"].append("REGULATORY_REGISTRATION")
            detection_evidence["confidence"] = "HIGH"
            detection_evidence["indicators_found"].extend([f"registration:{r}" for r in nydfs_registrations[:3]])
            return True, detection_evidence
    
    return False, detection_evidence


def _classify_nydfs_institution(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Classify NYDFS institution based on size, complexity, and risk.
    
    Returns:
        (institution_class, classification_evidence)
        institution_class: "CLASS_A", "CLASS_B", "CLASS_C", "LIMITED_EXEMPTION", "UNKNOWN"
    """
    classification_evidence = {
        "factors_considered": [],
        "institution_class": "UNKNOWN",
        "confidence": "LOW",
    }
    
    nydfs_profile = payload.get("nydfs_profile", {})
    meta = payload.get("meta", {})
    
    # Factor 1: Explicit classification
    explicit_class = str(nydfs_profile.get("institution_class", "")).upper()
    if explicit_class in NYDFS_INSTITUTION_CLASSES:
        classification_evidence["factors_considered"].append("EXPLICIT_CLASSIFICATION")
        classification_evidence["institution_class"] = explicit_class
        classification_evidence["confidence"] = "HIGH"
        return explicit_class, classification_evidence
    
    # Factor 2: Size-based classification
    employee_count = nydfs_profile.get("employee_count", 0)
    total_assets = nydfs_profile.get("total_assets", 0)
    annual_revenue = nydfs_profile.get("annual_revenue", 0)
    
    classification_evidence["factors_considered"].extend([
        f"employees:{employee_count}",
        f"assets:{total_assets}",
        f"revenue:{annual_revenue}",
    ])
    
    # Check Class A thresholds
    class_a = NYDFS_INSTITUTION_CLASSES["CLASS_A"]
    if (employee_count >= class_a["employee_threshold"] or
        total_assets >= class_a["asset_threshold"] or
        annual_revenue >= class_a["revenue_threshold"]):
        classification_evidence["institution_class"] = "CLASS_A"
        classification_evidence["confidence"] = "HIGH"
        return "CLASS_A", classification_evidence
    
    # Check Class B thresholds
    class_b = NYDFS_INSTITUTION_CLASSES["CLASS_B"]
    if (employee_count >= class_b["employee_threshold"] or
        total_assets >= class_b["asset_threshold"] or
        annual_revenue >= class_b["revenue_threshold"]):
        classification_evidence["institution_class"] = "CLASS_B"
        classification_evidence["confidence"] = "MEDIUM"
        return "CLASS_B", classification_evidence
    
    # Check Class C thresholds
    class_c = NYDFS_INSTITUTION_CLASSES["CLASS_C"]
    if (employee_count >= class_c["employee_threshold"] or
        total_assets >= class_c["asset_threshold"] or
        annual_revenue >= class_c["revenue_threshold"]):
        classification_evidence["institution_class"] = "CLASS_C"
        classification_evidence["confidence"] = "MEDIUM"
        return "CLASS_C", classification_evidence
    
    # Factor 3: Complexity indicators
    complexity_indicators = [
        nydfs_profile.get("international_operations"),
        nydfs_profile.get("multiple_business_lines"),
        nydfs_profile.get("significant_third_party_exposure"),
        nydfs_profile.get("high_risk_activities"),
    ]
    
    if any(complexity_indicators):
        classification_evidence["factors_considered"].append("COMPLEXITY_INDICATORS")
        classification_evidence["institution_class"] = "CLASS_B"  # Default to higher class for complexity
        classification_evidence["confidence"] = "LOW"
        return "CLASS_B", classification_evidence
    
    # Factor 4: Limited exemption check
    exemption_indicators = [
        employee_count < 10,
        total_assets < 5000000,
        annual_revenue < 1000000,
        nydfs_profile.get("qualifies_for_limited_exemption"),
    ]
    
    if all(exemption_indicators):
        classification_evidence["factors_considered"].append("LIMITED_EXEMPTION_INDICATORS")
        classification_evidence["institution_class"] = "LIMITED_EXEMPTION"
        classification_evidence["confidence"] = "MEDIUM"
        return "LIMITED_EXEMPTION", classification_evidence
    
    # Default: CLASS_C (conservative)
    classification_evidence["institution_class"] = "CLASS_C"
    classification_evidence["confidence"] = "LOW"
    return "CLASS_C", classification_evidence


def _assess_cybersecurity_program(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Assess NYDFS cybersecurity program requirements.
    
    Returns:
        (requirement_scores, assessment_evidence)
    """
    assessment_evidence = {
        "requirements_assessed": [],
        "methods_used": [],
        "confidence": "LOW",
    }
    
    nydfs_profile = payload.get("nydfs_profile", {})
    
    requirement_scores = {}
    
    for element_id, element_info in NYDFS_REQUIRED_ELEMENTS.items():
        score = 0
        max_score = len(element_info["evidence_fields"])
        
        for evidence_field in element_info["evidence_fields"]:
            if "." in evidence_field:
                parts = evidence_field.split(".")
                obj = payload
                for part in parts[:-1]:
                    obj = obj.get(part, {})
                value = obj.get(parts[-1])
            else:
                value = payload.get(evidence_field)
            
            if value is True or (isinstance(value, str) and value.strip()):
                score += 1
        
        # Normalize score to 0-100
        normalized_score = (score / max_score) * 100 if max_score > 0 else 0
        requirement_scores[element_id] = normalized_score
        
        assessment_evidence["requirements_assessed"].append({
            "requirement": element_id,
            "section": element_info["section"],
            "score": normalized_score,
            "evidence_fields": element_info["evidence_fields"],
        })
    
    assessment_evidence["methods_used"].append("EVIDENCE_BASED_SCORING")
    assessment_evidence["confidence"] = "MEDIUM"
    
    return requirement_scores, assessment_evidence


def _should_evaluate_nydfs_500(payload: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Future-proof decision: Should NYDFS 500 evaluation run for this payload?
    
    Returns:
        (should_evaluate, evaluation_reason, context_evidence)
    """
    context_evidence = {
        "nydfs_entity_detection": {},
        "institution_classification": {},
        "cybersecurity_program_assessment": {},
        "jurisdiction_check": {},
        "context_checks": {},
    }
    
    # Check 1: NYDFS entity detection
    is_nydfs_entity, entity_evidence = _detect_nydfs_entity(payload)
    context_evidence["nydfs_entity_detection"] = entity_evidence
    
    if not is_nydfs_entity:
        return False, "NOT_NYDFS_ENTITY", context_evidence
    
    # Check 2: Jurisdiction verification
    meta = payload.get("meta", {})
    jurisdiction = str(meta.get("jurisdiction", "")).upper()
    context_evidence["jurisdiction_check"]["jurisdiction"] = jurisdiction
    
    if not any(ny_jurisdiction in jurisdiction for ny_jurisdiction in NYDFS_JURISDICTIONS):
        return False, f"JURISDICTION_OUTSIDE_NY: {jurisdiction}", context_evidence
    
    # Check 3: Action relevance
    action = str(payload.get("action", "")).lower().strip()
    context_evidence["context_checks"]["action"] = action
    
    if action in NON_NYDFS_ACTIONS:
        return False, f"ACTION_EXCLUDED: {action}", context_evidence
    
    # Check 4: Institution classification
    institution_class, class_evidence = _classify_nydfs_institution(payload)
    context_evidence["institution_classification"] = class_evidence
    
    # Check 5: Cybersecurity program assessment
    program_scores, program_evidence = _assess_cybersecurity_program(payload)
    context_evidence["cybersecurity_program_assessment"] = program_evidence
    
    # All checks passed - evaluate NYDFS 500
    return True, f"EVALUATE_NYDFS_CLASS:{institution_class}", context_evidence


# ============================================================
# ENFORCEMENT SCOPE RESOLUTION (FUTURE-PROOF)
# ============================================================

def _normalize_nydfs_article(article: str) -> str:
    """
    Normalize NYDFS article identifier for consistent comparison.
    
    Future-proof examples:
        "23 NYCRR 500.02" → "500.02"
        "500.07" → "500.07"
        "NYDFS 500.16" → "500.16"
        "Part 500.12" → "500.12"
    """
    if not article:
        return ""
    
    article = article.strip()
    
    # Extract 500.XX pattern with optional letter
    import re
    match = re.search(r'500\.\d+[a-z]?', article)
    if match:
        return match.group(0)
    
    # For non-standard references
    if "APPLICABILITY" in article.upper():
        return "APPLICABILITY"
    elif "ANNUAL_CERTIFICATION" in article.upper():
        return "ANNUAL_CERTIFICATION"
    
    # Return cleaned version
    return re.sub(r'[^\d\.]', '', article)


def _get_nydfs_base_enforcement_scope(article: str) -> str:
    """
    Get base enforcement scope from governance catalog.
    
    Future-proof NYDFS Classification:
    - Program requirements: GOVERNANCE (organizational)
    - Technical controls: TRANSACTION (immediate enforcement)
    - Testing requirements: PLATFORM_AUDIT (periodic)
    - Reporting requirements: SUPERVISORY (regulatory)
    
    Returns: "TRANSACTION" | "PLATFORM_AUDIT" | "GOVERNANCE" | "CYBERSECURITY" | "SUPERVISORY"
    Default: "PLATFORM_AUDIT" (safe - logs but doesn't block unknown articles)
    """
    article_normalized = _normalize_nydfs_article(article)
    
    # First check catalog for NYDFS regime
    for regime in _GOVERNANCE_CATALOG.get("regimes", []):
        if regime.get("id") == NYDFS_REGIME_ID:
            for domain in regime.get("domains", []):
                for art_def in domain.get("articles", []):
                    if art_def.get("article", "") == article_normalized:
                        return art_def.get("enforcement_scope", "PLATFORM_AUDIT")
    
    # Local mapping based on requirement type
    nydfs_scopes = {
        # Cybersecurity Program (Governance)
        "500.02": "GOVERNANCE",  # Cybersecurity program
        "500.03": "GOVERNANCE",  # Cybersecurity policy
        "500.04": "GOVERNANCE",  # CISO
        
        # Testing and Assessment (Platform Audit)
        "500.05": "PLATFORM_AUDIT",  # Penetration testing
        "500.09": "PLATFORM_AUDIT",  # Risk assessment
        "500.16": "PLATFORM_AUDIT",  # Incident response testing
        
        # Technical Controls (Transaction)
        "500.06": "TRANSACTION",  # Audit trail
        "500.07": "TRANSACTION",  # Access controls
        "500.12": "TRANSACTION",  # MFA
        "500.15": "TRANSACTION",  # Encryption
        
        # Personnel and Training (Governance)
        "500.10": "GOVERNANCE",  # Cybersecurity personnel
        "500.14": "GOVERNANCE",  # Training and monitoring
        
        # Third Party and Development (Platform Audit)
        "500.08": "PLATFORM_AUDIT",  # Application security
        "500.11": "PLATFORM_AUDIT",  # Third party security
        
        # Data Management (Governance)
        "500.13": "GOVERNANCE",  # Data retention
        
        # Reporting and Notification (Supervisory)
        "500.17": "SUPERVISORY",  # Breach notification
        "ANNUAL_CERTIFICATION": "SUPERVISORY",  # Annual certification
        
        # Default scope for unknown sections
        "APPLICABILITY": "SUPERVISORY",
    }
    
    return nydfs_scopes.get(article_normalized, "PLATFORM_AUDIT")


def _resolve_nydfs_enforcement_scope(article: str, payload: Dict[str, Any]) -> str:
    """
    Resolve final enforcement scope with future-proof modifiers.
    
    NYDFS enforcement scope modifiers:
    1. Class A institution escalation
    2. Active cybersecurity breach escalation
    3. Critical control requirements
    4. Regulatory compliance deadlines
    
    Returns:
        Final enforcement scope after applying modifiers
    """
    base_scope = _get_nydfs_base_enforcement_scope(article)
    article_normalized = _normalize_nydfs_article(article)
    
    # Get context information
    institution_class, _ = _classify_nydfs_institution(payload)
    nydfs_profile = payload.get("nydfs_profile", {})
    risk_indicators = payload.get("risk_indicators", {})
    
    # MODIFIER 1: Class A institution escalation
    if institution_class == "CLASS_A":
        if base_scope in {"PLATFORM_AUDIT", "GOVERNANCE"}:
            # Class A institutions need stricter enforcement
            if article_normalized in {"500.07", "500.12", "500.15"}:  # Critical controls
                return "TRANSACTION"
    
    # MODIFIER 2: Active cybersecurity breach
    if risk_indicators.get("cybersecurity_breach_active"):
        if base_scope in {"PLATFORM_AUDIT", "GOVERNANCE"}:
            # Breaches escalate all requirements
            return "TRANSACTION"
    
    # MODIFIER 3: Critical controls always transactional
    critical_controls = {"500.07", "500.12", "500.15", "500.17"}  # Access, MFA, Encryption, Breach notification
    if article_normalized in critical_controls:
        return "TRANSACTION"
    
    # MODIFIER 4: Annual certification deadline
    certification_due = nydfs_profile.get("annual_certification_due")
    if certification_due and base_scope == "SUPERVISORY":
        # Past-due certification needs immediate attention
        return "TRANSACTION"
    
    # MODIFIER 5: High-risk financial activities
    action = str(payload.get("action", "")).lower()
    high_risk_actions = {"transfer_funds", "execute_trade", "process_payment", "issue_loan"}
    if action in high_risk_actions and base_scope == "PLATFORM_AUDIT":
        # High-risk financial activities need immediate controls
        return "TRANSACTION"
    
    # No modifiers applied
    return base_scope


# ============================================================
# EVIDENCE COLLECTION (Enhanced for Future-Proofing)
# ============================================================

def _collect_nydfs_evidence(payload: Dict[str, Any], rule_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect comprehensive NYDFS evidence for audit trails.
    
    Returns:
        Structured evidence with context, rule data, and metadata
    """
    evidence = {
        # Context evidence
        "context": {
            "industry_id": payload.get("industry_id"),
            "action": payload.get("action"),
            "jurisdiction": (payload.get("meta") or {}).get("jurisdiction"),
            "nydfs_entity_detected": True,
        },
        # Rule-specific evidence
        "rule_data": rule_data,
        # NYDFS-specific information
        "nydfs_info": {},
        # Metadata
        "metadata": {
            "evidence_collected_at": "NOW",  # Would be timestamp in real implementation
            "regulation_version": "23 NYCRR Part 500",
        }
    }
    
    # Collect NYDFS-specific information
    nydfs_profile = payload.get("nydfs_profile", {})
    institution_class, _ = _classify_nydfs_institution(payload)
    program_scores, _ = _assess_cybersecurity_program(payload)
    
    evidence["nydfs_info"] = {
        "institution_class": institution_class,
        "employee_count": nydfs_profile.get("employee_count"),
        "total_assets": nydfs_profile.get("total_assets"),
        "annual_certification_status": nydfs_profile.get("annual_certification"),
        "last_certification_date": nydfs_profile.get("last_certification_date"),
        "cybersecurity_program_scores": program_scores,
    }
    
    return evidence


# ============================================================
# NYDFS 500 RULE DEFINITIONS (Enhanced with All Sections)
# ============================================================

# NYDFS 500 rules with comprehensive metadata
NYDFS_500_RULES = [
    # ============================================================
    # CYBERSECURITY PROGRAM REQUIREMENTS
    # ============================================================
    {
        "article": "23 NYCRR 500.02",
        "title": "Cybersecurity Program",
        "description": "Establish and maintain a cybersecurity program designed to protect information systems and nonpublic information.",
        "field": "cybersecurity_program",
        "severity": "HIGH",
        "rule_id": "NYDFS_500_02_CYBER_PROGRAM",
        "enforcement_scope_default": "GOVERNANCE",
        "future_proof_notes": "Must be based on risk assessment and cover all required elements. Requires annual board/senior officer approval.",
        "evidence_fields": ["nydfs_profile.cybersecurity_program", "nydfs_profile.program_documentation", "nydfs_profile.program_approval_date"],
        "institution_class_applicability": ["CLASS_A", "CLASS_B", "CLASS_C"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "23 NYCRR 500.03",
        "title": "Cybersecurity Policy",
        "description": "Adopt and enforce a written cybersecurity policy approved by board or senior officer.",
        "field": "cybersecurity_policy",
        "severity": "HIGH",
        "rule_id": "NYDFS_500_03_POLICY",
        "enforcement_scope_default": "GOVERNANCE",
        "future_proof_notes": "Policy must cover: information security, data governance, access controls, business continuity, incident response.",
        "evidence_fields": ["nydfs_profile.cybersecurity_policy", "nydfs_profile.policy_approval_date", "nydfs_profile.policy_version"],
        "institution_class_applicability": ["CLASS_A", "CLASS_B", "CLASS_C"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "23 NYCRR 500.04",
        "title": "Chief Information Security Officer",
        "description": "Designate a qualified CISO responsible for overseeing and implementing cybersecurity program.",
        "field": "ciso_appointed",
        "severity": "HIGH",
        "rule_id": "NYDFS_500_04_CISO",
        "enforcement_scope_default": "GOVERNANCE",
        "future_proof_notes": "Can be employee, affiliate, or third party. Must report to board at least annually.",
        "evidence_fields": ["nydfs_profile.ciso_appointed", "nydfs_profile.ciso_qualifications", "nydfs_profile.ciso_reporting"],
        "institution_class_applicability": ["CLASS_A", "CLASS_B"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # CYBERSECURITY TESTING AND ASSESSMENT
    # ============================================================
    {
        "article": "23 NYCRR 500.05",
        "title": "Penetration Testing and Vulnerability Assessment",
        "description": "Conduct annual penetration testing and bi-annual vulnerability assessments.",
        "field": "penetration_testing",
        "severity": "MEDIUM",
        "rule_id": "NYDFS_500_05_PEN_TESTING",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Can be internal or external. Must be conducted by qualified personnel.",
        "evidence_fields": ["nydfs_profile.penetration_testing", "nydfs_profile.last_pen_test_date", "nydfs_profile.vulnerability_assessments"],
        "institution_class_applicability": ["CLASS_A", "CLASS_B"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "23 NYCRR 500.09",
        "title": "Risk Assessment",
        "description": "Conduct periodic risk assessment of information systems.",
        "field": "risk_assessment",
        "severity": "HIGH",
        "rule_id": "NYDFS_500_09_RISK_ASSESSMENT",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Must be conducted at least annually. Must inform cybersecurity program.",
        "evidence_fields": ["nydfs_profile.risk_assessment", "nydfs_profile.last_risk_assessment", "nydfs_profile.risk_assessment_methodology"],
        "institution_class_applicability": ["CLASS_A", "CLASS_B", "CLASS_C"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # TECHNICAL CYBERSECURITY CONTROLS
    # ============================================================
    {
        "article": "23 NYCRR 500.06",
        "title": "Audit Trail",
        "description": "Maintain audit trails designed to detect and respond to cybersecurity events.",
        "field": "audit_trail",
        "severity": "HIGH",
        "rule_id": "NYDFS_500_06_AUDIT_TRAIL",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Must reconstruct financial transactions. Retain logs for 5+ years.",
        "evidence_fields": ["nydfs_profile.audit_trail", "nydfs_profile.audit_log_retention", "nydfs_profile.log_integrity"],
        "institution_class_applicability": ["CLASS_A", "CLASS_B", "CLASS_C"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "23 NYCRR 500.07",
        "title": "Access Privileges",
        "description": "Limit access privileges to authorized users and conduct periodic access reviews.",
        "field": "access_controls",
        "severity": "HIGH",
        "rule_id": "NYDFS_500_07_ACCESS_CONTROLS",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Principle of least privilege. Periodic review of access rights.",
        "evidence_fields": ["nydfs_profile.access_controls", "nydfs_profile.access_review_frequency", "nydfs_profile.privileged_access_management"],
        "institution_class_applicability": ["CLASS_A", "CLASS_B", "CLASS_C"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "23 NYCRR 500.12",
        "title": "Multi-Factor Authentication",
        "description": "Implement MFA for remote access and privileged accounts.",
        "field": "multi_factor_authentication",
        "severity": "HIGH",
        "rule_id": "NYDFS_500_12_MFA",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Required for all remote access and privileged accounts. Risk-based for other access.",
        "evidence_fields": ["nydfs_profile.multi_factor_authentication", "nydfs_profile.mfa_implementation", "nydfs_profile.remote_access_controls"],
        "institution_class_applicability": ["CLASS_A", "CLASS_B", "CLASS_C"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "23 NYCRR 500.15",
        "title": "Encryption of Nonpublic Information",
        "description": "Implement encryption controls for nonpublic information at rest and in transit.",
        "field": "data_encryption",
        "severity": "HIGH",
        "rule_id": "NYDFS_500_15_ENCRYPTION",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Encrypt all nonpublic information. Use industry-standard encryption.",
        "evidence_fields": ["nydfs_profile.data_encryption", "nydfs_profile.encryption_standards", "nydfs_profile.encryption_key_management"],
        "institution_class_applicability": ["CLASS_A", "CLASS_B", "CLASS_C"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # PERSONNEL AND THIRD-PARTY MANAGEMENT
    # ============================================================
    {
        "article": "23 NYCRR 500.10",
        "title": "Cybersecurity Personnel",
        "description": "Employ qualified cybersecurity personnel or use qualified third parties.",
        "field": "cybersecurity_personnel",
        "severity": "MEDIUM",
        "rule_id": "NYDFS_500_10_PERSONNEL",
        "enforcement_scope_default": "GOVERNANCE",
        "future_proof_notes": "Can be employees, affiliates, or third parties. Must have adequate training.",
        "evidence_fields": ["nydfs_profile.cybersecurity_personnel", "nydfs_profile.security_training", "nydfs_profile.personnel_qualifications"],
        "institution_class_applicability": ["CLASS_A", "CLASS_B"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "23 NYCRR 500.11",
        "title": "Third Party Security Policy",
        "description": "Implement written policies and procedures for third party service providers.",
        "field": "third_party_security",
        "severity": "MEDIUM",
        "rule_id": "NYDFS_500_11_THIRD_PARTY",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Due diligence, contractual protections, periodic assessment of third parties.",
        "evidence_fields": ["nydfs_profile.third_party_security", "nydfs_profile.vendor_assessments", "nydfs_profile.third_party_contracts"],
        "institution_class_applicability": ["CLASS_A", "CLASS_B", "CLASS_C"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "23 NYCRR 500.14",
        "title": "Training and Monitoring",
        "description": "Provide regular cybersecurity awareness training and monitor authorized users.",
        "field": "training_monitoring",
        "severity": "MEDIUM",
        "rule_id": "NYDFS_500_14_TRAINING",
        "enforcement_scope_default": "GOVERNANCE",
        "future_proof_notes": "Annual training for all personnel. Monitoring for unauthorized access/use.",
        "evidence_fields": ["nydfs_profile.training_monitoring", "nydfs_profile.security_awareness_training", "nydfs_profile.user_monitoring"],
        "institution_class_applicability": ["CLASS_A", "CLASS_B", "CLASS_C"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # INCIDENT RESPONSE AND REPORTING
    # ============================================================
    {
        "article": "23 NYCRR 500.16",
        "title": "Incident Response Plan",
        "description": "Establish a written incident response plan and test it annually.",
        "field": "incident_response",
        "severity": "HIGH",
        "rule_id": "NYDFS_500_16_INCIDENT_RESPONSE",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Must include: internal/external reporting, recovery procedures, evidence preservation.",
        "evidence_fields": ["nydfs_profile.incident_response", "nydfs_profile.irp_testing", "nydfs_profile.incident_response_team"],
        "institution_class_applicability": ["CLASS_A", "CLASS_B", "CLASS_C"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "23 NYCRR 500.17",
        "title": "72-Hour Breach Notification",
        "description": "Notify superintendent within 72 hours of determining a cybersecurity event.",
        "field": "breach_notification_procedures",
        "severity": "CRITICAL",
        "rule_id": "NYDFS_500_17_BREACH_NOTIFICATION",
        "enforcement_scope_default": "SUPERVISORY",
        "future_proof_notes": "Notification required for material impact. Annual notice of exemptions.",
        "evidence_fields": ["nydfs_profile.breach_notification_procedures", "nydfs_profile.last_notification_drill", "nydfs_profile.notification_contacts"],
        "institution_class_applicability": ["CLASS_A", "CLASS_B", "CLASS_C"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # ANNUAL CERTIFICATION (Critical Requirement)
    # ============================================================
    {
        "article": "NYDFS Annual Certification",
        "title": "Annual Certification to Superintendent",
        "description": "File annual certification of compliance with NYDFS cybersecurity requirements.",
        "field": "annual_certification",
        "severity": "CRITICAL",
        "rule_id": "NYDFS_ANNUAL_CERTIFICATION",
        "enforcement_scope_default": "SUPERVISORY",
        "future_proof_notes": "Due February 15 each year. Must be signed by senior officer/board.",
        "evidence_fields": ["nydfs_profile.annual_certification", "nydfs_profile.last_certification_date", "nydfs_profile.certification_authority"],
        "institution_class_applicability": ["CLASS_A", "CLASS_B", "CLASS_C"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # FUTURE NYDFS AMENDMENTS (Readiness for updates)
    # ============================================================
    {
        "article": "NYDFS Proposed 500.18",
        "title": "Ransomware Preparedness",
        "description": "Enhanced ransomware protection and response requirements.",
        "field": "ransomware_preparedness",
        "severity": "HIGH",
        "rule_id": "NYDFS_500_18_RANSOMWARE",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Proposed amendment for enhanced ransomware controls, backups, and response planning.",
        "evidence_fields": ["nydfs_profile.ransomware_preparedness", "nydfs_profile.backup_recovery", "nydfs_profile.ransomware_response"],
        "institution_class_applicability": ["CLASS_A", "CLASS_B"],
        "compliance_level": "ADDRESSABLE",
        "future_implementation": True,
    },
    {
        "article": "NYDFS Proposed 500.19",
        "title": "Supply Chain Security",
        "description": "Enhanced supply chain and third-party risk management.",
        "field": "supply_chain_security",
        "severity": "MEDIUM",
        "rule_id": "NYDFS_500_19_SUPPLY_CHAIN",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Proposed amendment for software supply chain security and vendor risk management.",
        "evidence_fields": ["nydfs_profile.supply_chain_security", "nydfs_profile.software_bill_of_materials", "nydfs_profile.vendor_risk_program"],
        "institution_class_applicability": ["CLASS_A"],
        "compliance_level": "ADDRESSABLE",
        "future_implementation": True,
    },
]


# ============================================================
# MAIN EVALUATION FUNCTION (Future-Proof Architecture)
# ============================================================

def evaluate_nydfs_500_rules(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Future-proof NYDFS 500 evaluation with comprehensive context gating.
    
    Features:
    1. Multi-method NYDFS entity detection
    2. Institution classification (Class A, B, C, Limited Exemption)
    3. Cybersecurity program requirement assessment
    4. 72-hour breach notification compliance
    5. Enhanced enforcement scope resolution
    6. Comprehensive evidence collection
    7. Detailed context tracking
    8. Future amendment readiness
    
    Returns:
        (policies, summary)
        - policies: List with enforcement_scope, evidence, and context
        - summary: Aggregate statistics with detailed context info
    """
    policies: List[Dict[str, Any]] = []
    
    # ============================================================
    # FUTURE-PROOF: CONTEXT GATING DECISION
    # ============================================================
    should_evaluate, evaluation_reason, context_evidence = _should_evaluate_nydfs_500(payload)
    
    if not should_evaluate:
        # NYDFS 500 doesn't apply - return with NOT_APPLICABLE
        policies.append({
            "domain": NYDFS_DOMAIN,
            "regime": "NYDFS_500",
            "framework": NYDFS_FRAMEWORK,
            "domain_id": "NYDFS_500",
            "article": "23 NYCRR 500:APPLICABILITY",
            "category": "Applicability",
            "title": "Applicability",
            "status": "NOT_APPLICABLE",
            "severity": "LOW",
            "impact_on_verdict": "COMPLIANT",
            "trigger_type": "NOT_APPLICABLE",
            "rule_ids": ["NYDFS_500_APPLICABILITY_NA"],
            "enforcement_scope": "SUPERVISORY",
            "notes": f"NYDFS 500 evaluation skipped: {evaluation_reason}",
            "evidence": context_evidence,
            "remediation": "No remediation required.",
            "violation_detail": "",
            "control_severity": "LOW",
        })
        
        summary = {
            "total_rules": 1,
            "passed": 0,
            "failed": 0,
            "blocking_failures": 0,
            "regime": "NYDFS_500",
            "context_gated": True,
            "evaluation_decision": evaluation_reason,
            "context_evidence": context_evidence,
            "notes": f"NYDFS 500 evaluation skipped: {evaluation_reason}"
        }
        return policies, summary
    
    # ============================================================
    # CONTEXT INFORMATION COLLECTION
    # ============================================================
    institution_class, institution_evidence = _classify_nydfs_institution(payload)
    program_scores, program_evidence = _assess_cybersecurity_program(payload)
    nydfs_profile = payload.get("nydfs_profile", {}) or {}
    risk_indicators = payload.get("risk_indicators", {}) or {}
    
    # ============================================================
    # RULE EVALUATION (Enhanced with Evidence Collection)
    # ============================================================
    
    evaluation_errors = []
    
    for rule_def in NYDFS_500_RULES:
        # Skip future implementation rules if not ready
        if rule_def.get("future_implementation") and not nydfs_profile.get("enable_future_requirements"):
            continue
        
        # Check if rule applies to this institution class
        applicable_classes = rule_def.get("institution_class_applicability", [])
        if institution_class not in applicable_classes and applicable_classes:
            continue
        
        try:
            # Check if the required field exists and is compliant
            field_value = nydfs_profile.get(rule_def["field"])
            
            # Determine status based on field value
            if field_value is False:
                status = "VIOLATED"
            elif field_value is True:
                status = "SATISFIED"
            elif field_value is None:
                # Missing field - determine based on compliance level
                if rule_def.get("compliance_level") == "REQUIRED":
                    status = "VIOLATED"
                else:
                    status = "NOT_APPLICABLE"
            else:
                # Other values - treat as satisfied
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
            
            # Get enforcement scope with modifiers
            enforcement_scope = _resolve_nydfs_enforcement_scope(rule_def["article"], payload)
            
            # Determine impact on verdict
            if status == "VIOLATED" and rule_def["severity"] in {"HIGH", "CRITICAL"}:
                impact_on_verdict = "BLOCKING_FAILURE"
            elif status == "VIOLATED":
                impact_on_verdict = "NON_BLOCKING"
            else:
                impact_on_verdict = "COMPLIANT"
            
            # Determine severity based on context
            severity = rule_def["severity"]
            if status == "VIOLATED" and institution_class == "CLASS_A":
                # Escalate severity for Class A institutions
                if severity == "MEDIUM":
                    severity = "HIGH"
                elif severity == "HIGH":
                    severity = "CRITICAL"
            
            # Check for active breaches that escalate severity
            if status == "VIOLATED" and risk_indicators.get("cybersecurity_breach_active"):
                if severity == "MEDIUM":
                    severity = "HIGH"
                elif severity == "HIGH":
                    severity = "CRITICAL"
            
            # Create policy
            policy = {
                "domain": NYDFS_DOMAIN,
                "regime": "NYDFS_500",
                "framework": NYDFS_FRAMEWORK,
                "domain_id": "NYDFS_500",
                "article": rule_def["article"],
                "category": rule_def["title"],
                "title": rule_def["title"],
                "status": status,
                "severity": severity if status == "VIOLATED" else "LOW",
                "enforcement_scope": enforcement_scope,
                "impact_on_verdict": impact_on_verdict,
                "trigger_type": "NYDFS_500_CONTROL",
                "rule_ids": [rule_def["rule_id"]],
                "notes": rule_def["description"],
                "evidence": _collect_nydfs_evidence(payload, rule_evidence),
                "remediation": (
                    f"Implement {rule_def['title']} controls per NYDFS 500 requirements. "
                    "Document procedures and re-run GNCE after remediation."
                    if status == "VIOLATED" else "No remediation required."
                ),
                "violation_detail": rule_def["description"] if status == "VIOLATED" else "",
                "control_severity": rule_def["severity"],
                # Future-proof metadata
                "metadata": {
                    "institution_class": institution_class,
                    "institution_class_applicability": applicable_classes,
                    "compliance_level": rule_def.get("compliance_level", "REQUIRED"),
                    "breach_notification_required": "500.17" in rule_def["article"],
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
        "institution_class": institution_class,
        "nydfs_entity_detected": True,
    }
    
    # Count by requirement type
    program_violations = sum(1 for p in policies 
                           if p["status"] == "VIOLATED" and "500.02" in p["article"])
    technical_violations = sum(1 for p in policies 
                             if p["status"] == "VIOLATED" and any(
                                 section in p["article"] for section in ["500.06", "500.07", "500.12", "500.15"]
                             ))
    reporting_violations = sum(1 for p in policies 
                             if p["status"] == "VIOLATED" and any(
                                 section in p["article"] for section in ["500.16", "500.17", "ANNUAL_CERTIFICATION"]
                             ))
    
    # Cybersecurity program scores
    program_score_summary = {}
    for element_id, score in program_scores.items():
        element_info = NYDFS_REQUIRED_ELEMENTS.get(element_id, {})
        program_score_summary[f"{element_id.lower()}_score"] = {
            "score": score,
            "section": element_info.get("section", "UNKNOWN"),
        }
    
    summary = {
        "total_rules": len(policies),
        "passed": passed,
        "failed": failed,
        "blocking_failures": blocking,
        "regime": "NYDFS_500",
        "context_gated": False,
        "evaluation_decision": evaluation_reason,
        # Context information
        "context": context_info,
        "context_evidence": context_evidence,
        # Institution information
        "institution_class": institution_class,
        "institution_classification": institution_evidence,
        # Cybersecurity program assessment
        "cybersecurity_program_scores": program_scores,
        "cybersecurity_program_assessment": program_evidence,
        # Violation breakdown
        "program_violations": program_violations,
        "technical_violations": technical_violations,
        "reporting_violations": reporting_violations,
        "class_a_violations": sum(1 for p in policies 
                                if p["status"] == "VIOLATED" and 
                                p.get("metadata", {}).get("institution_class") == "CLASS_A"),
        # Compliance level breakdown
        "required_violations": sum(1 for p in policies 
                                 if p["status"] == "VIOLATED" and 
                                 p.get("metadata", {}).get("compliance_level") == "REQUIRED"),
        "addressable_violations": sum(1 for p in policies 
                                    if p["status"] == "VIOLATED" and 
                                    p.get("metadata", {}).get("compliance_level") == "ADDRESSABLE"),
        # Scope breakdown
        "governance_violations": sum(1 for p in policies 
                                   if p["status"] == "VIOLATED" and p.get("enforcement_scope") == "GOVERNANCE"),
        "platform_audit_violations": sum(1 for p in policies 
                                       if p["status"] == "VIOLATED" and p.get("enforcement_scope") == "PLATFORM_AUDIT"),
        "transaction_violations": sum(1 for p in policies 
                                    if p["status"] == "VIOLATED" and p.get("enforcement_scope") == "TRANSACTION"),
        "supervisory_violations": sum(1 for p in policies 
                                    if p["status"] == "VIOLATED" and p.get("enforcement_scope") == "SUPERVISORY"),
        # Risk indicators
        "active_cybersecurity_breach": risk_indicators.get("cybersecurity_breach_active", False),
        "breach_detected": risk_indicators.get("cybersecurity_breach_detected", False),
        "breach_notification_required": risk_indicators.get("cybersecurity_breach_detected", False) and 
                                      not nydfs_profile.get("breach_notification_filed", False),
        # Rule statistics
        "core_rules_evaluated": len([r for r in NYDFS_500_RULES if not r.get("future_implementation")]),
        "future_rules_available": len([r for r in NYDFS_500_RULES if r.get("future_implementation")]),
        "future_rules_evaluated": len([r for r in NYDFS_500_RULES if r.get("future_implementation") 
                                      and nydfs_profile.get("enable_future_requirements")]),
        # Annual certification status
        "annual_certification_compliant": nydfs_profile.get("annual_certification", False),
        "certification_due_date": nydfs_profile.get("certification_due_date"),
        # Error tracking
        "evaluation_errors": evaluation_errors if evaluation_errors else None,
    }
    
    return policies, summary