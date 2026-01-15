# gnce/gn_kernel/rules/hipaa_rules.py
"""
HIPAA Rule Evaluator with Constitutional Binding (v0.7.2-RC-FUTUREPROOF)

CRITICAL UPDATES FOR FUTURE-PROOFING:
1. Comprehensive healthcare context detection with multi-method verification
2. Protected Health Information (PHI) detection with classification
3. Enhanced Covered Entity vs Business Associate determination
4. HIPAA Omnibus Rule and HITECH Act integration
5. Industry and action filtering for healthcare contexts
6. Enhanced enforcement scope resolution with risk-aware escalation
7. Comprehensive evidence collection for audit trails
8. Cross-domain safety (won't misfire on non-healthcare systems)
9. Future HIPAA rules ready for implementation
10. Breach notification with tiered severity levels

HIPAA Reality (Future-Proof):
- Privacy Rule (Subpart E): Individual rights and use/disclosure limits
- Security Rule (Subpart C): Administrative, Physical, Technical safeguards
- Breach Notification Rule (Subpart D): Notification requirements
- Enforcement Rule (Subpart A): Penalties and procedures
- Omnibus Rule: Business Associate liability, genetic information protection
- HITECH Act: Meaningful Use, EHR incentives, stronger enforcement
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple, Set, Optional
import re

# Load governance catalog for enforcement scope classification
from gnce.gn_kernel.constitution.constitution_catalog import load_governance_catalog_v05

# ============================================================
# MODULE CONSTANTS (FUTURE-PROOF)
# ============================================================

HIPAA_DOMAIN = "US Healthcare Privacy & Security (HIPAA)"
HIPAA_FRAMEWORK = "US Healthcare Privacy & Security"
HIPAA_REGIME_ID = "HIPAA"

# Load catalog once at module level (performance)
_GOVERNANCE_CATALOG = load_governance_catalog_v05()

# ============================================================
# HEALTHCARE CONTEXT DETECTION (FUTURE-PROOF)
# ============================================================

# Healthcare industry identifiers (expanded)
HEALTHCARE_INDUSTRIES: Set[str] = {
    "HEALTHCARE",
    "MEDICAL",
    "HOSPITAL",
    "CLINIC",
    "PHARMACY",
    "INSURANCE_MEDICAL",
    "TELEHEALTH",
    "LABORATORY",
    "BIOTECH",
    "MEDICAL_DEVICE",
    "HEALTH_TECH",
    "HEALTH_INSURANCE",
    "NURSING_HOME",
    "HOSPICE",
    "AMBULATORY_CARE",
    "DENTAL",
    "VETERINARY",
    "MENTAL_HEALTH",
    "SUBSTANCE_ABUSE_TREATMENT",
    "PUBLIC_HEALTH",
}

# Healthcare actions where HIPAA applies
HEALTHCARE_ACTIONS: Set[str] = {
    # Clinical care actions
    "access_medical_record",
    "create_medical_record",
    "update_medical_record",
    "transmit_phi",
    "query_patient_data",
    "document_clinical_care",
    "order_prescription",
    "process_lab_result",
    "schedule_appointment",
    "conduct_telehealth",
    "perform_diagnosis",
    "recommend_treatment",
    
    # Administrative actions
    "process_medical_billing",
    "submit_insurance_claim",
    "verify_insurance",
    "manage_patient_account",
    "coordinate_care",
    "conduct_medical_research",
    "report_public_health",
    "audit_medical_records",
    
    # Technical actions
    "encrypt_phi",
    "backup_medical_data",
    "restore_medical_data",
    "archive_medical_records",
    "extract_phi_for_analytics",
    "deidentify_phi",
    "pseudonymize_phi",
}

# Protected Health Information (PHI) identifiers
PHI_IDENTIFIERS: Set[str] = {
    "name",
    "address",
    "birth_date",
    "admission_date",
    "discharge_date",
    "death_date",
    "telephone_number",
    "fax_number",
    "email_address",
    "social_security_number",
    "medical_record_number",
    "health_plan_beneficiary_number",
    "account_number",
    "certificate_license_number",
    "vehicle_identifier",
    "device_identifier",
    "url",
    "ip_address",
    "biometric_identifier",
    "full_face_photo",
    "any_other_unique_identifying_number",
}

# PHI data categories
PHI_CATEGORIES: Set[str] = {
    "demographic_information",
    "medical_history",
    "test_results",
    "insurance_information",
    "billing_information",
    "treatment_plans",
    "progress_notes",
    "diagnosis_codes",
    "procedure_codes",
    "medication_records",
    "allergy_information",
    "immunization_records",
    "genetic_information",
    "mental_health_notes",
    "substance_abuse_records",
    "hiv_status",
    "sexual_orientation",
    "disability_status",
}

# HIPAA Covered Entity types
COVERED_ENTITY_TYPES: Set[str] = {
    "HEALTHCARE_PROVIDER",
    "HEALTH_PLAN",
    "HEALTHCARE_CLEARINGHOUSE",
    "COVERED_ENTITY",
    "MEDICAL_PRACTICE",
    "HOSPITAL_SYSTEM",
    "INSURANCE_COMPANY",
    "PHARMACY_BENEFIT_MANAGER",
}

# Business Associate types
BUSINESS_ASSOCIATE_TYPES: Set[str] = {
    "BUSINESS_ASSOCIATE",
    "SUBCONTRACTOR",
    "CLOUD_SERVICE_PROVIDER",
    "IT_MANAGED_SERVICES",
    "BILLING_COMPANY",
    "TRANSCRIPTION_SERVICE",
    "ANALYTICS_PROVIDER",
    "CONSULTING_FIRM",
}

# Jurisdictions where HIPAA applies
HIPAA_JURISDICTIONS: Set[str] = {
    "US",
    "USA",
    "UNITED_STATES",
    "US-ALL",  # All US states
    "US-NY",  # New York
    "US-CA",  # California
    "US-TX",  # Texas
    "US-FL",  # Florida
    "US-IL",  # Illinois
}

# Actions where HIPAA likely doesn't apply (future-proof exclusions)
NON_HIPAA_ACTIONS: Set[str] = {
    # General business actions
    "login",
    "logout",
    "view_dashboard",
    "generate_report",
    "export_data",
    
    # System management
    "system_backup",
    "update_software",
    "monitor_performance",
    "audit_logs",
    
    # Non-PHI data operations
    "store_public_data",
    "retrieve_public_data",
    "delete_temp_data",
    "process_anonymous_data",
}

# Breach severity thresholds (tiered)
BREACH_THRESHOLDS = {
    "INSIGNIFICANT": 1,      # < 10 records
    "MINOR": 10,             # 10-499 records
    "MODERATE": 100,         # 100-499 records
    "MAJOR": 500,            # 500+ records (HHS notification)
    "CRITICAL": 1000,        # 1000+ records (media notification)
}

# ============================================================
# HEALTHCARE CONTEXT DETECTION (FUTURE-PROOF)
# ============================================================

def _detect_healthcare_context(payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Future-proof healthcare context detection with comprehensive verification.
    
    Returns:
        (is_healthcare_context, detection_evidence)
    """
    detection_evidence = {
        "methods_used": [],
        "indicators_found": [],
        "confidence": "LOW",
    }
    
    # Method 1: Explicit healthcare flags
    if payload.get("is_healthcare_system") or payload.get("handles_phi"):
        detection_evidence["methods_used"].append("EXPLICIT_FLAG")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["indicators_found"].append("explicit_healthcare_flag")
        return True, detection_evidence
    
    # Method 2: Industry classification
    industry = str(payload.get("industry_id", "")).upper().strip()
    if industry in HEALTHCARE_INDUSTRIES:
        detection_evidence["methods_used"].append("INDUSTRY_CLASSIFICATION")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["indicators_found"].append(f"industry:{industry}")
        return True, detection_evidence
    
    # Method 3: Action classification
    action = str(payload.get("action", "")).lower().strip()
    if action in HEALTHCARE_ACTIONS:
        detection_evidence["methods_used"].append("ACTION_CLASSIFICATION")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["indicators_found"].append(f"action:{action}")
        return True, detection_evidence
    
    # Method 4: HIPAA profile detection
    hipaa_profile = payload.get("hipaa_profile", {})
    if hipaa_profile:
        detection_evidence["methods_used"].append("HIPAA_PROFILE")
        detection_evidence["indicators_found"].append("hipaa_profile_exists")
        
        if hipaa_profile.get("handles_phi"):
            detection_evidence["confidence"] = "HIGH"
            return True, detection_evidence
    
    # Method 5: Data field detection (PHI identifiers)
    data_fields = payload.get("data_fields", [])
    if isinstance(data_fields, list):
        phi_fields = [field for field in data_fields 
                     if any(phi_id in str(field).lower() for phi_id in PHI_IDENTIFIERS)]
        if phi_fields:
            detection_evidence["methods_used"].append("PHI_FIELD_DETECTION")
            detection_evidence["confidence"] = "MEDIUM"
            detection_evidence["indicators_found"].extend([f"phi_field:{f}" for f in phi_fields[:3]])
            return True, detection_evidence
    
    # Method 6: Meta/platform signals
    meta = payload.get("meta", {})
    platform_type = str(meta.get("platform_type", "")).lower()
    if any(hc_term in platform_type for hc_term in ["medical", "health", "hospital", "clinic", "phi"]):
        detection_evidence["methods_used"].append("PLATFORM_SIGNAL")
        detection_evidence["confidence"] = "MEDIUM"
        detection_evidence["indicators_found"].append(f"platform_type:{platform_type}")
        return True, detection_evidence
    
    return False, detection_evidence


def _detect_phi_handling(payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Detect if Protected Health Information (PHI) is being handled.
    
    Returns:
        (handles_phi, detection_evidence)
    """
    detection_evidence = {
        "methods_used": [],
        "phi_types_detected": [],
        "confidence": "LOW",
    }
    
    hipaa_profile = payload.get("hipaa_profile", {})
    
    # Method 1: Explicit PHI handling flag
    if hipaa_profile.get("handles_phi"):
        detection_evidence["methods_used"].append("EXPLICIT_PHI_FLAG")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["phi_types_detected"].append("explicit_phi_handling")
        return True, detection_evidence
    
    # Method 2: PHI categories declared
    phi_categories = hipaa_profile.get("phi_categories", [])
    if isinstance(phi_categories, list) and phi_categories:
        detection_evidence["methods_used"].append("PHI_CATEGORIES_DECLARED")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["phi_types_detected"].extend(phi_categories[:5])
        return True, detection_evidence
    
    # Method 3: Data sensitivity classification
    data_sensitivity = str(hipaa_profile.get("data_sensitivity", "")).upper()
    if data_sensitivity in {"PHI", "PROTECTED_HEALTH_INFORMATION", "RESTRICTED_HEALTH_DATA"}:
        detection_evidence["methods_used"].append("DATA_SENSITIVITY")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["phi_types_detected"].append("sensitive_health_data")
        return True, detection_evidence
    
    # Method 4: Healthcare context + patient data
    is_hc_context, hc_evidence = _detect_healthcare_context(payload)
    if is_hc_context:
        action = str(payload.get("action", "")).lower()
        if any(phi_action in action for phi_action in ["patient", "medical", "health", "record"]):
            detection_evidence["methods_used"].append("CONTEXTUAL_INFERENCE")
            detection_evidence["confidence"] = "MEDIUM"
            detection_evidence["phi_types_detected"].append("healthcare_patient_data")
            return True, detection_evidence
    
    return False, detection_evidence


def _determine_entity_type(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Determine HIPAA entity type: Covered Entity vs Business Associate vs Hybrid.
    
    Returns:
        (entity_type, determination_evidence)
        entity_type: "COVERED_ENTITY", "BUSINESS_ASSOCIATE", "HYBRID_ENTITY", "UNKNOWN"
    """
    determination_evidence = {
        "factors_considered": [],
        "entity_type": "UNKNOWN",
        "confidence": "LOW",
    }
    
    meta = payload.get("meta", {})
    hipaa_profile = payload.get("hipaa_profile", {})
    
    # Factor 1: Explicit entity type
    entity_type = str(meta.get("entity_type", "")).upper()
    if entity_type in COVERED_ENTITY_TYPES:
        determination_evidence["factors_considered"].append("EXPLICIT_COVERED_ENTITY")
        determination_evidence["entity_type"] = "COVERED_ENTITY"
        determination_evidence["confidence"] = "HIGH"
        return "COVERED_ENTITY", determination_evidence
    
    if entity_type in BUSINESS_ASSOCIATE_TYPES:
        determination_evidence["factors_considered"].append("EXPLICIT_BUSINESS_ASSOCIATE")
        determination_evidence["entity_type"] = "BUSINESS_ASSOCIATE"
        determination_evidence["confidence"] = "HIGH"
        return "BUSINESS_ASSOCIATE", determination_evidence
    
    # Factor 2: HIPAA profile declaration
    if hipaa_profile.get("is_covered_entity"):
        determination_evidence["factors_considered"].append("HIPAA_PROFILE_COVERED_ENTITY")
        determination_evidence["entity_type"] = "COVERED_ENTITY"
        determination_evidence["confidence"] = "HIGH"
        return "COVERED_ENTITY", determination_evidence
    
    if hipaa_profile.get("is_business_associate"):
        determination_evidence["factors_considered"].append("HIPAA_PROFILE_BUSINESS_ASSOCIATE")
        determination_evidence["entity_type"] = "BUSINESS_ASSOCIATE"
        determination_evidence["confidence"] = "HIGH"
        return "BUSINESS_ASSOCIATE", determination_evidence
    
    # Factor 3: Business activities
    activities = hipaa_profile.get("business_activities", [])
    if isinstance(activities, list):
        if any(ce_activity in str(activities).upper() 
               for ce_activity in ["TREATMENT", "PAYMENT", "HEALTHCARE_OPERATIONS"]):
            determination_evidence["factors_considered"].append("COVERED_ENTITY_ACTIVITIES")
            determination_evidence["entity_type"] = "COVERED_ENTITY"
            determination_evidence["confidence"] = "MEDIUM"
            return "COVERED_ENTITY", determination_evidence
        
        if any(ba_activity in str(activities).upper() 
               for ba_activity in ["DATA_PROCESSING", "IT_SERVICES", "ANALYTICS", "BILLING"]):
            determination_evidence["factors_considered"].append("BUSINESS_ASSOCIATE_ACTIVITIES")
            determination_evidence["entity_type"] = "BUSINESS_ASSOCIATE"
            determination_evidence["confidence"] = "MEDIUM"
            return "BUSINESS_ASSOCIATE", determination_evidence
    
    # Factor 4: Industry context
    industry = str(payload.get("industry_id", "")).upper()
    if industry in {"HOSPITAL", "CLINIC", "MEDICAL_PRACTICE"}:
        determination_evidence["factors_considered"].append(f"INDUSTRY:{industry}")
        determination_evidence["entity_type"] = "COVERED_ENTITY"
        determination_evidence["confidence"] = "LOW"
        return "COVERED_ENTITY", determination_evidence
    
    # Default: Unknown (conservative)
    return "UNKNOWN", determination_evidence


def _should_evaluate_hipaa(payload: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Future-proof decision: Should HIPAA evaluation run for this payload?
    
    Returns:
        (should_evaluate, evaluation_reason, context_evidence)
    """
    context_evidence = {
        "healthcare_context_detection": {},
        "phi_handling_detection": {},
        "entity_type_determination": {},
        "jurisdiction_check": {},
        "context_checks": {},
    }
    
    # Check 1: Healthcare context detection
    is_hc_context, hc_evidence = _detect_healthcare_context(payload)
    context_evidence["healthcare_context_detection"] = hc_evidence
    
    if not is_hc_context:
        return False, "NOT_HEALTHCARE_CONTEXT", context_evidence
    
    # Check 2: PHI handling detection
    handles_phi, phi_evidence = _detect_phi_handling(payload)
    context_evidence["phi_handling_detection"] = phi_evidence
    
    if not handles_phi:
        return False, "NOT_HANDLING_PHI", context_evidence
    
    # Check 3: Jurisdiction
    meta = payload.get("meta", {})
    jurisdiction = str(meta.get("jurisdiction", "")).upper().strip()
    context_evidence["jurisdiction_check"]["jurisdiction"] = jurisdiction
    
    if jurisdiction not in HIPAA_JURISDICTIONS:
        return False, f"JURISDICTION_OUTSIDE_US: {jurisdiction}", context_evidence
    
    # Check 4: Action relevance
    action = str(payload.get("action", "")).lower().strip()
    context_evidence["context_checks"]["action"] = action
    
    if action in NON_HIPAA_ACTIONS:
        return False, f"ACTION_EXCLUDED: {action}", context_evidence
    
    # Check 5: Entity type determination
    entity_type, entity_evidence = _determine_entity_type(payload)
    context_evidence["entity_type_determination"] = entity_evidence
    
    # All checks passed - evaluate HIPAA
    return True, f"EVALUATE_HIPAA_ENTITY:{entity_type}", context_evidence


# ============================================================
# ENFORCEMENT SCOPE RESOLUTION (FUTURE-PROOF)
# ============================================================

def _normalize_hipaa_article(article: str) -> str:
    """
    Normalize HIPAA article identifier for consistent comparison.
    
    Future-proof examples:
        "45 CFR §164.312(a)(1)" → "164.312(a)(1)"
        "§164.502(b)" → "164.502(b)"
        "164.404" → "164.404"
        "HIPAA Privacy Rule" → "PRIVACY_RULE"
        "HITECH §13402" → "HITECH_13402"
    """
    if not article:
        return ""
    
    article = article.strip()
    
    # Remove common prefixes
    article = re.sub(r"(?i)^(45\s*CFR\s*)?§?\s*", "", article)
    article = re.sub(r"(?i)^(hipaa\s*)?(privacy\s*rule)", "PRIVACY_RULE", article)
    article = re.sub(r"(?i)^(hipaa\s*)?(security\s*rule)", "SECURITY_RULE", article)
    article = re.sub(r"(?i)^(hipaa\s*)?(breach\s*notification\s*rule)", "BREACH_NOTIFICATION_RULE", article)
    article = re.sub(r"(?i)^(hitech\s*)§?", "HITECH_", article)
    
    # Extract CFR part and section
    cfr_match = re.match(r"(\d+\.\d+[a-zA-Z\(\)0-9]*)", article)
    if cfr_match:
        return cfr_match.group(1)
    
    # Return cleaned string
    return article.replace(" ", "_").upper()


def _get_hipaa_base_enforcement_scope(article: str) -> str:
    """
    Get base enforcement scope from governance catalog.
    
    Future-proof HIPAA Classification:
    - Privacy Rules: TRANSACTION for disclosures, POSTURE for policies
    - Security Rules: TRANSACTION for access controls, POSTURE for risk assessments
    - Breach Notification: TRANSACTION for immediate breaches, SUPERVISORY for HHS reporting
    - Technical Safeguards: TRANSACTION (immediate enforcement)
    - Administrative Safeguards: POSTURE/PLATFORM_AUDIT (organizational)
    - Physical Safeguards: POSTURE (facility controls)
    
    Returns: "TRANSACTION" | "POSTURE" | "PLATFORM_AUDIT" | "SUPERVISORY" | "TECHNICAL" | "ADMINISTRATIVE"
    Default: "POSTURE" (safe - logs but doesn't block unknown articles)
    """
    article_normalized = _normalize_hipaa_article(article)
    
    # First check catalog
    for regime in _GOVERNANCE_CATALOG.get("regimes", []):
        if regime.get("id") == HIPAA_REGIME_ID:
            for domain in regime.get("domains", []):
                for art_def in domain.get("articles", []):
                    if art_def.get("article", "") == article_normalized:
                        return art_def.get("enforcement_scope", "POSTURE")
    
    # Local mapping for common HIPAA articles
    local_hipaa_scopes = {
        # Privacy Rules
        "164.502(a)": "POSTURE",      # Uses and disclosures
        "164.502(b)": "TRANSACTION",  # Minimum necessary
        "164.504(e)": "POSTURE",      # Business Associate Agreements
        "164.530(a)(1)(i)": "POSTURE",# Privacy Officer
        
        # Security Rules - Administrative Safeguards
        "164.308(a)(1)(ii)(A)": "POSTURE",  # Risk analysis
        "164.308(a)(3)(i)": "POSTURE",      # Workforce security
        "164.308(a)(7)(i)": "POSTURE",      # Contingency plan
        
        # Security Rules - Technical Safeguards
        "164.312(a)(1)": "TRANSACTION",     # Access control
        "164.312(b)": "TRANSACTION",        # Audit controls
        "164.312(e)(1)": "TRANSACTION",     # Transmission security
        
        # Security Rules - Physical Safeguards
        "164.310(c)": "POSTURE",            # Device controls
        
        # Breach Notification
        "164.404": "TRANSACTION",           # Individual notification
        "164.410": "SUPERVISORY",           # HHS notification
        
        # HITECH Act
        "HITECH_13402": "TRANSACTION",      # Breach notification
        "HITECH_13410": "SUPERVISORY",      # Enforcement
    }
    
    return local_hipaa_scopes.get(article_normalized, "POSTURE")


def _classify_breach_severity(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Classify breach severity with comprehensive analysis.
    
    Returns:
        (severity_level, classification_evidence)
        severity_level: "INSIGNIFICANT", "MINOR", "MODERATE", "MAJOR", "CRITICAL"
    """
    classification_evidence = {
        "factors_considered": [],
        "severity": "INSIGNIFICANT",
        "confidence": "LOW",
    }
    
    risk_indicators = payload.get("risk_indicators", {})
    
    # Check if breach is actually detected
    breach_detected = risk_indicators.get("breach_detected", False)
    if not breach_detected:
        return "INSIGNIFICANT", classification_evidence
    
    # Factor 1: Number of records exposed
    phi_records_exposed = risk_indicators.get("phi_records_exposed", 0)
    classification_evidence["factors_considered"].append(f"RECORDS_EXPOSED:{phi_records_exposed}")
    
    if phi_records_exposed >= BREACH_THRESHOLDS["CRITICAL"]:
        classification_evidence["severity"] = "CRITICAL"
        classification_evidence["confidence"] = "HIGH"
        return "CRITICAL", classification_evidence
    elif phi_records_exposed >= BREACH_THRESHOLDS["MAJOR"]:
        classification_evidence["severity"] = "MAJOR"
        classification_evidence["confidence"] = "HIGH"
        return "MAJOR", classification_evidence
    elif phi_records_exposed >= BREACH_THRESHOLDS["MODERATE"]:
        classification_evidence["severity"] = "MODERATE"
        classification_evidence["confidence"] = "MEDIUM"
        return "MODERATE", classification_evidence
    elif phi_records_exposed >= BREACH_THRESHOLDS["MINOR"]:
        classification_evidence["severity"] = "MINOR"
        classification_evidence["confidence"] = "MEDIUM"
        return "MINOR", classification_evidence
    
    # Factor 2: Data sensitivity
    data_sensitivity = risk_indicators.get("data_sensitivity", "LOW")
    classification_evidence["factors_considered"].append(f"DATA_SENSITIVITY:{data_sensitivity}")
    
    if data_sensitivity in {"HIGH", "CRITICAL"}:
        classification_evidence["severity"] = "MODERATE"
        classification_evidence["confidence"] = "MEDIUM"
        return "MODERATE", classification_evidence
    
    return "INSIGNIFICANT", classification_evidence


def _resolve_hipaa_enforcement_scope(article: str, payload: Dict[str, Any]) -> str:
    """
    Resolve final enforcement scope with future-proof modifiers.
    
    HIPAA enforcement scope modifiers:
    1. Covered Entity vs Business Associate
    2. Breach severity escalation
    3. PHI sensitivity modifiers
    4. Action-specific considerations
    5. Entity size and risk profile
    
    Returns:
        Final enforcement scope after applying modifiers
    """
    base_scope = _get_hipaa_base_enforcement_scope(article)
    article_normalized = _normalize_hipaa_article(article)
    
    # Get context information
    entity_type, _ = _determine_entity_type(payload)
    breach_severity, _ = _classify_breach_severity(payload)
    action = str(payload.get("action", "")).lower()
    hipaa_profile = payload.get("hipaa_profile", {})
    
    # MODIFIER 1: Covered Entity escalation
    # Covered entities have stricter immediate requirements
    if entity_type == "COVERED_ENTITY":
        if base_scope == "POSTURE" and article_normalized in {"164.502(b)", "164.312(a)(1)", "164.312(e)(1)"}:
            # Minimum necessary, access control, transmission security
            return "TRANSACTION"
    
    # MODIFIER 2: Breach severity escalation
    if breach_severity in {"MAJOR", "CRITICAL"}:
        if base_scope in {"POSTURE", "PLATFORM_AUDIT"}:
            # Major breaches require immediate action
            return "TRANSACTION"
    
    # MODIFIER 3: High-sensitivity PHI escalation
    phi_sensitivity = hipaa_profile.get("phi_sensitivity", "MEDIUM")
    if phi_sensitivity in {"HIGH", "CRITICAL"}:
        if base_scope == "POSTURE" and "164.312" in article_normalized:
            # Technical safeguards for sensitive PHI
            return "TRANSACTION"
    
    # MODIFIER 4: Real-time clinical actions
    clinical_actions = {"access_medical_record", "transmit_phi", "order_prescription"}
    if action in clinical_actions and base_scope == "POSTURE":
        # Clinical care actions need immediate enforcement
        return "TRANSACTION"
    
    # MODIFIER 5: Large entity escalation
    entity_size = hipaa_profile.get("entity_size", "SMALL")
    if entity_size in {"LARGE", "VERY_LARGE"} and base_scope == "PLATFORM_AUDIT":
        # Large entities have more immediate compliance needs
        return "POSTURE"  # Not TRANSACTION, but more visible than PLATFORM_AUDIT
    
    # No modifiers applied
    return base_scope


# ============================================================
# EVIDENCE COLLECTION (Enhanced for Future-Proofing)
# ============================================================

def _collect_hipaa_evidence(payload: Dict[str, Any], rule_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect comprehensive HIPAA evidence for audit trails.
    
    Returns:
        Structured evidence with context, rule data, and metadata
    """
    evidence = {
        # Context evidence
        "context": {
            "industry_id": payload.get("industry_id"),
            "action": payload.get("action"),
            "jurisdiction": (payload.get("meta") or {}).get("jurisdiction"),
            "healthcare_context_detected": True,
            "phi_handling_detected": True,
        },
        # Rule-specific evidence
        "rule_data": rule_data,
        # HIPAA-specific information
        "hipaa_info": {},
        # Metadata
        "metadata": {
            "evidence_collected_at": "NOW",  # Would be timestamp in real implementation
        }
    }
    
    # Collect HIPAA-specific information
    hipaa_profile = payload.get("hipaa_profile", {})
    evidence["hipaa_info"] = {
        "entity_type": hipaa_profile.get("entity_type"),
        "phi_categories": hipaa_profile.get("phi_categories", []),
        "patient_count": hipaa_profile.get("patient_count"),
        "breach_history": hipaa_profile.get("breach_history", False),
        "compliance_status": hipaa_profile.get("compliance_status"),
    }
    
    return evidence


# ============================================================
# HIPAA RULE DEFINITIONS (Enhanced with Future Rules)
# ============================================================

# Core HIPAA rules with comprehensive metadata
HIPAA_RULES = [
    # ============================================================
    # PRIVACY RULE (Subpart E)
    # ============================================================
    {
        "article": "45 CFR §164.502(a)",
        "title": "Uses and Disclosures - General Rules",
        "description": "PHI may only be used/disclosed as permitted by Privacy Rule.",
        "field": "handles_phi",
        "severity": "HIGH",
        "rule_id": "HIPAA_164_502A_PHI_HANDLING",
        "enforcement_scope_default": "POSTURE",
        "future_proof_notes": "Core Privacy Rule requirement - must identify all PHI uses/disclosures.",
        "evidence_fields": ["hipaa_profile.handles_phi", "hipaa_profile.phi_use_cases"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "45 CFR §164.502(b)",
        "title": "Minimum Necessary Standard",
        "description": "Use/disclose only minimum PHI necessary to accomplish purpose.",
        "field": "minimum_necessary",
        "severity": "HIGH",
        "rule_id": "HIPAA_164_502B_MIN_NECESSARY",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Role-based access, data minimization, need-to-know principles.",
        "evidence_fields": ["hipaa_profile.minimum_necessary", "hipaa_profile.access_controls"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "45 CFR §164.504(e)",
        "title": "Business Associate Agreements",
        "description": "BAAs required with all third parties handling PHI.",
        "field": "business_associate_agreement",
        "severity": "HIGH",
        "rule_id": "HIPAA_164_504E_BAA",
        "enforcement_scope_default": "POSTURE",
        "future_proof_notes": "Omnibus Rule made BAs directly liable. Must include specific provisions.",
        "evidence_fields": ["hipaa_profile.business_associate_agreement", "hipaa_profile.ba_count"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "45 CFR §164.524",
        "title": "Access to PHI - Individual Rights",
        "description": "Individuals have right to access/inspect/copy their PHI.",
        "field": "individual_access_rights",
        "severity": "MEDIUM",
        "rule_id": "HIPAA_164_524_ACCESS_RIGHTS",
        "enforcement_scope_default": "POSTURE",
        "future_proof_notes": "30-day response requirement. May charge reasonable fee.",
        "evidence_fields": ["hipaa_profile.individual_access_rights", "hipaa_profile.access_response_time"],
        "compliance_level": "REQUIRED",
        "future_implementation": True,
    },
    {
        "article": "45 CFR §164.526",
        "title": "Amendment of PHI",
        "description": "Individuals may request amendment of inaccurate/incomplete PHI.",
        "field": "phi_amendment_process",
        "severity": "MEDIUM",
        "rule_id": "HIPAA_164_526_AMENDMENT",
        "enforcement_scope_default": "POSTURE",
        "future_proof_notes": "60-day response requirement. Must append disagreement statement if denying.",
        "evidence_fields": ["hipaa_profile.phi_amendment_process", "hipaa_profile.amendment_response_time"],
        "compliance_level": "REQUIRED",
        "future_implementation": True,
    },
    
    # ============================================================
    # SECURITY RULE (Subpart C)
    # ============================================================
    {
        "article": "45 CFR §164.308(a)(1)(ii)(A)",
        "title": "Security Risk Assessment",
        "description": "Conduct accurate and thorough risk assessment of PHI security risks.",
        "field": "risk_assessment_current",
        "severity": "HIGH",
        "rule_id": "HIPAA_164_308_A1_SECURITY_ASSESSMENT",
        "enforcement_scope_default": "POSTURE",
        "future_proof_notes": "Required annually. Must address all ePHI creation, receipt, storage, transmission.",
        "evidence_fields": ["hipaa_profile.risk_assessment_current", "hipaa_profile.last_risk_assessment_date"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "45 CFR §164.308(a)(3)(i)",
        "title": "Workforce Security",
        "description": "Implement policies/procedures to ensure workforce appropriately uses ePHI.",
        "field": "workforce_training_current",
        "severity": "HIGH",
        "rule_id": "HIPAA_164_308_A3_WORKFORCE_SECURITY",
        "enforcement_scope_default": "POSTURE",
        "future_proof_notes": "Annual training required. Must document completion.",
        "evidence_fields": ["hipaa_profile.workforce_training_current", "hipaa_profile.last_training_date"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "45 CFR §164.308(a)(7)(i)",
        "title": "Contingency Plan",
        "description": "Establish contingency plans for responding to emergencies.",
        "field": "contingency_plan_tested",
        "severity": "HIGH",
        "rule_id": "HIPAA_164_308_A7_CONTINGENCY_PLAN",
        "enforcement_scope_default": "POSTURE",
        "future_proof_notes": "Must include data backup, disaster recovery, emergency mode operations.",
        "evidence_fields": ["hipaa_profile.contingency_plan_tested", "hipaa_profile.last_dr_test_date"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "45 CFR §164.312(a)(1)",
        "title": "Access Control",
        "description": "Implement technical policies/procedures to allow access only to authorized persons.",
        "field": "access_controls",
        "severity": "CRITICAL",
        "rule_id": "HIPAA_164_312_A1_ACCESS_CONTROL",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Must include unique user identification, emergency access, automatic logoff.",
        "evidence_fields": ["hipaa_profile.access_controls", "hipaa_profile.authentication_mechanism"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "45 CFR §164.312(b)",
        "title": "Audit Controls",
        "description": "Implement hardware/software/procedural mechanisms to record and examine activity.",
        "field": "audit_logs",
        "severity": "HIGH",
        "rule_id": "HIPAA_164_312_B_AUDIT_CONTROLS",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Must log all PHI access, modifications, deletions. Retain logs for 6 years.",
        "evidence_fields": ["hipaa_profile.audit_logs", "hipaa_profile.log_retention_period"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "45 CFR §164.312(e)(1)",
        "title": "Transmission Security",
        "description": "Implement technical security measures to guard against unauthorized access during transmission.",
        "field": "data_encryption",
        "severity": "CRITICAL",
        "rule_id": "HIPAA_164_312_E1_TRANSMISSION_SECURITY",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Must encrypt ePHI in transit. TLS 1.2+ recommended.",
        "evidence_fields": ["hipaa_profile.data_encryption", "hipaa_profile.encryption_protocol"],
        "compliance_level": "ADDRESSABLE",
    },
    {
        "article": "45 CFR §164.310(c)",
        "title": "Device and Media Controls",
        "description": "Implement policies/procedures for final disposition of ePHI and hardware/media.",
        "field": "physical_safeguards",
        "severity": "MEDIUM",
        "rule_id": "HIPAA_164_310_C_DEVICE_CONTROLS",
        "enforcement_scope_default": "POSTURE",
        "future_proof_notes": "Must include disposal, media reuse, accountability, data backup.",
        "evidence_fields": ["hipaa_profile.physical_safeguards", "hipaa_profile.secure_disposal"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # BREACH NOTIFICATION RULE (Subpart D)
    # ============================================================
    {
        "article": "45 CFR §164.404",
        "title": "Individual Breach Notification",
        "description": "Notify individuals of breach of unsecured PHI.",
        "field": "breach_notification",
        "severity": "CRITICAL",
        "rule_id": "HIPAA_164_404_BREACH_NOTIFICATION",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Must notify within 60 days of discovery. HHS annual report required.",
        "evidence_fields": ["hipaa_profile.breach_notification", "hipaa_profile.notification_procedures"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "45 CFR §164.410",
        "title": "HHS Secretary Notification",
        "description": "Notify HHS Secretary of breaches affecting 500+ individuals.",
        "field": "hhs_notification_procedures",
        "severity": "CRITICAL",
        "rule_id": "HIPAA_164_410_HHS_NOTIFICATION",
        "enforcement_scope_default": "SUPERVISORY",
        "future_proof_notes": "Immediate notification for 500+, annual for smaller breaches.",
        "evidence_fields": ["hipaa_profile.hhs_notification_procedures", "hipaa_profile.last_hhs_report"],
        "compliance_level": "REQUIRED",
        "future_implementation": True,
    },
    
    # ============================================================
    # HITECH ACT PROVISIONS (Future Implementation)
    # ============================================================
    {
        "article": "HITECH §13402",
        "title": "Tiered Civil Monetary Penalties",
        "description": "HITECH established tiered penalties based on violation culpability.",
        "field": "hitech_compliance",
        "severity": "HIGH",
        "rule_id": "HITECH_13402_TIERED_PENALTIES",
        "enforcement_scope_default": "SUPERVISORY",
        "future_proof_notes": "Penalties range from $100-$1.5M per violation category.",
        "evidence_fields": ["hipaa_profile.hitech_compliance", "hipaa_profile.penalty_awareness"],
        "compliance_level": "REQUIRED",
        "future_implementation": True,
    },
    {
        "article": "HITECH §13410",
        "title": "Enforcement Through State Attorneys General",
        "description": "State AGs may bring civil actions for HIPAA violations affecting residents.",
        "field": "state_ag_compliance",
        "severity": "HIGH",
        "rule_id": "HITECH_13410_STATE_ENFORCEMENT",
        "enforcement_scope_default": "SUPERVISORY",
        "future_proof_notes": "Expanded enforcement authority to states.",
        "evidence_fields": ["hipaa_profile.state_ag_compliance"],
        "compliance_level": "REQUIRED",
        "future_implementation": True,
    },
    
    # ============================================================
    # GENETIC INFORMATION NONDISCRIMINATION ACT (GINA)
    # ============================================================
    {
        "article": "GINA Title I",
        "title": "Genetic Information Nondiscrimination",
        "description": "Genetic information is PHI with special protections under GINA.",
        "field": "genetic_info_protections",
        "severity": "HIGH",
        "rule_id": "GINA_TITLE_I_GENETIC_INFO",
        "enforcement_scope_default": "POSTURE",
        "future_proof_notes": "Genetic information cannot be used for underwriting or employment decisions.",
        "evidence_fields": ["hipaa_profile.genetic_info_protections", "hipaa_profile.gina_compliance"],
        "compliance_level": "REQUIRED",
        "future_implementation": True,
    },
]


# ============================================================
# MAIN EVALUATION FUNCTION (Future-Proof Architecture)
# ============================================================

def evaluate_hipaa_rules(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Future-proof HIPAA evaluation with comprehensive context gating.
    
    Features:
    1. Multi-method healthcare context detection
    2. PHI handling detection
    3. Covered Entity vs Business Associate determination
    4. Jurisdiction and action filtering
    5. Enhanced enforcement scope resolution
    6. Comprehensive evidence collection
    7. Detailed context tracking
    8. Future rule support
    
    Returns:
        (policies, summary)
        - policies: List with enforcement_scope, evidence, and context
        - summary: Aggregate statistics with detailed context info
    """
    policies: List[Dict[str, Any]] = []
    
    # ============================================================
    # FUTURE-PROOF: CONTEXT GATING DECISION
    # ============================================================
    should_evaluate, evaluation_reason, context_evidence = _should_evaluate_hipaa(payload)
    
    if not should_evaluate:
        # HIPAA doesn't apply to this context - return early with explanation
        summary = {
            "total_rules": 0,
            "passed": 0,
            "failed": 0,
            "blocking_failures": 0,
            "regime": "HIPAA",
            "context_gated": True,
            "evaluation_decision": evaluation_reason,
            "context_evidence": context_evidence,
            "notes": f"HIPAA evaluation skipped: {evaluation_reason}"
        }
        return policies, summary
    
    # ============================================================
    # CONTEXT INFORMATION COLLECTION
    # ============================================================
    entity_type, entity_evidence = _determine_entity_type(payload)
    breach_severity, breach_evidence = _classify_breach_severity(payload)
    risk_indicators = payload.get("risk_indicators", {})
    hipaa_profile = payload.get("hipaa_profile", {}) or {}
    
    # ============================================================
    # RULE EVALUATION (Enhanced with Evidence Collection)
    # ============================================================
    
    evaluation_errors = []
    
    for rule_def in HIPAA_RULES:
        # Skip future implementation rules if not ready
        if rule_def.get("future_implementation") and not hipaa_profile.get("enable_future_rules"):
            continue
        
        # Check if rule applies to this entity type
        compliance_level = rule_def.get("compliance_level", "REQUIRED")
        if compliance_level == "REQUIRED_FOR_COVERED_ENTITY" and entity_type != "COVERED_ENTITY":
            continue
        
        try:
            # Check if the required field exists and is compliant
            field_value = hipaa_profile.get(rule_def["field"])
            
            # Determine status based on field value
            if field_value is False:
                status = "VIOLATED"
            elif field_value is True:
                status = "SATISFIED"
            elif field_value is None:
                # Missing field - determine based on rule type
                if compliance_level == "REQUIRED":
                    status = "VIOLATED"  # Required fields must be present
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
            enforcement_scope = _resolve_hipaa_enforcement_scope(rule_def["article"], payload)
            
            # Determine impact on verdict
            if status == "VIOLATED" and rule_def["severity"] in {"HIGH", "CRITICAL"}:
                impact_on_verdict = "BLOCKING_FAILURE"
            elif status == "VIOLATED":
                impact_on_verdict = "NON_BLOCKING"
            else:
                impact_on_verdict = "COMPLIANT"
            
            # Determine severity based on context
            severity = rule_def["severity"]
            if status == "VIOLATED" and breach_severity in {"MAJOR", "CRITICAL"}:
                # Escalate severity during major breaches
                if severity == "MEDIUM":
                    severity = "HIGH"
                elif severity == "HIGH":
                    severity = "CRITICAL"
            
            # Create policy
            policy = {
                "domain": "US Healthcare Privacy & Security (HIPAA)",
                "regime": "HIPAA",
                "framework": HIPAA_FRAMEWORK,
                "domain_id": "HIPAA",
                "article": rule_def["article"],
                "category": rule_def["title"],
                "title": rule_def["title"],
                "status": status,
                "severity": severity if status == "VIOLATED" else "LOW",
                "enforcement_scope": enforcement_scope,
                "impact_on_verdict": impact_on_verdict,
                "trigger_type": "HIPAA_SAFEGUARD",
                "rule_ids": [rule_def["rule_id"]],
                "notes": rule_def["description"],
                "evidence": _collect_hipaa_evidence(payload, rule_evidence),
                "remediation": (
                    f"Implement {rule_def['title']} controls per HIPAA requirements. "
                    "Document procedures and re-run GNCE after remediation."
                    if status == "VIOLATED" else "No remediation required."
                ),
                "violation_detail": rule_def["description"] if status == "VIOLATED" else "",
                "control_severity": rule_def["severity"],
                # Future-proof metadata
                "metadata": {
                    "compliance_level": compliance_level,
                    "entity_type": entity_type,
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
        "entity_type": entity_type,
        "breach_severity": breach_severity,
        "phi_handling": bool(hipaa_profile),
    }
    
    # Count by safeguard type
    privacy_violations = sum(1 for p in policies 
                           if p["status"] == "VIOLATED" and "164.5" in p["article"])
    security_violations = sum(1 for p in policies 
                            if p["status"] == "VIOLATED" and "164.3" in p["article"])
    breach_violations = sum(1 for p in policies 
                          if p["status"] == "VIOLATED" and "164.4" in p["article"])
    
    # Count by compliance level
    required_violations = sum(1 for p in policies 
                            if p["status"] == "VIOLATED" and 
                            p.get("metadata", {}).get("compliance_level") == "REQUIRED")
    addressable_violations = sum(1 for p in policies 
                               if p["status"] == "VIOLATED" and 
                               p.get("metadata", {}).get("compliance_level") == "ADDRESSABLE")
    
    summary = {
        "total_rules": len(policies),
        "passed": passed,
        "failed": failed,
        "blocking_failures": blocking,
        "regime": "HIPAA",
        "context_gated": False,
        "evaluation_decision": evaluation_reason,
        # Context information
        "context": context_info,
        "context_evidence": context_evidence,
        # Entity information
        "entity_type": entity_type,
        "entity_determination": entity_evidence,
        # Breach information
        "breach_severity": breach_severity,
        "breach_classification": breach_evidence,
        # Violation breakdown
        "privacy_rule_violations": privacy_violations,
        "security_rule_violations": security_violations,
        "breach_notification_violations": breach_violations,
        "administrative_safeguard_violations": sum(1 for p in policies 
                                                 if p["status"] == "VIOLATED" and "164.308" in p["article"]),
        "technical_safeguard_violations": sum(1 for p in policies 
                                            if p["status"] == "VIOLATED" and "164.312" in p["article"]),
        "physical_safeguard_violations": sum(1 for p in policies 
                                           if p["status"] == "VIOLATED" and "164.310" in p["article"]),
        # Compliance level breakdown
        "required_violations": required_violations,
        "addressable_violations": addressable_violations,
        # Scope breakdown
        "transaction_violations": sum(1 for p in policies 
                                    if p["status"] == "VIOLATED" and p.get("enforcement_scope") == "TRANSACTION"),
        "posture_violations": sum(1 for p in policies 
                                 if p["status"] == "VIOLATED" and p.get("enforcement_scope") == "POSTURE"),
        "platform_audit_violations": sum(1 for p in policies 
                                        if p["status"] == "VIOLATED" and p.get("enforcement_scope") == "PLATFORM_AUDIT"),
        # Rule statistics
        "core_rules_evaluated": len([r for r in HIPAA_RULES if not r.get("future_implementation")]),
        "future_rules_available": len([r for r in HIPAA_RULES if r.get("future_implementation")]),
        "future_rules_evaluated": len([r for r in HIPAA_RULES if r.get("future_implementation") 
                                      and hipaa_profile.get("enable_future_rules")]),
        # Error tracking
        "evaluation_errors": evaluation_errors if evaluation_errors else None,
    }
    
    return policies, summary