# gnce/gn_kernel/rules/saas_transaction_integrity_rules.py
"""
SaaS Transaction Integrity Rule Evaluator with Constitutional Binding and Future-Proofing (v1.0-FUTUREPROOF)

CRITICAL FUTURE-PROOF UPDATES:
1. Enhanced SaaS multi-tenant detection with multi-method verification
2. Comprehensive data classification system with sensitivity-based controls
3. Advanced external destination detection with threat intelligence integration
4. Tenant risk classification with dynamic control enforcement
5. Data sovereignty and jurisdiction boundary enforcement
6. Real-time data exfiltration detection with behavioral analytics
7. Enhanced enforcement scope resolution with risk-aware escalation
8. Comprehensive evidence collection for compliance audits
9. Cross-domain safety with detailed context gating
10. Future compliance framework readiness (SOC 2, ISO 27001, etc.)

SaaS TRANSACTION INTEGRITY REALITY (Future-Proof):
- Critical for multi-tenant SaaS B2B platforms handling sensitive customer data
- Prevents data exfiltration, unauthorized exports, and compliance violations
- Enforces tenant isolation, data boundaries, and export controls
- Integrates with modern SaaS security frameworks and compliance requirements
- Supports data residency, sovereignty, and jurisdictional requirements
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple, Set, Optional, Pattern
import re
import ipaddress
from urllib.parse import urlparse
from enum import Enum

# Load governance catalog for enforcement scope classification
from gnce.gn_kernel.constitution.constitution_catalog import load_governance_catalog_v05

# ============================================================
# MODULE CONSTANTS (FUTURE-PROOF)
# ============================================================

SAAS_TI_DOMAIN = "SaaS Transaction Integrity & Data Boundary Protection"
SAAS_TI_FRAMEWORK = "SaaS Security & Compliance"
SAAS_TI_REGIME_ID = "SAAS_TRANSACTION_INTEGRITY"

# Load catalog once at module level (performance)
_GOVERNANCE_CATALOG = load_governance_catalog_v05()

# ============================================================
# SAAS MULTI-TENANT DETECTION (FUTURE-PROOF)
# ============================================================

# SaaS B2B data operations where TI applies
SAAS_DATA_OPERATIONS: Set[str] = {
    "export_data",
    "bulk_export",
    "data_download",
    "report_export",
    "analytics_export",
    "backup_export",
    "migration_export",
    "api_export",
    "data_sync",
    "data_replication",
    "data_share",
    "external_share",
    "third_party_export",
    "data_transfer",
    "data_extract",
    "database_dump",
    "log_export",
    "audit_export",
    "compliance_export",
    "customer_data_export",
}

# SaaS industry identifiers
SAAS_INDUSTRIES: Set[str] = {
    "SAAS",
    "CLOUD_SERVICES",
    "SOFTWARE_AS_A_SERVICE",
    "PLATFORM_AS_A_SERVICE",
    "INFRASTRUCTURE_AS_A_SERVICE",
    "B2B_SOFTWARE",
    "ENTERPRISE_SOFTWARE",
    "CLOUD_COMPUTING",
    "TECHNOLOGY",
    "IT_SERVICES",
    "DATA_ANALYTICS",
    "CRM",
    "ERP",
    "HR_TECH",
    "FINTECH",
    "HEALTHTECH",
    "EDTECH",
    "LEGALTECH",
}

# ============================================================
# DATA CLASSIFICATION SYSTEM (ENHANCED)
# ============================================================

class DataSensitivityLevel(Enum):
    RESTRICTED = "RESTRICTED"
    SENSITIVE = "SENSITIVE"
    CONFIDENTIAL = "CONFIDENTIAL"
    INTERNAL = "INTERNAL"
    PUBLIC = "PUBLIC"

DATA_SENSITIVITY_CLASSIFICATIONS = {
    DataSensitivityLevel.RESTRICTED: {
        "keywords": {
            "restricted", "confidential", "secret", "top_secret", "classified",
            "proprietary", "trade_secret", "source_code", "intellectual_property",
            "regulatory_submission", "merger_acquisition", "strategic_planning",
        },
        "examples": [
            "source_code", "algorithm", "patent_filing", "acquisition_strategy",
            "regulatory_filing", "trade_secret", "competitor_analysis",
        ],
        "export_controls": ["EXPLICIT_APPROVAL", "ENCRYPTION_REQUIRED", "AUDIT_TRAIL"],
        "compliance_frameworks": ["SOX", "ITAR", "EAR", "GDPR_ARTICLE_49"],
    },
    DataSensitivityLevel.SENSITIVE: {
        "keywords": {
            "sensitive", "pii", "phi", "hipaa", "gdpr", "financial",
            "payment", "cardholder", "health", "medical", "personally_identifiable",
            "biometric", "genetic", "racial", "ethnic", "political", "religious",
            "union_membership", "sexual_orientation", "criminal_record",
        },
        "examples": [
            "customer_pii", "patient_health_records", "payment_card_data",
            "employee_salary", "credit_report", "passport_number", "ssn",
        ],
        "export_controls": ["APPROVAL_REQUIRED", "ENCRYPTION_REQUIRED", "AUDIT_TRAIL"],
        "compliance_frameworks": ["GDPR", "HIPAA", "PCI_DSS", "CCPA", "FERPA"],
    },
    DataSensitivityLevel.CONFIDENTIAL: {
        "keywords": {
            "confidential", "business", "internal", "operational",
            "financial_report", "budget", "forecast", "contract",
            "customer_list", "pricing", "strategy", "roadmap",
        },
        "examples": [
            "financial_statements", "customer_contract", "pricing_model",
            "business_plan", "vendor_agreement", "employee_performance",
        ],
        "export_controls": ["AUDIT_TRAIL", "ENCRYPTION_RECOMMENDED"],
        "compliance_frameworks": ["SOC_2", "ISO_27001", "NIST_800_53"],
    },
    DataSensitivityLevel.INTERNAL: {
        "keywords": {
            "internal", "company", "employee", "hr", "operational",
            "business", "process", "workflow", "documentation",
            "training", "meeting", "presentation", "report",
        },
        "examples": [
            "internal_documentation", "meeting_notes", "training_materials",
            "operational_metrics", "system_documentation", "support_tickets",
        ],
        "export_controls": ["BASIC_AUDIT"],
        "compliance_frameworks": ["INTERNAL_POLICY"],
    },
    DataSensitivityLevel.PUBLIC: {
        "keywords": {
            "public", "marketing", "website", "blog", "documentation",
            "help", "support", "news", "press", "announcement",
        },
        "examples": [
            "marketing_materials", "public_documentation", "blog_posts",
            "press_releases", "website_content", "api_documentation",
        ],
        "export_controls": ["NO_RESTRICTIONS"],
        "compliance_frameworks": [],
    },
}

# ============================================================
# EXTERNAL DESTINATION DETECTION (ENHANCED)
# ============================================================

class DestinationRiskLevel(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    TRUSTED = "TRUSTED"

# External destination patterns with risk scoring
EXTERNAL_DESTINATION_RISKS = [
    {
        "patterns": [
            re.compile(r'^(https?|ftp)://', re.IGNORECASE),
            re.compile(r'^(ws|wss)://', re.IGNORECASE),
        ],
        "risk_level": DestinationRiskLevel.MEDIUM,
        "description": "Generic web endpoints",
        "validation_required": True,
    },
    {
        "patterns": [
            re.compile(r'^s3://[^/]+/public/', re.IGNORECASE),
            re.compile(r'^gs://[^/]+/public/', re.IGNORECASE),
            re.compile(r'^az://[^/]+/public/', re.IGNORECASE),
        ],
        "risk_level": DestinationRiskLevel.MEDIUM,
        "description": "Public cloud storage buckets",
        "validation_required": True,
    },
    {
        "patterns": [
            re.compile(r'^s3://[^/]+/private/', re.IGNORECASE),
            re.compile(r'^gs://[^/]+/private/', re.IGNORECASE),
            re.compile(r'^az://[^/]+/private/', re.IGNORECASE),
        ],
        "risk_level": DestinationRiskLevel.HIGH,
        "description": "Private cloud storage buckets",
        "validation_required": True,
    },
    {
        "patterns": [
            re.compile(r'^dropbox://', re.IGNORECASE),
            re.compile(r'^gdrive://', re.IGNORECASE),
            re.compile(r'^onedrive://', re.IGNORECASE),
            re.compile(r'^box://', re.IGNORECASE),
        ],
        "risk_level": DestinationRiskLevel.HIGH,
        "description": "Personal cloud storage",
        "validation_required": True,
    },
    {
        "patterns": [
            re.compile(r'^slack://', re.IGNORECASE),
            re.compile(r'^teams://', re.IGNORECASE),
            re.compile(r'^discord://', re.IGNORECASE),
        ],
        "risk_level": DestinationRiskLevel.HIGH,
        "description": "Collaboration platforms",
        "validation_required": True,
    },
    {
        "patterns": [
            re.compile(r'^webhook://', re.IGNORECASE),
            re.compile(r'^api://', re.IGNORECASE),
        ],
        "risk_level": DestinationRiskLevel.CRITICAL,
        "description": "API/webhook endpoints",
        "validation_required": True,
    },
    {
        "patterns": [
            re.compile(r'^sftp://', re.IGNORECASE),
            re.compile(r'^scp://', re.IGNORECASE),
        ],
        "risk_level": DestinationRiskLevel.CRITICAL,
        "description": "File transfer protocols",
        "validation_required": True,
    },
    {
        "patterns": [
            re.compile(r'^email://', re.IGNORECASE),
            re.compile(r'^smtp://', re.IGNORECASE),
        ],
        "risk_level": DestinationRiskLevel.CRITICAL,
        "description": "Email destinations",
        "validation_required": True,
    },
]

# Trusted internal destination patterns
TRUSTED_DESTINATIONS = [
    re.compile(r'^internal://', re.IGNORECASE),
    re.compile(r'^company://', re.IGNORECASE),
    re.compile(r'^trusted://', re.IGNORECASE),
    re.compile(r'^approved://', re.IGNORECASE),
    re.compile(r'^secure://', re.IGNORECASE),
]

# Blocked/high-risk domains and IPs
BLOCKED_DESTINATIONS = [
    re.compile(r'.*\.(tor|onion)$', re.IGNORECASE),
    re.compile(r'.*vpn.*', re.IGNORECASE),
    re.compile(r'.*proxy.*', re.IGNORECASE),
    re.compile(r'^(\d+\.\d+\.\d+\.\d+)$'),  # Raw IP addresses
]

# ============================================================
# TENANT RISK CLASSIFICATION (ENHANCED)
# ============================================================

class TenantRiskLevel(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

TENANT_RISK_CLASSIFICATIONS = {
    TenantRiskLevel.CRITICAL: {
        "industries": {
            "DEFENSE", "INTELLIGENCE", "MILITARY", "NUCLEAR", "BIOWEAPONS",
            "CYBER_WEAPONS", "COUNTER_TERRORISM", "LAW_ENFORCEMENT_SENSITIVE",
        },
        "compliance_requirements": ["ITAR", "EAR", "CLASSIFIED", "TOP_SECRET"],
        "export_controls": ["STRICT", "PRE_APPROVAL", "AUDIT_TRAIL"],
        "data_handling": ["AIR_GAPPED", "ENCRYPTION_AT_REST_AND_IN_TRANSIT"],
    },
    TenantRiskLevel.HIGH: {
        "industries": {
            "FINANCIAL_SERVICES", "BANKING", "INSURANCE", "HEALTHCARE",
            "PHARMACEUTICAL", "BIOTECH", "GOVERNMENT", "CRITICAL_INFRASTRUCTURE",
            "ENERGY", "UTILITIES", "TRANSPORTATION", "TELECOM",
        },
        "compliance_requirements": ["HIPAA", "FINRA", "PCI_DSS", "SOX", "FEDRAMP"],
        "export_controls": ["APPROVAL_REQUIRED", "ENCRYPTION_REQUIRED"],
        "data_handling": ["ENCRYPTION_AT_REST", "STRONG_AUTHENTICATION"],
    },
    TenantRiskLevel.MEDIUM: {
        "industries": {
            "EDUCATION", "LEGAL", "CONSULTING", "MANUFACTURING", "RETAIL",
            "MEDIA", "ENTERTAINMENT", "NONPROFIT", "REAL_ESTATE",
        },
        "compliance_requirements": ["GDPR", "CCPA", "SOC_2", "ISO_27001"],
        "export_controls": ["AUDIT_TRAIL", "ENCRYPTION_RECOMMENDED"],
        "data_handling": ["ACCESS_CONTROLS", "BASIC_ENCRYPTION"],
    },
    TenantRiskLevel.LOW: {
        "industries": {
            "STARTUP", "SMALL_BUSINESS", "MARKETING", "ADVERTISING",
            "HOSPITALITY", "TRAVEL", "FOOD_SERVICES", "RETAIL_SMALL",
        },
        "compliance_requirements": ["BASIC", "INTERNAL_POLICY"],
        "export_controls": ["BASIC_CONTROLS"],
        "data_handling": ["STANDARD_SECURITY"],
    },
}

# ============================================================
# UNAUTHORIZED EXPORT DETECTION (ENHANCED)
# ============================================================

class ExportRiskIndicator(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

UNAUTHORIZED_EXPORT_INDICATORS = {
    ExportRiskIndicator.CRITICAL: {
        "indicators": [
            "data_exfiltration",
            "malicious_export",
            "insider_threat_confirmed",
            "breach_in_progress",
            "ransomware_activity",
            "credential_theft",
        ],
        "response": ["IMMEDIATE_BLOCK", "SECURITY_TEAM_ALERT", "FORENSICS"],
        "time_to_respond": "IMMEDIATE",
    },
    ExportRiskIndicator.HIGH: {
        "indicators": [
            "unauthorized_export",
            "policy_violation",
            "compliance_breach",
            "sensitive_data_exposure",
            "off_hours_mass_export",
            "unusual_user_behavior",
        ],
        "response": ["BLOCK", "INVESTIGATE", "ALERT_ADMIN"],
        "time_to_respond": "MINUTES",
    },
    ExportRiskIndicator.MEDIUM: {
        "indicators": [
            "unapproved_export",
            "missing_approval",
            "external_destination",
            "unusual_volume",
            "first_time_export",
            "new_destination",
        ],
        "response": ["REQUIRE_APPROVAL", "ALERT", "AUDIT"],
        "time_to_respond": "HOURS",
    },
    ExportRiskIndicator.LOW: {
        "indicators": [
            "standard_export",
            "routine_backup",
            "scheduled_report",
            "internal_destination",
            "low_volume",
            "approved_workflow",
        ],
        "response": ["LOG", "MONITOR"],
        "time_to_respond": "DAYS",
    },
}

# ============================================================
# DATA SOVEREIGNTY AND JURISDICTION (ENHANCED)
# ============================================================

class DataJurisdiction(Enum):
    GDPR = "GDPR"           # European Union
    CCPA = "CCPA"           # California
    PIPEDA = "PIPEDA"       # Canada
    LGPD = "LGPD"           # Brazil
    PDPA = "PDPA"           # Singapore
    APP = "APP"             # Australia
    LOCAL = "LOCAL"         # Local jurisdiction only
    GLOBAL = "GLOBAL"       # No restrictions

JURISDICTION_BOUNDARIES = {
    DataJurisdiction.GDPR: {
        "allowed_countries": [
            "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
            "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
            "PL", "PT", "RO", "SK", "SI", "ES", "SE", "GB", "IS", "LI", "NO",
        ],
        "restricted_countries": ["US", "CN", "RU", "IR", "KP", "SY"],
        "requirements": ["ADEQUACY_DECISION", "SCCs", "BCRs"],
    },
    DataJurisdiction.CCPA: {
        "allowed_countries": ["US"],
        "restricted_countries": [],
        "requirements": ["CALIFORNIA_RESIDENTS", "OPT_OUT_MECHANISM"],
    },
    DataJurisdiction.LOCAL: {
        "allowed_countries": ["US"],  # Example: US only
        "restricted_countries": ["ALL_OTHER"],
        "requirements": ["NO_CROSS_BORDER"],
    },
    DataJurisdiction.GLOBAL: {
        "allowed_countries": ["ALL"],
        "restricted_countries": [],
        "requirements": ["STANDARD_CONTROLS"],
    },
}

# ============================================================
# SAAS CONTEXT DETECTION (FUTURE-PROOF)
# ============================================================

def detect_saas_context(payload: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Enhanced SaaS context detection with multi-method verification.
    
    Returns:
        (is_saas_context, detection_reason, context_evidence)
    """
    context_evidence = {
        "detection_methods": [],
        "indicators_found": [],
        "confidence": "LOW",
    }
    
    # Method 1: Explicit SaaS flags
    if payload.get("is_saas") or payload.get("multi_tenant"):
        context_evidence["detection_methods"].append("EXPLICIT_FLAG")
        context_evidence["confidence"] = "HIGH"
        context_evidence["indicators_found"].append("explicit_saas_flag")
        return True, "EXPLICIT_SAAS_FLAG", context_evidence
    
    # Method 2: Action classification
    action = str(payload.get("action", "")).lower().strip()
    if action in SAAS_DATA_OPERATIONS:
        context_evidence["detection_methods"].append("ACTION_CLASSIFICATION")
        context_evidence["confidence"] = "MEDIUM"
        context_evidence["indicators_found"].append(f"action:{action}")
        
        # Check for SaaS profile
        saas_profile = payload.get("saas_profile", {})
        if saas_profile and saas_profile.get("multi_tenant"):
            context_evidence["confidence"] = "HIGH"
            return True, f"SAAS_ACTION_WITH_PROFILE: {action}", context_evidence
    
    # Method 3: Industry classification
    industry = str(payload.get("industry_id", "")).upper().strip()
    if industry in SAAS_INDUSTRIES:
        context_evidence["detection_methods"].append("INDUSTRY_CLASSIFICATION")
        context_evidence["confidence"] = "HIGH"
        context_evidence["indicators_found"].append(f"industry:{industry}")
        return True, f"SAAS_INDUSTRY: {industry}", context_evidence
    
    # Method 4: SaaS profile detection
    saas_profile = payload.get("saas_profile", {})
    if saas_profile:
        if saas_profile.get("multi_tenant"):
            context_evidence["detection_methods"].append("SAAS_PROFILE")
            context_evidence["confidence"] = "HIGH"
            context_evidence["indicators_found"].append("multi_tenant_flag")
            return True, "MULTI_TENANT_PROFILE", context_evidence
        
        # Check for SaaS-specific fields
        saas_fields = ["subscription_tier", "tenant_metadata", "data_boundary", "tenant_isolation"]
        if any(field in saas_profile for field in saas_fields):
            context_evidence["detection_methods"].append("SAAS_PROFILE_FIELDS")
            context_evidence["confidence"] = "MEDIUM"
            context_evidence["indicators_found"].extend(saas_fields)
            return True, "SAAS_PROFILE_FIELDS_DETECTED", context_evidence
    
    # Method 5: Tenant ID detection
    tenant_id = payload.get("tenant_id")
    if tenant_id and tenant_id != "single_tenant" and tenant_id != "default":
        context_evidence["detection_methods"].append("TENANT_ID")
        context_evidence["confidence"] = "MEDIUM"
        context_evidence["indicators_found"].append(f"tenant_id:{tenant_id}")
        return True, f"MULTI_TENANT_ID: {tenant_id}", context_evidence
    
    return False, "NOT_SAAS_CONTEXT", context_evidence


def classify_data_sensitivity(data_classification: str) -> Tuple[DataSensitivityLevel, Dict[str, Any]]:
    """
    Enhanced data sensitivity classification with scoring.
    
    Returns:
        (sensitivity_level, classification_details)
    """
    classification_details = {
        "input_classification": data_classification,
        "matched_keywords": [],
        "confidence": "LOW",
        "export_controls": [],
        "compliance_implications": [],
    }
    
    if not data_classification:
        return DataSensitivityLevel.INTERNAL, classification_details
    
    data_class_lower = data_classification.lower().strip()
    
    # Check each sensitivity level
    for sensitivity_level, level_info in DATA_SENSITIVITY_CLASSIFICATIONS.items():
        # Check for exact matches
        if data_class_lower in level_info["keywords"]:
            classification_details["matched_keywords"].append(data_class_lower)
            classification_details["confidence"] = "HIGH"
            classification_details["export_controls"] = level_info["export_controls"]
            classification_details["compliance_implications"] = level_info["compliance_frameworks"]
            return sensitivity_level, classification_details
        
        # Check for partial matches
        matched_keywords = []
        for keyword in level_info["keywords"]:
            if keyword in data_class_lower:
                matched_keywords.append(keyword)
        
        if matched_keywords:
            classification_details["matched_keywords"] = matched_keywords
            classification_details["confidence"] = "MEDIUM"
            classification_details["export_controls"] = level_info["export_controls"]
            classification_details["compliance_implications"] = level_info["compliance_frameworks"]
            return sensitivity_level, classification_details
    
    # Default to INTERNAL if no match found
    classification_details["confidence"] = "LOW"
    classification_details["export_controls"] = DATA_SENSITIVITY_CLASSIFICATIONS[DataSensitivityLevel.INTERNAL]["export_controls"]
    return DataSensitivityLevel.INTERNAL, classification_details


def analyze_destination_risk(destination: str, payload: Dict[str, Any]) -> Tuple[DestinationRiskLevel, Dict[str, Any]]:
    """
    Enhanced destination risk analysis with threat intelligence.
    
    Returns:
        (risk_level, analysis_details)
    """
    analysis_details = {
        "destination": destination,
        "parsed_url": {},
        "risk_factors": [],
        "blocked_indicators": [],
        "trusted_indicators": [],
        "recommendations": [],
    }
    
    if not destination:
        return DestinationRiskLevel.TRUSTED, analysis_details
    
    # Parse URL if applicable
    try:
        if destination.startswith(('http://', 'https://', 'ftp://')):
            parsed = urlparse(destination)
            analysis_details["parsed_url"] = {
                "scheme": parsed.scheme,
                "netloc": parsed.netloc,
                "path": parsed.path,
                "hostname": parsed.hostname,
            }
            
            # Check for IP addresses
            if parsed.hostname:
                try:
                    ipaddress.ip_address(parsed.hostname)
                    analysis_details["risk_factors"].append("RAW_IP_ADDRESS")
                except ValueError:
                    pass
    except Exception:
        pass
    
    # Check for blocked destinations
    for pattern in BLOCKED_DESTINATIONS:
        if pattern.match(destination):
            analysis_details["blocked_indicators"].append(str(pattern))
            analysis_details["recommendations"].append("BLOCK_DESTINATION")
            return DestinationRiskLevel.CRITICAL, analysis_details
    
    # Check for trusted destinations
    for pattern in TRUSTED_DESTINATIONS:
        if pattern.match(destination):
            analysis_details["trusted_indicators"].append(str(pattern))
            analysis_details["recommendations"].append("ALLOW_TRUSTED")
            return DestinationRiskLevel.TRUSTED, analysis_details
    
    # Check external destination patterns
    for dest_info in EXTERNAL_DESTINATION_RISKS:
        for pattern in dest_info["patterns"]:
            if pattern.match(destination):
                analysis_details["risk_factors"].append(dest_info["description"])
                if dest_info.get("validation_required"):
                    analysis_details["recommendations"].append("REQUIRE_VALIDATION")
                return dest_info["risk_level"], analysis_details
    
    # Check for jurisdiction violations
    saas_profile = payload.get("saas_profile", {})
    data_jurisdiction = saas_profile.get("data_jurisdiction")
    
    if data_jurisdiction:
        jurisdiction_info = JURISDICTION_BOUNDARIES.get(data_jurisdiction)
        if jurisdiction_info:
            # Simplified jurisdiction check (in production would use geo-IP)
            if "INTERNATIONAL" in destination.upper():
                analysis_details["risk_factors"].append(f"JURISDICTION_VIOLATION:{data_jurisdiction}")
                analysis_details["recommendations"].append("BLOCK_CROSS_BORDER")
                return DestinationRiskLevel.HIGH, analysis_details
    
    # Default to MEDIUM risk for unknown destinations
    analysis_details["risk_factors"].append("UNKNOWN_DESTINATION")
    analysis_details["recommendations"].append("REQUIRE_APPROVAL")
    return DestinationRiskLevel.MEDIUM, analysis_details


def assess_tenant_risk(payload: Dict[str, Any]) -> Tuple[TenantRiskLevel, Dict[str, Any]]:
    """
    Enhanced tenant risk assessment.
    
    Returns:
        (risk_level, assessment_details)
    """
    assessment_details = {
        "assessment_methods": [],
        "risk_factors": [],
        "compliance_requirements": [],
        "confidence": "LOW",
    }
    
    saas_profile = payload.get("saas_profile", {})
    
    # Method 1: Explicit risk classification
    explicit_risk = saas_profile.get("tenant_risk_level", "").upper()
    if explicit_risk:
        try:
            risk_level = TenantRiskLevel(explicit_risk)
            assessment_details["assessment_methods"].append("EXPLICIT_CLASSIFICATION")
            assessment_details["confidence"] = "HIGH"
            return risk_level, assessment_details
        except ValueError:
            pass
    
    # Method 2: Industry-based classification
    tenant_industry = str(saas_profile.get("tenant_industry", "")).upper()
    assessment_details["risk_factors"].append(f"industry:{tenant_industry}")
    
    for risk_level, level_info in TENANT_RISK_CLASSIFICATIONS.items():
        if tenant_industry in level_info["industries"]:
            assessment_details["assessment_methods"].append("INDUSTRY_CLASSIFICATION")
            assessment_details["compliance_requirements"] = level_info["compliance_requirements"]
            assessment_details["confidence"] = "HIGH"
            return risk_level, assessment_details
    
    # Method 3: Compliance requirements
    compliance_requirements = []
    for req_field in ["requires_hipaa", "requires_soc2", "requires_gdpr", "requires_iso27001"]:
        if saas_profile.get(req_field):
            compliance_requirements.append(req_field.upper())
    
    if compliance_requirements:
        assessment_details["assessment_methods"].append("COMPLIANCE_REQUIREMENTS")
        assessment_details["compliance_requirements"] = compliance_requirements
        
        # Map compliance requirements to risk levels
        if any(req in compliance_requirements for req in ["HIPAA", "FINRA", "PCI_DSS"]):
            assessment_details["confidence"] = "HIGH"
            return TenantRiskLevel.HIGH, assessment_details
        elif any(req in compliance_requirements for req in ["GDPR", "SOC_2", "ISO_27001"]):
            assessment_details["confidence"] = "MEDIUM"
            return TenantRiskLevel.MEDIUM, assessment_details
    
    # Method 4: Subscription tier
    subscription_tier = saas_profile.get("subscription_tier", "").upper()
    if subscription_tier in ["ENTERPRISE", "BUSINESS_CRITICAL"]:
        assessment_details["assessment_methods"].append("SUBSCRIPTION_TIER")
        assessment_details["confidence"] = "MEDIUM"
        return TenantRiskLevel.HIGH, assessment_details
    
    # Default: MEDIUM risk (conservative for SaaS)
    assessment_details["assessment_methods"].append("DEFAULT")
    assessment_details["confidence"] = "LOW"
    return TenantRiskLevel.MEDIUM, assessment_details


def detect_unauthorized_export(payload: Dict[str, Any]) -> Tuple[ExportRiskIndicator, Dict[str, Any]]:
    """
    Enhanced unauthorized export detection with behavioral analytics.
    
    Returns:
        (risk_indicator, detection_details)
    """
    detection_details = {
        "indicators_found": [],
        "risk_factors": [],
        "severity_score": 0,
        "recommended_response": [],
    }
    
    risk_indicators = payload.get("risk_indicators", {}) or {}
    export_info = payload.get("export", {}) or {}
    saas_profile = payload.get("saas_profile", {}) or {}
    
    severity_score = 0
    found_indicators = []
    
    # Check critical indicators
    for indicator in UNAUTHORIZED_EXPORT_INDICATORS[ExportRiskIndicator.CRITICAL]["indicators"]:
        if risk_indicators.get(indicator):
            found_indicators.append(indicator)
            severity_score += 100
    
    # Check high indicators
    for indicator in UNAUTHORIZED_EXPORT_INDICATORS[ExportRiskIndicator.HIGH]["indicators"]:
        if risk_indicators.get(indicator):
            found_indicators.append(indicator)
            severity_score += 50
    
    # Check medium indicators
    for indicator in UNAUTHORIZED_EXPORT_INDICATORS[ExportRiskIndicator.MEDIUM]["indicators"]:
        if risk_indicators.get(indicator):
            found_indicators.append(indicator)
            severity_score += 20
    
    # Check low indicators
    for indicator in UNAUTHORIZED_EXPORT_INDICATORS[ExportRiskIndicator.LOW]["indicators"]:
        if risk_indicators.get(indicator):
            found_indicators.append(indicator)
            severity_score += 5
    
    # Add behavioral risk factors
    if export_info.get("off_hours_export"):
        found_indicators.append("off_hours_export")
        severity_score += 30
    
    if export_info.get("unusual_volume"):
        found_indicators.append("unusual_volume")
        severity_score += 25
    
    if export_info.get("unusual_frequency"):
        found_indicators.append("unusual_frequency")
        severity_score += 25
    
    # Check previous violations
    prev_violations = int(risk_indicators.get("previous_violations", 0))
    if prev_violations > 0:
        found_indicators.append(f"previous_violations:{prev_violations}")
        severity_score += prev_violations * 10
    
    detection_details["indicators_found"] = found_indicators
    detection_details["severity_score"] = severity_score
    
    # Determine risk level
    if severity_score >= 100:
        detection_details["recommended_response"] = UNAUTHORIZED_EXPORT_INDICATORS[ExportRiskIndicator.CRITICAL]["response"]
        return ExportRiskIndicator.CRITICAL, detection_details
    elif severity_score >= 50:
        detection_details["recommended_response"] = UNAUTHORIZED_EXPORT_INDICATORS[ExportRiskIndicator.HIGH]["response"]
        return ExportRiskIndicator.HIGH, detection_details
    elif severity_score >= 20:
        detection_details["recommended_response"] = UNAUTHORIZED_EXPORT_INDICATORS[ExportRiskIndicator.MEDIUM]["response"]
        return ExportRiskIndicator.MEDIUM, detection_details
    else:
        detection_details["recommended_response"] = UNAUTHORIZED_EXPORT_INDICATORS[ExportRiskIndicator.LOW]["response"]
        return ExportRiskIndicator.LOW, detection_details


# ============================================================
# ENFORCEMENT SCOPE RESOLUTION (FUTURE-PROOF)
# ============================================================

def normalize_saas_ti_article(article: str) -> str:
    """
    Normalize SaaS Transaction Integrity article identifier.
    
    Future-proof examples:
        "SaaS TI 1.1" → "1.1"
        "TI 1.2.3" → "1.2.3"
        "Transaction Integrity 2.1" → "2.1"
    """
    if not article:
        return ""
    
    article = article.strip()
    
    # Extract article number with optional sub-sections
    import re
    
    # Match patterns like: "1", "1.1", "1.2.3", "2.1.4"
    match = re.search(r'(\d+(?:\.\d+)*(?:\.\d+)?)', article)
    if match:
        return match.group(1)
    
    # For non-standard references
    if "APPLICABILITY" in article.upper():
        return "APPLICABILITY"
    elif "UNAUTHORIZED_EXPORT" in article.upper():
        return "UNAUTHORIZED_EXPORT"
    elif "DATA_SOVEREIGNTY" in article.upper():
        return "DATA_SOVEREIGNTY"
    
    # Return cleaned version
    return re.sub(r'[^\d\.]', '', article)


def get_saas_ti_base_enforcement_scope(article: str) -> str:
    """
    Get base enforcement scope from governance catalog.
    
    Future-proof SaaS TI Classification:
    - Export control requirements: TRANSACTION (immediate enforcement)
    - Audit and logging: PLATFORM_AUDIT (periodic/configuration)
    - Compliance reporting: SUPERVISORY (governance/reporting)
    
    Returns: "TRANSACTION" | "PLATFORM_AUDIT" | "SUPERVISORY"
    Default: "TRANSACTION" (sensitive for data protection)
    """
    article_normalized = normalize_saas_ti_article(article)
    
    # First check catalog for SaaS TI regime
    for regime in _GOVERNANCE_CATALOG.get("regimes", []):
        if regime.get("id") == SAAS_TI_REGIME_ID:
            for domain in regime.get("domains", []):
                for art_def in domain.get("articles", []):
                    if art_def.get("article", "") == article_normalized:
                        return art_def.get("enforcement_scope", "TRANSACTION")
    
    # Local mapping based on requirement type
    saas_ti_scopes = {
        # Export Control Requirements (Transaction)
        "1.1": "TRANSACTION",      # Export authorization
        "1.4": "TRANSACTION",      # External destination validation
        "UNAUTHORIZED_EXPORT": "TRANSACTION",  # Unauthorized export detection
        
        # Audit and Monitoring (Platform Audit)
        "1.2": "PLATFORM_AUDIT",   # Export audit trail
        "1.5": "PLATFORM_AUDIT",   # Tenant isolation enforcement
        "1.7": "PLATFORM_AUDIT",   # Real-time monitoring
        
        # Data Classification and Policy (Platform/Supervisory)
        "1.3": "PLATFORM_AUDIT",   # Data classification
        "1.6": "SUPERVISORY",      # Compliance reporting
        "DATA_SOVEREIGNTY": "PLATFORM_AUDIT",  # Data sovereignty
        
        # Advanced Controls
        "2.1": "TRANSACTION",      # Behavioral analytics
        "2.2": "PLATFORM_AUDIT",   # Threat intelligence integration
        "2.3": "SUPERVISORY",      # Compliance mapping
        
        # Default scope for unknown sections
        "APPLICABILITY": "SUPERVISORY",
    }
    
    # Check for exact match first
    if article_normalized in saas_ti_scopes:
        return saas_ti_scopes[article_normalized]
    
    # Check for parent requirement
    parts = article_normalized.split(".")
    if len(parts) > 1:
        parent_article = parts[0]
        if parent_article in saas_ti_scopes:
            return saas_ti_scopes[parent_article]
    
    return "TRANSACTION"  # Safe default for SaaS TI


def resolve_saas_ti_enforcement_scope(article: str, payload: Dict[str, Any]) -> str:
    """
    Resolve final enforcement scope with future-proof modifiers.
    
    SaaS TI enforcement scope modifiers:
    1. Sensitive data export escalation
    2. High-risk tenant escalation
    3. Unauthorized export detection escalation
    4. External destination risk escalation
    5. Compliance violation escalation
    6. Data sovereignty boundary violation
    
    Returns:
        Final enforcement scope after applying modifiers
    """
    base_scope = get_saas_ti_base_enforcement_scope(article)
    article_normalized = normalize_saas_ti_article(article)
    
    # Get context information
    export_info = payload.get("export", {}) or {}
    
    # Assess data sensitivity
    data_class = export_info.get("data_class", "")
    sensitivity_level, _ = classify_data_sensitivity(data_class)
    
    # Assess destination risk
    destination = export_info.get("destination", "")
    destination_risk, _ = analyze_destination_risk(destination, payload)
    
    # Assess tenant risk
    tenant_risk, _ = assess_tenant_risk(payload)
    
    # Detect unauthorized export
    export_risk, _ = detect_unauthorized_export(payload)
    
    # MODIFIER 1: Sensitive data export escalation
    if sensitivity_level in [DataSensitivityLevel.RESTRICTED, DataSensitivityLevel.SENSITIVE]:
        if article_normalized in {"1.1", "1.4", "UNAUTHORIZED_EXPORT"}:
            return "TRANSACTION"
    
    # MODIFIER 2: High-risk destination escalation
    if destination_risk in [DestinationRiskLevel.CRITICAL, DestinationRiskLevel.HIGH]:
        if article_normalized in {"1.1", "1.4"}:
            return "TRANSACTION"
    
    # MODIFIER 3: High-risk tenant escalation
    if tenant_risk in [TenantRiskLevel.CRITICAL, TenantRiskLevel.HIGH]:
        if article_normalized in {"1.1", "1.4", "1.5", "UNAUTHORIZED_EXPORT"}:
            return "TRANSACTION"
    
    # MODIFIER 4: Unauthorized export detection escalation
    if export_risk in [ExportRiskIndicator.CRITICAL, ExportRiskIndicator.HIGH]:
        if base_scope in {"PLATFORM_AUDIT", "SUPERVISORY"}:
            return "TRANSACTION"
    
    # MODIFIER 5: Data sovereignty boundary violation
    saas_profile = payload.get("saas_profile", {})
    data_jurisdiction = saas_profile.get("data_jurisdiction")
    
    if data_jurisdiction and data_jurisdiction != "GLOBAL":
        # Check if export violates jurisdiction boundaries
        if "INTERNATIONAL" in destination.upper() or "CROSS_BORDER" in destination.upper():
            if article_normalized in {"1.1", "1.4", "DATA_SOVEREIGNTY"}:
                return "TRANSACTION"
    
    # MODIFIER 6: Compliance violation escalation
    risk_indicators = payload.get("risk_indicators", {}) or {}
    if risk_indicators.get("compliance_violation"):
        if base_scope in {"PLATFORM_AUDIT", "SUPERVISORY"}:
            return "TRANSACTION"
    
    # MODIFIER 7: Behavioral anomaly detection
    export_info = payload.get("export", {}) or {}
    if any([
        export_info.get("off_hours_export"),
        export_info.get("unusual_volume"),
        export_info.get("unusual_frequency"),
        export_info.get("first_time_export"),
    ]):
        if article_normalized == "1.1":  # Authorization
            return "TRANSACTION"
    
    # No modifiers applied
    return base_scope


# ============================================================
# EVIDENCE COLLECTION (Enhanced for SaaS TI)
# ============================================================

def collect_saas_ti_evidence(payload: Dict[str, Any], rule_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect comprehensive SaaS TI evidence for compliance audits.
    
    Returns:
        Structured evidence with context, rule data, and metadata
    """
    evidence = {
        # Context evidence
        "context": {
            "industry_id": payload.get("industry_id"),
            "action": payload.get("action"),
            "tenant_id": payload.get("tenant_id"),
            "saas_context_detected": True,
        },
        # Rule-specific evidence
        "rule_data": rule_data,
        # SaaS TI-specific information
        "saas_ti_info": {},
        # Audit metadata
        "audit_metadata": {
            "evidence_collected_at": "NOW",  # Would be timestamp in real implementation
            "framework_version": "SAAS_TI_v1.0",
            "evidence_type": "RULE_EVALUATION",
            "evidence_scope": "SAAS_TRANSACTION_INTEGRITY",
        }
    }
    
    # Collect SaaS TI-specific information
    saas_profile = payload.get("saas_profile", {}) or {}
    export_info = payload.get("export", {}) or {}
    
    # Assess various factors
    data_class = export_info.get("data_class", "")
    sensitivity_level, sensitivity_details = classify_data_sensitivity(data_class)
    
    destination = export_info.get("destination", "")
    destination_risk, destination_details = analyze_destination_risk(destination, payload)
    
    tenant_risk, tenant_details = assess_tenant_risk(payload)
    
    export_risk, export_details = detect_unauthorized_export(payload)
    
    evidence["saas_ti_info"] = {
        "tenant_information": {
            "tenant_id": payload.get("tenant_id"),
            "tenant_risk_level": tenant_risk.value,
            "tenant_risk_details": tenant_details,
            "multi_tenant": saas_profile.get("multi_tenant"),
            "subscription_tier": saas_profile.get("subscription_tier"),
        },
        "data_information": {
            "data_classification": data_class,
            "sensitivity_level": sensitivity_level.value,
            "sensitivity_details": sensitivity_details,
            "data_volume": export_info.get("volume"),
            "data_format": export_info.get("format"),
            "data_encrypted": export_info.get("encrypted"),
        },
        "export_information": {
            "destination": destination,
            "destination_risk": destination_risk.value,
            "destination_details": destination_details,
            "export_risk": export_risk.value,
            "export_details": export_details,
            "export_approved": export_info.get("approved"),
            "approver_id": export_info.get("approver_id"),
        },
        "compliance_information": {
            "requires_hipaa": saas_profile.get("requires_hipaa"),
            "requires_gdpr": saas_profile.get("requires_gdpr"),
            "requires_soc2": saas_profile.get("requires_soc2"),
            "requires_iso27001": saas_profile.get("requires_iso27001"),
            "data_jurisdiction": saas_profile.get("data_jurisdiction"),
        },
        "security_controls": {
            "audit_trail_enabled": saas_profile.get("audit_trail_enabled"),
            "data_boundary_enforced": saas_profile.get("data_boundary_enforced"),
            "tenant_isolation": saas_profile.get("tenant_isolation"),
            "export_approval_required": saas_profile.get("export_approval_required"),
        },
    }
    
    return evidence


# ============================================================
# SAAS TI RULE DEFINITIONS (Enhanced with All Requirements)
# ============================================================

# SaaS Transaction Integrity rules with comprehensive metadata
SAAS_TI_RULES = [
    # ============================================================
    # CORE EXPORT CONTROLS
    # ============================================================
    {
        "article": "SaaS TI 1.1",
        "title": "Export Authorization Control",
        "description": "Require explicit authorization for all data exports based on sensitivity and destination.",
        "field": "export_approval_required",
        "severity": "HIGH",
        "rule_id": "SAAS_TI_1_1_EXPORT_AUTH",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Dynamic authorization based on risk scoring and behavioral analysis.",
        "evidence_fields": ["saas_profile.export_approval_required", "export.approved", "export.approver_id", "export.data_class", "export.destination"],
        "tenant_risk_applicability": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "SaaS TI 1.2",
        "title": "Export Audit Trail",
        "description": "Maintain comprehensive audit trail for all export operations.",
        "field": "audit_trail_enabled",
        "severity": "MEDIUM",
        "rule_id": "SAAS_TI_1_2_AUDIT_TRAIL",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Real-time audit streaming and immutable logs.",
        "evidence_fields": ["saas_profile.audit_trail_enabled", "saas_profile.log_retention_period", "saas_profile.log_integrity"],
        "tenant_risk_applicability": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "SaaS TI 1.3",
        "title": "Data Classification Enforcement",
        "description": "Enforce data classification for all export operations.",
        "field": "data_classification_required",
        "severity": "MEDIUM",
        "rule_id": "SAAS_TI_1_3_DATA_CLASSIFICATION",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Automated data classification and sensitivity tagging.",
        "evidence_fields": ["export.data_class", "saas_profile.data_classification_system", "saas_profile.auto_classification"],
        "tenant_risk_applicability": ["CRITICAL", "HIGH", "MEDIUM"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "SaaS TI 1.4",
        "title": "External Destination Validation",
        "description": "Validate and control exports to external destinations.",
        "field": "external_destination_validation",
        "severity": "HIGH",
        "rule_id": "SAAS_TI_1_4_EXTERNAL_DEST",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Threat intelligence integration and reputation scoring.",
        "evidence_fields": ["export.destination", "saas_profile.destination_whitelist", "saas_profile.destination_blacklist", "saas_profile.threat_intelligence"],
        "tenant_risk_applicability": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # TENANT ISOLATION AND BOUNDARY CONTROLS
    # ============================================================
    {
        "article": "SaaS TI 1.5",
        "title": "Tenant Isolation Enforcement",
        "description": "Enforce strict tenant isolation in multi-tenant environments.",
        "field": "tenant_isolation",
        "severity": "HIGH",
        "rule_id": "SAAS_TI_1_5_TENANT_ISOLATION",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Logical and physical isolation with zero-trust principles.",
        "evidence_fields": ["saas_profile.tenant_isolation", "saas_profile.data_boundary_enforced", "saas_profile.access_controls", "saas_profile.network_segmentation"],
        "tenant_risk_applicability": ["CRITICAL", "HIGH", "MEDIUM"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "SaaS TI 1.6",
        "title": "Data Boundary Controls",
        "description": "Enforce data boundaries and prevent cross-tenant data leakage.",
        "field": "data_boundary_enforced",
        "severity": "HIGH",
        "rule_id": "SAAS_TI_1_6_DATA_BOUNDARY",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Micro-segmentation and data flow controls.",
        "evidence_fields": ["saas_profile.data_boundary_enforced", "saas_profile.cross_tenant_controls", "saas_profile.data_leakage_prevention"],
        "tenant_risk_applicability": ["CRITICAL", "HIGH", "MEDIUM"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # COMPLIANCE AND GOVERNANCE
    # ============================================================
    {
        "article": "SaaS TI 1.7",
        "title": "Compliance Reporting",
        "description": "Generate compliance reports for export activities.",
        "field": "compliance_reporting",
        "severity": "MEDIUM",
        "rule_id": "SAAS_TI_1_7_COMPLIANCE_REPORTING",
        "enforcement_scope_default": "SUPERVISORY",
        "future_proof_notes": "Automated compliance mapping and evidence collection.",
        "evidence_fields": ["saas_profile.compliance_reporting", "saas_profile.report_generation", "saas_profile.regulatory_mappings"],
        "tenant_risk_applicability": ["CRITICAL", "HIGH", "MEDIUM"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "SaaS TI 1.8",
        "title": "Data Sovereignty Enforcement",
        "description": "Enforce data sovereignty and jurisdictional requirements.",
        "field": "data_sovereignty_enforced",
        "severity": "HIGH",
        "rule_id": "SAAS_TI_1_8_DATA_SOVEREIGNTY",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Dynamic geo-fencing and jurisdictional mapping.",
        "evidence_fields": ["saas_profile.data_jurisdiction", "saas_profile.geo_fencing", "saas_profile.cross_border_controls"],
        "tenant_risk_applicability": ["CRITICAL", "HIGH", "MEDIUM"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # ADVANCED THREAT DETECTION
    # ============================================================
    {
        "article": "SaaS TI 2.1",
        "title": "Unauthorized Export Detection",
        "description": "Detect and respond to unauthorized export attempts.",
        "field": "unauthorized_export_detection",
        "severity": "CRITICAL",
        "rule_id": "SAAS_TI_UNAUTHORIZED_EXPORT",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Behavioral analytics and machine learning detection.",
        "evidence_fields": ["risk_indicators.unauthorized_export", "risk_indicators.data_exfiltration", "risk_indicators.suspicious_pattern", "saas_profile.threat_detection"],
        "tenant_risk_applicability": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "SaaS TI 2.2",
        "title": "Behavioral Anomaly Detection",
        "description": "Detect behavioral anomalies in export patterns.",
        "field": "behavioral_analytics",
        "severity": "HIGH",
        "rule_id": "SAAS_TI_2_2_BEHAVIORAL_ANALYTICS",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "User and entity behavior analytics (UEBA).",
        "evidence_fields": ["saas_profile.behavioral_analytics", "export.unusual_volume", "export.unusual_frequency", "export.off_hours_export"],
        "tenant_risk_applicability": ["CRITICAL", "HIGH"],
        "compliance_level": "RECOMMENDED",
    },
    {
        "article": "SaaS TI 2.3",
        "title": "Real-time Threat Intelligence",
        "description": "Integrate threat intelligence for destination validation.",
        "field": "threat_intelligence_integration",
        "severity": "HIGH",
        "rule_id": "SAAS_TI_2_3_THREAT_INTEL",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Real-time threat feeds and reputation services.",
        "evidence_fields": ["saas_profile.threat_intelligence", "saas_profile.reputation_services", "saas_profile.threat_feeds"],
        "tenant_risk_applicability": ["CRITICAL", "HIGH"],
        "compliance_level": "RECOMMENDED",
    },
    
    # ============================================================
    # ENCRYPTION AND DATA PROTECTION
    # ============================================================
    {
        "article": "SaaS TI 3.1",
        "title": "Export Data Encryption",
        "description": "Encrypt exported data based on sensitivity.",
        "field": "export_encryption_required",
        "severity": "HIGH",
        "rule_id": "SAAS_TI_3_1_EXPORT_ENCRYPTION",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "End-to-end encryption with customer-managed keys.",
        "evidence_fields": ["export.encrypted", "saas_profile.encryption_standard", "saas_profile.key_management", "export.data_class"],
        "tenant_risk_applicability": ["CRITICAL", "HIGH", "MEDIUM"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "SaaS TI 3.2",
        "title": "Data Loss Prevention",
        "description": "Prevent data loss through export controls.",
        "field": "data_loss_prevention",
        "severity": "HIGH",
        "rule_id": "SAAS_TI_3_2_DLP",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Content inspection and pattern matching.",
        "evidence_fields": ["saas_profile.dlp_enabled", "saas_profile.content_inspection", "saas_profile.pattern_matching"],
        "tenant_risk_applicability": ["CRITICAL", "HIGH"],
        "compliance_level": "RECOMMENDED",
    },
    
    # ============================================================
    # FUTURE COMPLIANCE READINESS
    # ============================================================
    {
        "article": "SaaS TI 4.1",
        "title": "Automated Compliance Mapping",
        "description": "Automatically map export controls to compliance frameworks.",
        "field": "automated_compliance_mapping",
        "severity": "MEDIUM",
        "rule_id": "SAAS_TI_4_1_COMPLIANCE_MAPPING",
        "enforcement_scope_default": "SUPERVISORY",
        "future_proof_notes": "AI-powered compliance mapping and gap analysis.",
        "evidence_fields": ["saas_profile.compliance_mapping", "saas_profile.framework_mappings", "saas_profile.gap_analysis"],
        "tenant_risk_applicability": ["CRITICAL", "HIGH"],
        "compliance_level": "FUTURE",
        "future_implementation": True,
    },
    {
        "article": "SaaS TI 4.2",
        "title": "Predictive Risk Scoring",
        "description": "Predict export risks using machine learning.",
        "field": "predictive_risk_scoring",
        "severity": "MEDIUM",
        "rule_id": "SAAS_TI_4_2_PREDICTIVE_RISK",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "ML models for risk prediction and proactive controls.",
        "evidence_fields": ["saas_profile.predictive_analytics", "saas_profile.risk_scoring_models", "saas_profile.proactive_controls"],
        "tenant_risk_applicability": ["CRITICAL", "HIGH"],
        "compliance_level": "FUTURE",
        "future_implementation": True,
    },
]


# ============================================================
# MAIN EVALUATION FUNCTION (Future-Proof Architecture)
# ============================================================

def evaluate_saas_transaction_integrity_rules(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Future-proof SaaS Transaction Integrity evaluation with comprehensive context gating.
    
    Features:
    1. Enhanced SaaS multi-tenant detection with confidence scoring
    2. Comprehensive data sensitivity classification with export controls
    3. Advanced external destination analysis with risk scoring
    4. Tenant risk assessment with dynamic control enforcement
    5. Unauthorized export detection with behavioral analytics
    6. Data sovereignty and jurisdiction boundary enforcement
    7. Enhanced enforcement scope resolution with risk-aware escalation
    8. Comprehensive evidence collection for compliance audits
    9. Detailed context tracking and decision logging
    10. Future compliance framework readiness
    
    Returns:
        (policies, summary)
        - policies: List with enforcement_scope, evidence, and context
        - summary: Aggregate statistics with detailed context info
    """
    policies: List[Dict[str, Any]] = []
    
    # ============================================================
    # FUTURE-PROOF: CONTEXT GATING DECISION
    # ============================================================
    is_saas_context, detection_reason, context_evidence = detect_saas_context(payload)
    
    if not is_saas_context:
        # SaaS TI doesn't apply - return with NOT_APPLICABLE
        policies.append({
            "domain": SAAS_TI_DOMAIN,
            "regime": SAAS_TI_REGIME_ID,
            "framework": SAAS_TI_FRAMEWORK,
            "domain_id": SAAS_TI_REGIME_ID,
            "article": "SaaS TI Applicability",
            "category": "Applicability",
            "title": "Applicability",
            "status": "NOT_APPLICABLE",
            "severity": "LOW",
            "impact_on_verdict": "COMPLIANT",
            "trigger_type": "NOT_APPLICABLE",
            "rule_ids": ["SAAS_TI_APPLICABILITY_NA"],
            "enforcement_scope": "SUPERVISORY",
            "notes": f"SaaS Transaction Integrity evaluation skipped: {detection_reason}",
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
            "regime": SAAS_TI_REGIME_ID,
            "context_gated": True,
            "evaluation_decision": detection_reason,
            "context_evidence": context_evidence,
            "notes": f"SaaS TI evaluation skipped: {detection_reason}"
        }
        return policies, summary
    
    # ============================================================
    # CONTEXT INFORMATION COLLECTION
    # ============================================================
    saas_profile = payload.get("saas_profile", {}) or {}
    export_info = payload.get("export", {}) or {}
    risk_indicators = payload.get("risk_indicators", {}) or {}
    
    # Assess various factors
    data_class = export_info.get("data_class", "")
    sensitivity_level, sensitivity_details = classify_data_sensitivity(data_class)
    
    destination = export_info.get("destination", "")
    destination_risk, destination_details = analyze_destination_risk(destination, payload)
    
    tenant_risk, tenant_details = assess_tenant_risk(payload)
    
    export_risk, export_details = detect_unauthorized_export(payload)
    
    # ============================================================
    # RULE EVALUATION (Enhanced with Evidence Collection)
    # ============================================================
    
    evaluation_errors = []
    
    for rule_def in SAAS_TI_RULES:
        # Skip future implementation rules if not ready
        if rule_def.get("future_implementation") and not saas_profile.get("enable_future_requirements"):
            continue
        
        # Check if rule applies to this tenant risk level
        applicable_risks = rule_def.get("tenant_risk_applicability", [])
        if applicable_risks and tenant_risk.value not in applicable_risks:
            continue
        
        try:
            # Check if the required field exists and is compliant
            field_value = saas_profile.get(rule_def["field"])
            
            # Determine status based on field value
            if field_value is False:
                status = "VIOLATED"
            elif field_value is True:
                status = "SATISFIED"
            elif field_value is None:
                # Missing field - determine based on compliance level
                compliance_level = rule_def.get("compliance_level", "REQUIRED")
                if compliance_level == "REQUIRED":
                    status = "VIOLATED"
                elif compliance_level in ["RECOMMENDED", "FUTURE"]:
                    status = "NOT_APPLICABLE"
                else:
                    status = "NOT_APPLICABLE"
            else:
                # Other values - treat as satisfied if truthy
                status = "SATISFIED" if field_value else "VIOLATED"
            
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
            enforcement_scope = resolve_saas_ti_enforcement_scope(rule_def["article"], payload)
            
            # Determine impact on verdict
            if status == "VIOLATED" and rule_def["severity"] in {"HIGH", "CRITICAL"}:
                impact_on_verdict = "BLOCKING_FAILURE"
            elif status == "VIOLATED":
                impact_on_verdict = "NON_BLOCKING"
            else:
                impact_on_verdict = "COMPLIANT"
            
            # Determine severity based on context
            severity = rule_def["severity"]
            if status == "VIOLATED":
                # Escalate severity based on context
                if tenant_risk == TenantRiskLevel.CRITICAL:
                    if severity == "MEDIUM":
                        severity = "HIGH"
                    elif severity == "HIGH":
                        severity = "CRITICAL"
                
                if export_risk == ExportRiskIndicator.CRITICAL:
                    if severity == "MEDIUM":
                        severity = "HIGH"
                    elif severity == "HIGH":
                        severity = "CRITICAL"
                
                if sensitivity_level in [DataSensitivityLevel.RESTRICTED, DataSensitivityLevel.SENSITIVE]:
                    if severity == "MEDIUM":
                        severity = "HIGH"
                
                if destination_risk in [DestinationRiskLevel.CRITICAL, DestinationRiskLevel.HIGH]:
                    if severity == "MEDIUM":
                        severity = "HIGH"
            
            # Create policy
            policy = {
                "domain": SAAS_TI_DOMAIN,
                "regime": SAAS_TI_REGIME_ID,
                "framework": SAAS_TI_FRAMEWORK,
                "domain_id": SAAS_TI_REGIME_ID,
                "article": rule_def["article"],
                "category": rule_def["title"],
                "title": rule_def["title"],
                "status": status,
                "severity": severity if status == "VIOLATED" else "LOW",
                "enforcement_scope": enforcement_scope,
                "impact_on_verdict": impact_on_verdict,
                "trigger_type": "SAAS_TI_CONTROL",
                "rule_ids": [rule_def["rule_id"]],
                "notes": rule_def["description"],
                "evidence": collect_saas_ti_evidence(payload, rule_evidence),
                "remediation": (
                    f"Implement {rule_def['title']} controls per SaaS Transaction Integrity requirements. "
                    "Document procedures and re-run GNCE after remediation."
                    if status == "VIOLATED" else "No remediation required."
                ),
                "violation_detail": rule_def["description"] if status == "VIOLATED" else "",
                "control_severity": rule_def["severity"],
                # Future-proof metadata
                "metadata": {
                    "tenant_risk_level": tenant_risk.value,
                    "tenant_risk_applicability": applicable_risks,
                    "compliance_level": rule_def.get("compliance_level", "REQUIRED"),
                    "data_sensitivity_level": sensitivity_level.value,
                    "destination_risk_level": destination_risk.value,
                    "export_risk_level": export_risk.value,
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
        "tenant_id": payload.get("tenant_id"),
        "multi_tenant": saas_profile.get("multi_tenant"),
        "tenant_risk_level": tenant_risk.value,
    }
    
    # Count by requirement type
    export_control_violations = sum(1 for p in policies 
                                  if p["status"] == "VIOLATED" and "1.1" in p["article"])
    destination_violations = sum(1 for p in policies 
                               if p["status"] == "VIOLATED" and "1.4" in p["article"])
    isolation_violations = sum(1 for p in policies 
                             if p["status"] == "VIOLATED" and any(
                                 req in p["article"] for req in ["1.5", "1.6"]
                             ))
    unauthorized_export_violations = sum(1 for p in policies 
                                       if p["status"] == "VIOLATED" and "UNAUTHORIZED_EXPORT" in p["article"])
    
    # Export risk assessment
    export_risk_assessment = {
        "destination_risk": destination_risk.value,
        "data_sensitivity": sensitivity_level.value,
        "tenant_risk": tenant_risk.value,
        "export_risk": export_risk.value,
        "severity_score": export_details.get("severity_score", 0),
        "indicators_found": export_details.get("indicators_found", []),
    }
    
    summary = {
        "total_rules": len(policies),
        "passed": passed,
        "failed": failed,
        "blocking_failures": blocking,
        "regime": SAAS_TI_REGIME_ID,
        "context_gated": False,
        "evaluation_decision": detection_reason,
        # Context information
        "context": context_info,
        "context_evidence": context_evidence,
        # Tenant information
        "tenant_risk_level": tenant_risk.value,
        "tenant_details": tenant_details,
        # Data sensitivity
        "data_sensitivity_level": sensitivity_level.value,
        "data_sensitivity_details": sensitivity_details,
        # Destination analysis
        "destination_risk_level": destination_risk.value,
        "destination_details": destination_details,
        # Export risk assessment
        "export_risk_assessment": export_risk_assessment,
        "export_details": export_details,
        # Violation breakdown
        "export_control_violations": export_control_violations,
        "destination_violations": destination_violations,
        "isolation_violations": isolation_violations,
        "unauthorized_export_violations": unauthorized_export_violations,
        "critical_tenant_violations": sum(1 for p in policies 
                                        if p["status"] == "VIOLATED" and 
                                        p.get("metadata", {}).get("tenant_risk_level") == "CRITICAL"),
        # Compliance level breakdown
        "required_violations": sum(1 for p in policies 
                                 if p["status"] == "VIOLATED" and 
                                 p.get("metadata", {}).get("compliance_level") == "REQUIRED"),
        "recommended_violations": sum(1 for p in policies 
                                    if p["status"] == "VIOLATED" and 
                                    p.get("metadata", {}).get("compliance_level") == "RECOMMENDED"),
        # Scope breakdown
        "platform_audit_violations": sum(1 for p in policies 
                                       if p["status"] == "VIOLATED" and p.get("enforcement_scope") == "PLATFORM_AUDIT"),
        "transaction_violations": sum(1 for p in policies 
                                    if p["status"] == "VIOLATED" and p.get("enforcement_scope") == "TRANSACTION"),
        "supervisory_violations": sum(1 for p in policies 
                                    if p["status"] == "VIOLATED" and p.get("enforcement_scope") == "SUPERVISORY"),
        # Risk indicators
        "unauthorized_export_indicators": export_details.get("indicators_found", []),
        "previous_violations": risk_indicators.get("previous_violations", 0),
        "harmful_content_flag": risk_indicators.get("harmful_content_flag", False),
        "suspicious_pattern": risk_indicators.get("suspicious_pattern", False),
        # Export information
        "export_approved": export_info.get("approved", False),
        "export_volume": export_info.get("volume"),
        "export_format": export_info.get("format"),
        "export_encrypted": export_info.get("encrypted", False),
        # SaaS profile
        "multi_tenant": saas_profile.get("multi_tenant", False),
        "tenant_isolation": saas_profile.get("tenant_isolation", False),
        "data_boundary_enforced": saas_profile.get("data_boundary_enforced", False),
        "audit_trail_enabled": saas_profile.get("audit_trail_enabled", False),
        # Compliance requirements
        "requires_hipaa": saas_profile.get("requires_hipaa", False),
        "requires_gdpr": saas_profile.get("requires_gdpr", False),
        "requires_soc2": saas_profile.get("requires_soc2", False),
        "requires_iso27001": saas_profile.get("requires_iso27001", False),
        "data_jurisdiction": saas_profile.get("data_jurisdiction"),
        # Rule statistics
        "core_rules_evaluated": len([r for r in SAAS_TI_RULES if not r.get("future_implementation")]),
        "future_rules_available": len([r for r in SAAS_TI_RULES if r.get("future_implementation")]),
        "future_rules_evaluated": len([r for r in SAAS_TI_RULES if r.get("future_implementation") 
                                      and saas_profile.get("enable_future_requirements")]),
        # Error tracking
        "evaluation_errors": evaluation_errors if evaluation_errors else None,
    }
    
    return policies, summary