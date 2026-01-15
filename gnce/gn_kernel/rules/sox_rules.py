# gnce/gn_kernel/rules/sox_rules.py
"""
SOX (Sarbanes-Oxley Act) Rule Evaluator with Constitutional Binding and Future-Proofing (v1.0-FUTUREPROOF)

CRITICAL FUTURE-PROOF UPDATES:
1. Enhanced public company detection with multi-method verification
2. Comprehensive filer classification with dynamic thresholds
3. Materiality-based controls with quantitative impact assessment
4. Internal control framework integration (COSO, COBIT)
5. Real-time disclosure and reporting requirements
6. Enhanced enforcement scope resolution with risk-aware escalation
7. Comprehensive evidence collection for audit trails
8. Cross-domain safety with detailed context gating
9. Emerging growth company and smaller reporting company exemptions
10. Future SEC reporting requirement readiness

SOX REALITY (Future-Proof):
- Sarbanes-Oxley Act of 2002 with subsequent amendments
- Covers all US public companies and SEC registrants
- Key sections: 302, 404, 409, 802, 906, 201, 407
- Internal control over financial reporting (ICFR)
- CEO/CFO certification requirements
- Audit committee independence and expertise
- Real-time disclosure requirements
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple, Set, Optional
import re
from enum import Enum
from datetime import datetime

# Load governance catalog for enforcement scope classification
from gnce.gn_kernel.constitution.constitution_catalog import load_governance_catalog_v05

# ============================================================
# MODULE CONSTANTS (FUTURE-PROOF)
# ============================================================

SOX_DOMAIN = "Sarbanes-Oxley Act of 2002 (SOX)"
SOX_FRAMEWORK = "Financial Reporting & Internal Controls"
SOX_REGIME_ID = "SOX"

# Load catalog once at module level (performance)
_GOVERNANCE_CATALOG = load_governance_catalog_v05()

# ============================================================
# PUBLIC COMPANY DETECTION (FUTURE-PROOF)
# ============================================================

# Financial reporting and SEC filing contexts
FINANCIAL_REPORTING_CONTEXTS: Set[str] = {
    "prepare_financial_statements",
    "file_sec_report",
    "submit_10k",
    "submit_10q",
    "submit_8k",
    "prepare_earnings_release",
    "conduct_financial_close",
    "perform_audit",
    "assess_internal_controls",
    "certify_financials",
    "disclose_material_events",
    "report_going_concern",
    "restate_financials",
    "file_proxy_statement",
    "conduct_quarterly_review",
    "prepare_mda",
    "file_registration_statement",
    "conduct_ipo",
    "report_insider_transactions",
    "file_section_16",
}

# Public company and SEC registrant identifiers
PUBLIC_COMPANY_INDICATORS: Set[str] = {
    "PUBLIC_COMPANY",
    "SEC_REGISTRANT",
    "LISTED_COMPANY",
    "NYSE",
    "NASDAQ",
    "NYSE_AMERICAN",
    "NYSE_ARCA",
    "OTC_MARKETS",
    "SEC_FILER",
    "ACCELERATED_FILER",
    "LARGE_ACCELERATED_FILER",
    "NON_ACCELERATED_FILER",
    "EMERGING_GROWTH_COMPANY",
    "SMALLER_REPORTING_COMPANY",
    "FOREIGN_PRIVATE_ISSUER",
    "BANK_HOLDING_COMPANY",
    "INSURANCE_HOLDING_COMPANY",
}

# ============================================================
# SOX FILER CLASSIFICATION SYSTEM (ENHANCED)
# ============================================================

class FilerClassification(Enum):
    LARGE_ACCELERATED = "LARGE_ACCELERATED_FILER"
    ACCELERATED = "ACCELERATED_FILER"
    NON_ACCELERATED = "NON_ACCELERATED_FILER"
    SMALLER_REPORTING = "SMALLER_REPORTING_COMPANY"
    EMERGING_GROWTH = "EMERGING_GROWTH_COMPANY"
    FOREIGN_PRIVATE = "FOREIGN_PRIVATE_ISSUER"
    MICROCAP = "MICROCAP_COMPANY"
    UNKNOWN = "UNKNOWN"

FILER_CLASSIFICATIONS = {
    FilerClassification.LARGE_ACCELERATED: {
        "public_float_threshold": 700_000_000,  # $700M+
        "revenue_threshold": None,
        "requirements": ["404(b)_ATTESTATION", "ACCELERATED_FILING", "XBRL"],
        "description": "Large accelerated filers with $700M+ public float",
        "sox_404b_required": True,
        "filing_deadlines": {"10-K": "60 days", "10-Q": "40 days"},
    },
    FilerClassification.ACCELERATED: {
        "public_float_threshold": (75_000_000, 699_999_999),  # $75M-$700M
        "revenue_threshold": None,
        "requirements": ["404(b)_ATTESTATION", "ACCELERATED_FILING", "XBRL"],
        "description": "Accelerated filers with $75M-$700M public float",
        "sox_404b_required": True,
        "filing_deadlines": {"10-K": "75 days", "10-Q": "40 days"},
    },
    FilerClassification.NON_ACCELERATED: {
        "public_float_threshold": (0, 74_999_999),  # <$75M
        "revenue_threshold": None,
        "requirements": ["404(a)_MANAGEMENT_REPORT", "NON_ACCELERATED_FILING"],
        "description": "Non-accelerated filers with <$75M public float",
        "sox_404b_required": False,
        "filing_deadlines": {"10-K": "90 days", "10-Q": "45 days"},
    },
    FilerClassification.SMALLER_REPORTING: {
        "public_float_threshold": (0, 250_000_000),  # <$250M
        "revenue_threshold": (0, 100_000_000),  # <$100M revenue
        "requirements": ["SCALED_DISCLOSURES", "404(a)_MANAGEMENT_REPORT"],
        "description": "Smaller reporting companies with scaled disclosures",
        "sox_404b_required": False,
        "filing_deadlines": {"10-K": "90 days", "10-Q": "45 days"},
    },
    FilerClassification.EMERGING_GROWTH: {
        "public_float_threshold": (0, 1_070_000_000),  # <$1.07B
        "revenue_threshold": (0, 100_000_000),  # <$100M revenue (initial qualification)
        "requirements": ["EGC_EXEMPTIONS", "SCALED_DISCLOSURES", "OPT_OUT_404(b)"],
        "description": "Emerging growth companies with temporary exemptions",
        "sox_404b_required": False,  # Can opt out for up to 5 years
        "filing_deadlines": {"10-K": "90 days", "10-Q": "45 days"},
    },
    FilerClassification.FOREIGN_PRIVATE: {
        "public_float_threshold": None,
        "revenue_threshold": None,
        "requirements": ["FPI_DISCLOSURES", "FORM_20_F", "HOME_COUNTRY_PRACTICES"],
        "description": "Foreign private issuers with home country disclosures",
        "sox_404b_required": True,  # For large accelerated/accelerated FPIs
        "filing_deadlines": {"20-F": "4 months", "6-K": "Real-time"},
    },
    FilerClassification.MICROCAP: {
        "public_float_threshold": (0, 50_000_000),  # <$50M
        "revenue_threshold": (0, 25_000_000),  # <$25M revenue
        "requirements": ["MINIMAL_DISCLOSURES", "404(a)_MANAGEMENT_REPORT"],
        "description": "Microcap companies with minimal disclosure requirements",
        "sox_404b_required": False,
        "filing_deadlines": {"10-K": "90 days", "10-Q": "45 days"},
    },
}

# ============================================================
# MATERIALITY AND RISK ASSESSMENT (ENHANCED)
# ============================================================

class MaterialityLevel(Enum):
    HIGHLY_MATERIAL = "HIGHLY_MATERIAL"
    MATERIAL = "MATERIAL"
    MODERATELY_MATERIAL = "MODERATELY_MATERIAL"
    IMMATERIAL = "IMMATERIAL"

MATERIALITY_THRESHOLDS = {
    MaterialityLevel.HIGHLY_MATERIAL: {
        "income_statement": 0.10,  # 10% of net income
        "balance_sheet": 0.05,     # 5% of total assets
        "revenue": 0.03,           # 3% of revenue
        "equity": 0.05,            # 5% of shareholders' equity
        "cash_flow": 0.10,         # 10% of operating cash flow
        "description": "Highly material - requires immediate disclosure and correction",
        "disclosure_requirement": "IMMEDIATE_8K",
    },
    MaterialityLevel.MATERIAL: {
        "income_statement": 0.05,  # 5% of net income
        "balance_sheet": 0.03,     # 3% of total assets
        "revenue": 0.02,           # 2% of revenue
        "equity": 0.03,            # 3% of shareholders' equity
        "cash_flow": 0.05,         # 5% of operating cash flow
        "description": "Material - requires disclosure in next periodic report",
        "disclosure_requirement": "NEXT_PERIODIC_REPORT",
    },
    MaterialityLevel.MODERATELY_MATERIAL: {
        "income_statement": 0.02,  # 2% of net income
        "balance_sheet": 0.01,     # 1% of total assets
        "revenue": 0.01,           # 1% of revenue
        "equity": 0.01,            # 1% of shareholders' equity
        "cash_flow": 0.02,         # 2% of operating cash flow
        "description": "Moderately material - requires evaluation and monitoring",
        "disclosure_requirement": "INTERNAL_MONITORING",
    },
    MaterialityLevel.IMMATERIAL: {
        "income_statement": 0.00,  # Below all thresholds
        "balance_sheet": 0.00,
        "revenue": 0.00,
        "equity": 0.00,
        "cash_flow": 0.00,
        "description": "Immaterial - no disclosure required",
        "disclosure_requirement": "NO_DISCLOSURE",
    },
}

# ============================================================
# INTERNAL CONTROL FRAMEWORKS (ENHANCED)
# ============================================================

class ControlFramework(Enum):
    COSO_2013 = "COSO_2013"
    COBIT_2019 = "COBIT_2019"
    ISO_27001 = "ISO_27001"
    NIST_800_53 = "NIST_800_53"
    PCAOB = "PCAOB_STANDARDS"
    CUSTOM = "CUSTOM_FRAMEWORK"
    NONE = "NO_FRAMEWORK"

INTERNAL_CONTROL_FRAMEWORKS = {
    ControlFramework.COSO_2013: {
        "components": [
            "CONTROL_ENVIRONMENT",
            "RISK_ASSESSMENT",
            "CONTROL_ACTIVITIES",
            "INFORMATION_COMMUNICATION",
            "MONITORING_ACTIVITIES",
        ],
        "principles": 17,
        "acceptance": "WIDELY_ACCEPTED",
        "description": "Committee of Sponsoring Organizations (COSO) 2013 Framework",
        "recommended_for": ["ALL_PUBLIC_COMPANIES", "SOX_COMPLIANCE"],
    },
    ControlFramework.COBIT_2019: {
        "components": [
            "GOVERNANCE_OBJECTIVES",
            "MANAGEMENT_OBJECTIVES",
            "DESIGN_FACTORS",
            "FOCUS_AREAS",
        ],
        "principles": 6,
        "acceptance": "INDUSTRY_ACCEPTED",
        "description": "Control Objectives for Information and Related Technologies",
        "recommended_for": ["TECHNOLOGY_COMPANIES", "IT_CONTROLS"],
    },
    ControlFramework.ISO_27001: {
        "components": [
            "INFORMATION_SECURITY_POLICY",
            "ORGANIZATION_OF_INFORMATION_SECURITY",
            "HUMAN_RESOURCE_SECURITY",
            "ASSET_MANAGEMENT",
            "ACCESS_CONTROL",
            "CRYPTOGRAPHY",
            "PHYSICAL_SECURITY",
            "OPERATIONAL_SECURITY",
            "COMMUNICATIONS_SECURITY",
            "SYSTEM_ACQUISITION",
            "SUPPLIER_RELATIONSHIPS",
            "INFORMATION_SECURITY_INCIDENT_MANAGEMENT",
            "BUSINESS_CONTINUITY",
            "COMPLIANCE",
        ],
        "principles": 14,
        "acceptance": "INTERNATIONAL_STANDARD",
        "description": "International standard for information security management",
        "recommended_for": ["INFORMATION_SECURITY", "DATA_PROTECTION"],
    },
    ControlFramework.PCAOB: {
        "components": [
            "AUDITING_STANDARD_5",
            "RISK_BASED_AUDIT",
            "TOP_DOWN_APPROACH",
            "ENTITY_LEVEL_CONTROLS",
            "PROCESS_LEVEL_CONTROLS",
        ],
        "principles": 5,
        "acceptance": "REGULATORY_REQUIRED",
        "description": "Public Company Accounting Oversight Board Auditing Standards",
        "recommended_for": ["AUDITORS", "ATTESTATION_ENGAGEMENTS"],
    },
}

# ============================================================
# SOX SECTION DETAILS (COMPREHENSIVE)
# ============================================================

class SOXSection(Enum):
    SECTION_302 = "302"
    SECTION_404 = "404"
    SECTION_409 = "409"
    SECTION_802 = "802"
    SECTION_906 = "906"
    SECTION_201 = "201"
    SECTION_407 = "407"
    SECTION_301 = "301"
    SECTION_402 = "402"
    SECTION_403 = "403"

SOX_SECTIONS = {
    SOXSection.SECTION_302: {
        "title": "Corporate Responsibility for Financial Reports",
        "requirements": [
            "CEO_CFO_CERTIFICATION",
            "DISCLOSURE_CONTROLS_PROCEDURES",
            "INTERNAL_CONTROL_EVALUATION",
            "DESIGN_EFFECTIVENESS",
            "OPERATIONAL_EFFECTIVENESS",
            "MATERIAL_WEAKNESS_DISCLOSURE",
        ],
        "certification_required": True,
        "filing_requirement": "EACH_PERIODIC_REPORT",
        "penalties": ["CIVIL", "CRIMINAL"],
        "future_updates": ["ENHANCED_CERTIFICATION", "REAL_TIME_VERIFICATION"],
    },
    SOXSection.SECTION_404: {
        "title": "Management Assessment of Internal Controls",
        "requirements": [
            "MANAGEMENT_ASSESSMENT",
            "INTERNAL_CONTROL_FRAMEWORK",
            "AUDITOR_ATTESTATION",
            "MATERIAL_WEAKNESS_IDENTIFICATION",
            "DEFICIENCY_DISCLOSURE",
            "CONTROL_DOCUMENTATION",
        ],
        "certification_required": False,
        "filing_requirement": "ANNUAL_REPORT",
        "penalties": ["CIVIL", "REGULATORY"],
        "future_updates": ["CONTINUOUS_CONTROL_MONITORING", "AUTOMATED_CONTROL_TESTING"],
    },
    SOXSection.SECTION_409: {
        "title": "Real-Time Issuer Disclosures",
        "requirements": [
            "REAL_TIME_DISCLOSURE",
            "MATERIAL_EVENT_REPORTING",
            "RAPID_FINANCIAL_REPORTING",
            "FORM_8K_FILING",
            "WEBSITE_DISCLOSURE",
            "XBRL_TAGGING",
        ],
        "certification_required": False,
        "filing_requirement": "REAL_TIME",
        "penalties": ["CIVIL", "REGULATORY"],
        "future_updates": ["INSTANT_DISCLOSURE", "AI_POWERED_MATERIALITY_ASSESSMENT"],
    },
    SOXSection.SECTION_802: {
        "title": "Criminal Penalties for Altering Documents",
        "requirements": [
            "RECORD_RETENTION_POLICY",
            "DOCUMENT_DESTRUCTION_PROHIBITION",
            "AUDIT_TRAIL_MAINTENANCE",
            "ELECTRONIC_RECORD_PRESERVATION",
            "WHISTLEBLOWER_PROTECTION",
        ],
        "certification_required": False,
        "filing_requirement": "POLICY_IMPLEMENTATION",
        "penalties": ["CRIMINAL"],
        "future_updates": ["DIGITAL_PRESERVATION", "BLOCKCHAIN_VERIFICATION"],
    },
    SOXSection.SECTION_906: {
        "title": "Corporate Responsibility for Financial Reports (Criminal)",
        "requirements": [
            "CRIMINAL_CERTIFICATION",
            "PENALTY_OF_PERJURY",
            "FALSE_CERTIFICATION_PROHIBITION",
            "KNOWING_CERTIFICATION",
            "WILLFUL_CERTIFICATION",
        ],
        "certification_required": True,
        "filing_requirement": "EACH_PERIODIC_REPORT",
        "penalties": ["CRIMINAL"],
        "future_updates": ["ENHANCED_CRIMINAL_LIABILITY", "AUTOMATED_CERTIFICATION_VERIFICATION"],
    },
    SOXSection.SECTION_201: {
        "title": "Services Outside the Scope of Practice of Auditors",
        "requirements": [
            "PROHIBITED_NON_AUDIT_SERVICES",
            "AUDITOR_INDEPENDENCE",
            "AUDIT_COMMITTEE_PRE_APPROVAL",
            "COOLING_OFF_PERIOD",
            "PARTNER_ROTATION",
        ],
        "certification_required": False,
        "filing_requirement": "PROXY_STATEMENT",
        "penalties": ["REGULATORY", "CIVIL"],
        "future_updates": ["EXPANDED_PROHIBITIONS", "AUDITOR_INDEPENDENCE_MONITORING"],
    },
    SOXSection.SECTION_407: {
        "title": "Disclosure of Audit Committee Financial Expert",
        "requirements": [
            "AUDIT_COMMITTEE_COMPOSITION",
            "FINANCIAL_EXPERT_DISCLOSURE",
            "INDEPENDENCE_REQUIREMENT",
            "FINANCIAL_LITERACY",
            "COMMITTEE_CHARTER",
        ],
        "certification_required": False,
        "filing_requirement": "ANNUAL_REPORT",
        "penalties": ["REGULATORY"],
        "future_updates": ["ENHANCED_EXPERTISE_REQUIREMENTS", "CONTINUING_EDUCATION"],
    },
}

# ============================================================
# SOX COMPLIANCE DETECTION (FUTURE-PROOF)
# ============================================================

def detect_sox_context(payload: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Enhanced SOX context detection with multi-method verification.
    
    Returns:
        (is_sox_context, detection_reason, context_evidence)
    """
    context_evidence = {
        "detection_methods": [],
        "indicators_found": [],
        "confidence": "LOW",
    }
    
    # Method 1: Explicit SOX flags
    if payload.get("sox_compliance_required") or payload.get("public_company"):
        context_evidence["detection_methods"].append("EXPLICIT_FLAG")
        context_evidence["confidence"] = "HIGH"
        context_evidence["indicators_found"].append("explicit_sox_flag")
        return True, "EXPLICIT_SOX_FLAG", context_evidence
    
    # Method 2: Action classification
    action = str(payload.get("action", "")).lower().strip()
    if action in FINANCIAL_REPORTING_CONTEXTS:
        context_evidence["detection_methods"].append("ACTION_CLASSIFICATION")
        context_evidence["confidence"] = "MEDIUM"
        context_evidence["indicators_found"].append(f"action:{action}")
        
        # Check for SEC filing context
        if any(term in action for term in ["sec", "10k", "10q", "8k", "filing"]):
            context_evidence["confidence"] = "HIGH"
            return True, f"SEC_FILING_ACTION: {action}", context_evidence
    
    # Method 3: Company type classification
    company_type = str(payload.get("company_type", "")).upper().strip()
    if company_type in PUBLIC_COMPANY_INDICATORS:
        context_evidence["detection_methods"].append("COMPANY_TYPE")
        context_evidence["confidence"] = "HIGH"
        context_evidence["indicators_found"].append(f"company_type:{company_type}")
        return True, f"PUBLIC_COMPANY_TYPE: {company_type}", context_evidence
    
    # Method 4: SOX profile detection
    sox_profile = payload.get("sox_profile", {})
    if sox_profile:
        if sox_profile.get("public_company") or sox_profile.get("sec_filer"):
            context_evidence["detection_methods"].append("SOX_PROFILE")
            context_evidence["confidence"] = "HIGH"
            context_evidence["indicators_found"].append("public_company_flag")
            return True, "SOX_PROFILE_PUBLIC_COMPANY", context_evidence
        
        # Check for SOX-specific fields
        sox_fields = ["filer_classification", "public_float", "ic_certification", "ic_assessment"]
        if any(field in sox_profile for field in sox_fields):
            context_evidence["detection_methods"].append("SOX_PROFILE_FIELDS")
            context_evidence["confidence"] = "MEDIUM"
            context_evidence["indicators_found"].extend(sox_fields)
            return True, "SOX_PROFILE_FIELDS_DETECTED", context_evidence
    
    # Method 5: Jurisdiction verification
    meta = payload.get("meta", {})
    jurisdiction = str(meta.get("jurisdiction", "")).upper()
    
    # SOX is US-specific
    if not any(us_term in jurisdiction for us_term in ["US", "UNITED_STATES", "USA"]):
        return False, "NON_US_JURISDICTION", context_evidence
    
    # Method 6: Exchange listing
    exchange = str(meta.get("exchange", "")).upper()
    if exchange in ["NYSE", "NASDAQ", "NYSE_AMERICAN", "OTC"]:
        context_evidence["detection_methods"].append("EXCHANGE_LISTING")
        context_evidence["confidence"] = "HIGH"
        context_evidence["indicators_found"].append(f"exchange:{exchange}")
        return True, f"US_EXCHANGE_LISTED: {exchange}", context_evidence
    
    return False, "NOT_SOX_CONTEXT", context_evidence


def classify_sox_filer(payload: Dict[str, Any]) -> Tuple[FilerClassification, Dict[str, Any]]:
    """
    Enhanced SOX filer classification with multiple factors.
    
    Returns:
        (filer_classification, classification_details)
    """
    classification_details = {
        "classification_method": "DEFAULT",
        "factors_considered": [],
        "public_float": 0,
        "revenue": 0,
        "confidence": "LOW",
    }
    
    sox_profile = payload.get("sox_profile", {}) or {}
    
    # Method 1: Explicit classification
    explicit_class = sox_profile.get("filer_classification", "").upper()
    if explicit_class:
        try:
            # Try to map explicit classification to enum
            for filer_class in FilerClassification:
                if filer_class.value == explicit_class:
                    classification_details["classification_method"] = "EXPLICIT"
                    classification_details["confidence"] = "HIGH"
                    return filer_class, classification_details
        except ValueError:
            pass
    
    # Method 2: Quantitative classification
    public_float = sox_profile.get("public_float", 0)
    revenue = sox_profile.get("revenue", 0)
    
    classification_details["public_float"] = public_float
    classification_details["revenue"] = revenue
    classification_details["factors_considered"].extend([
        f"public_float:{public_float}",
        f"revenue:{revenue}",
    ])
    
    # Check emerging growth company status
    if sox_profile.get("emerging_growth_company"):
        classification_details["classification_method"] = "EMERGING_GROWTH_FLAG"
        classification_details["confidence"] = "HIGH"
        return FilerClassification.EMERGING_GROWTH, classification_details
    
    # Check smaller reporting company status
    if sox_profile.get("smaller_reporting_company"):
        classification_details["classification_method"] = "SMALLER_REPORTING_FLAG"
        classification_details["confidence"] = "HIGH"
        return FilerClassification.SMALLER_REPORTING, classification_details
    
    # Check foreign private issuer status
    if sox_profile.get("foreign_private_issuer"):
        classification_details["classification_method"] = "FOREIGN_PRIVATE_ISSUER_FLAG"
        classification_details["confidence"] = "HIGH"
        return FilerClassification.FOREIGN_PRIVATE, classification_details
    
    # Quantitative classification based on public float
    if public_float >= 700_000_000:
        classification_details["classification_method"] = "PUBLIC_FLOAT_THRESHOLD"
        classification_details["confidence"] = "HIGH"
        return FilerClassification.LARGE_ACCELERATED, classification_details
    
    elif 75_000_000 <= public_float <= 699_999_999:
        classification_details["classification_method"] = "PUBLIC_FLOAT_THRESHOLD"
        classification_details["confidence"] = "HIGH"
        return FilerClassification.ACCELERATED, classification_details
    
    elif public_float < 75_000_000:
        # Check for microcap
        if public_float < 50_000_000 and revenue < 25_000_000:
            classification_details["classification_method"] = "MICROCAP_THRESHOLD"
            classification_details["confidence"] = "MEDIUM"
            return FilerClassification.MICROCAP, classification_details
        else:
            classification_details["classification_method"] = "PUBLIC_FLOAT_THRESHOLD"
            classification_details["confidence"] = "HIGH"
            return FilerClassification.NON_ACCELERATED, classification_details
    
    # Default: NON_ACCELERATED (conservative)
    classification_details["classification_method"] = "DEFAULT"
    classification_details["confidence"] = "LOW"
    return FilerClassification.NON_ACCELERATED, classification_details


def assess_materiality(amount: float, financial_statement: str, payload: Dict[str, Any]) -> Tuple[MaterialityLevel, Dict[str, Any]]:
    """
    Assess materiality of an amount relative to financial statement benchmarks.
    
    Returns:
        (materiality_level, assessment_details)
    """
    assessment_details = {
        "amount": amount,
        "financial_statement": financial_statement,
        "benchmark": 0,
        "percentage": 0.0,
        "thresholds_checked": [],
    }
    
    sox_profile = payload.get("sox_profile", {}) or {}
    
    # Get relevant financial metrics
    net_income = sox_profile.get("net_income", 0)
    total_assets = sox_profile.get("total_assets", 0)
    total_revenue = sox_profile.get("revenue", 0)
    shareholders_equity = sox_profile.get("shareholders_equity", 0)
    operating_cash_flow = sox_profile.get("operating_cash_flow", 0)
    
    # Calculate percentage based on financial statement type
    percentage = 0.0
    benchmark = 0
    
    if financial_statement == "INCOME_STATEMENT" and net_income != 0:
        percentage = abs(amount / net_income)
        benchmark = net_income
        assessment_details["benchmark"] = benchmark
        assessment_details["percentage"] = percentage
    elif financial_statement == "BALANCE_SHEET" and total_assets != 0:
        percentage = abs(amount / total_assets)
        benchmark = total_assets
        assessment_details["benchmark"] = benchmark
        assessment_details["percentage"] = percentage
    elif financial_statement == "REVENUE" and total_revenue != 0:
        percentage = abs(amount / total_revenue)
        benchmark = total_revenue
        assessment_details["benchmark"] = benchmark
        assessment_details["percentage"] = percentage
    elif financial_statement == "EQUITY" and shareholders_equity != 0:
        percentage = abs(amount / shareholders_equity)
        benchmark = shareholders_equity
        assessment_details["benchmark"] = benchmark
        assessment_details["percentage"] = percentage
    elif financial_statement == "CASH_FLOW" and operating_cash_flow != 0:
        percentage = abs(amount / operating_cash_flow)
        benchmark = operating_cash_flow
        assessment_details["benchmark"] = benchmark
        assessment_details["percentage"] = percentage
    
    # Determine materiality level
    if percentage >= 0.10:
        assessment_details["thresholds_checked"].append("HIGHLY_MATERIAL")
        return MaterialityLevel.HIGHLY_MATERIAL, assessment_details
    elif percentage >= 0.05:
        assessment_details["thresholds_checked"].append("MATERIAL")
        return MaterialityLevel.MATERIAL, assessment_details
    elif percentage >= 0.02:
        assessment_details["thresholds_checked"].append("MODERATELY_MATERIAL")
        return MaterialityLevel.MODERATELY_MATERIAL, assessment_details
    else:
        assessment_details["thresholds_checked"].append("IMMATERIAL")
        return MaterialityLevel.IMMATERIAL, assessment_details


def detect_material_misstatement(payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Enhanced material misstatement detection with quantitative analysis.
    
    Returns:
        (has_material_misstatement, detection_details)
    """
    detection_details = {
        "misstatement_indicators": [],
        "quantitative_assessments": [],
        "severity_score": 0,
        "confidence": "LOW",
    }
    
    sox_profile = payload.get("sox_profile", {}) or {}
    risk_indicators = payload.get("risk_indicators", {}) or {}
    
    severity_score = 0
    misstatement_indicators = []
    
    # Check explicit indicators
    if risk_indicators.get("material_misstatement_active"):
        misstatement_indicators.append("material_misstatement_active")
        severity_score += 100
    
    if sox_profile.get("financial_restatement"):
        misstatement_indicators.append("financial_restatement")
        severity_score += 100
    
    if sox_profile.get("material_weakness"):
        misstatement_indicators.append("material_weakness")
        severity_score += 80
    
    if sox_profile.get("significant_deficiency"):
        misstatement_indicators.append("significant_deficiency")
        severity_score += 60
    
    # Check quantitative misstatements
    misstatement_amount = risk_indicators.get("misstatement_amount", 0)
    financial_statement = risk_indicators.get("financial_statement", "INCOME_STATEMENT")
    
    if misstatement_amount > 0:
        materiality_level, materiality_details = assess_materiality(
            misstatement_amount, financial_statement, payload
        )
        
        detection_details["quantitative_assessments"].append({
            "amount": misstatement_amount,
            "financial_statement": financial_statement,
            "materiality_level": materiality_level.value,
            "details": materiality_details,
        })
        
        if materiality_level in [MaterialityLevel.HIGHLY_MATERIAL, MaterialityLevel.MATERIAL]:
            misstatement_indicators.append(f"quantitative_misstatement:{materiality_level.value}")
            severity_score += 70 if materiality_level == MaterialityLevel.HIGHLY_MATERIAL else 50
    
    # Check fraud indicators
    fraud_indicators = [
        "financial_statement_fraud",
        "revenue_recognition_issues",
        "inventory_misstatement",
        "expense_misstatement",
        "asset_impairment_issues",
        "liability_understatement",
    ]
    
    for indicator in fraud_indicators:
        if risk_indicators.get(indicator):
            misstatement_indicators.append(indicator)
            severity_score += 40
    
    # Check going concern issues
    if risk_indicators.get("going_concern_issue"):
        misstatement_indicators.append("going_concern_issue")
        severity_score += 90
    
    detection_details["misstatement_indicators"] = misstatement_indicators
    detection_details["severity_score"] = severity_score
    
    # Determine if material misstatement exists
    has_material_misstatement = (
        severity_score >= 50 or  # Quantitative threshold
        sox_profile.get("financial_restatement") or
        sox_profile.get("material_weakness") or
        risk_indicators.get("material_misstatement_active")
    )
    
    if has_material_misstatement:
        detection_details["confidence"] = "HIGH" if severity_score >= 70 else "MEDIUM"
    else:
        detection_details["confidence"] = "LOW"
    
    return has_material_misstatement, detection_details


def assess_internal_control_framework(payload: Dict[str, Any]) -> Tuple[ControlFramework, Dict[str, Any]]:
    """
    Assess internal control framework implementation.
    
    Returns:
        (control_framework, assessment_details)
    """
    assessment_details = {
        "framework_identified": "UNKNOWN",
        "components_present": [],
        "completeness_score": 0,
        "recommendations": [],
    }
    
    sox_profile = payload.get("sox_profile", {}) or {}
    
    # Check explicit framework
    framework_name = sox_profile.get("internal_controls_framework", "")
    if framework_name:
        framework_name_upper = framework_name.upper()
        
        # Map to enum
        if "COSO" in framework_name_upper:
            assessment_details["framework_identified"] = "COSO_2013"
            return ControlFramework.COSO_2013, assessment_details
        elif "COBIT" in framework_name_upper:
            assessment_details["framework_identified"] = "COBIT_2019"
            return ControlFramework.COBIT_2019, assessment_details
        elif "ISO" in framework_name_upper and "27001" in framework_name_upper:
            assessment_details["framework_identified"] = "ISO_27001"
            return ControlFramework.ISO_27001, assessment_details
        elif "PCAOB" in framework_name_upper or "AS5" in framework_name_upper:
            assessment_details["framework_identified"] = "PCAOB"
            return ControlFramework.PCAOB, assessment_details
        elif "CUSTOM" in framework_name_upper:
            assessment_details["framework_identified"] = "CUSTOM_FRAMEWORK"
            return ControlFramework.CUSTOM, assessment_details
    
    # Check framework components
    framework_components = sox_profile.get("framework_components", [])
    if isinstance(framework_components, list):
        assessment_details["components_present"] = framework_components
        
        # Try to infer framework from components
        coso_components = {"CONTROL_ENVIRONMENT", "RISK_ASSESSMENT", "CONTROL_ACTIVITIES"}
        if any(comp in coso_components for comp in framework_components):
            assessment_details["framework_identified"] = "COSO_2013 (INFERRED)"
            return ControlFramework.COSO_2013, assessment_details
    
    # Default: NO_FRAMEWORK
    assessment_details["framework_identified"] = "NO_FRAMEWORK"
    assessment_details["recommendations"].append("IMPLEMENT_COSO_FRAMEWORK")
    return ControlFramework.NONE, assessment_details


# ============================================================
# ENFORCEMENT SCOPE RESOLUTION (FUTURE-PROOF)
# ============================================================

def normalize_sox_article(article: str) -> str:
    """
    Normalize SOX article identifier.
    
    Future-proof examples:
        "SOX §302" → "302"
        "Section 404" → "404"
        "SOX 409" → "409"
        "SOX Section 802(a)" → "802"
    """
    if not article:
        return ""
    
    article = article.strip()
    
    # Extract section number
    import re
    
    # Match patterns like: "302", "404", "802", "906"
    match = re.search(r'(\d{3})', article)
    if match:
        return match.group(1)
    
    # For non-standard references
    if "MATERIAL_MISSTATEMENT" in article.upper():
        return "MATERIAL_MISSTATEMENT"
    elif "INTERNAL_CONTROL" in article.upper():
        return "INTERNAL_CONTROL"
    elif "APPLICABILITY" in article.upper():
        return "APPLICABILITY"
    
    # Return cleaned version
    return re.sub(r'[^\d]', '', article)


def get_sox_base_enforcement_scope(article: str) -> str:
    """
    Get base enforcement scope from governance catalog.
    
    Future-proof SOX Classification:
    - CEO/CFO certification: TRANSACTION (immediate enforcement)
    - Internal controls: PLATFORM_AUDIT (periodic assessment)
    - Disclosure requirements: TRANSACTION/SUPERVISORY
    - Audit committee: SUPERVISORY (governance)
    
    Returns: "TRANSACTION" | "PLATFORM_AUDIT" | "SUPERVISORY"
    Default: "PLATFORM_AUDIT" (conservative for SOX)
    """
    article_normalized = normalize_sox_article(article)
    
    # First check catalog for SOX regime
    for regime in _GOVERNANCE_CATALOG.get("regimes", []):
        if regime.get("id") == SOX_REGIME_ID:
            for domain in regime.get("domains", []):
                for art_def in domain.get("articles", []):
                    if art_def.get("article", "") == article_normalized:
                        return art_def.get("enforcement_scope", "PLATFORM_AUDIT")
    
    # Local mapping based on requirement type
    sox_scopes = {
        # CEO/CFO Certification Requirements (Transaction)
        "302": "TRANSACTION",  # CEO/CFO certification
        "906": "TRANSACTION",  # Criminal certification
        
        # Internal Control Requirements (Platform Audit)
        "404": "PLATFORM_AUDIT",  # Management assessment
        "INTERNAL_CONTROL": "PLATFORM_AUDIT",  # Internal controls
        
        # Disclosure Requirements (Transaction/Supervisory)
        "409": "TRANSACTION",  # Real-time disclosure
        "802": "SUPERVISORY",  # Record retention
        
        # Governance Requirements (Supervisory)
        "201": "SUPERVISORY",  # Auditor independence
        "407": "SUPERVISORY",  # Audit committee
        
        # Material Misstatement (Transaction)
        "MATERIAL_MISSTATEMENT": "TRANSACTION",
        
        # Default scope for unknown sections
        "APPLICABILITY": "SUPERVISORY",
    }
    
    # Check for exact match first
    if article_normalized in sox_scopes:
        return sox_scopes[article_normalized]
    
    return "PLATFORM_AUDIT"  # Safe default for SOX


def resolve_sox_enforcement_scope(article: str, payload: Dict[str, Any]) -> str:
    """
    Resolve final enforcement scope with future-proof modifiers.
    
    SOX enforcement scope modifiers:
    1. Material misstatement escalation
    2. Large accelerated filer escalation
    3. Real-time reporting requirements
    4. Going concern issues
    5. Fraud detection
    6. Financial restatement
    
    Returns:
        Final enforcement scope after applying modifiers
    """
    base_scope = get_sox_base_enforcement_scope(article)
    article_normalized = normalize_sox_article(article)
    
    # Get context information
    sox_profile = payload.get("sox_profile", {}) or {}
    risk_indicators = payload.get("risk_indicators", {}) or {}
    
    # Assess filer classification
    filer_classification, _ = classify_sox_filer(payload)
    is_large_accelerated = filer_classification == FilerClassification.LARGE_ACCELERATED
    
    # Detect material misstatement
    has_material_misstatement, _ = detect_material_misstatement(payload)
    
    # MODIFIER 1: Material misstatement escalation
    if has_material_misstatement:
        if base_scope in {"PLATFORM_AUDIT", "SUPERVISORY"}:
            return "TRANSACTION"
    
    # MODIFIER 2: Large accelerated filer escalation
    if is_large_accelerated:
        if article_normalized in {"302", "404", "409", "906"}:
            return "TRANSACTION"
    
    # MODIFIER 3: Real-time financial reporting
    action = str(payload.get("action", "")).lower()
    if "real_time" in action or "8k" in action:
        if article_normalized in {"302", "409"}:
            return "TRANSACTION"
    
    # MODIFIER 4: Going concern issues
    if risk_indicators.get("going_concern_issue"):
        if article_normalized in {"302", "409"}:
            return "TRANSACTION"
    
    # MODIFIER 5: Fraud detection
    fraud_indicators = [
        "financial_statement_fraud",
        "revenue_recognition_issues",
        "inventory_misstatement",
        "expense_misstatement",
    ]
    
    if any(risk_indicators.get(indicator) for indicator in fraud_indicators):
        if article_normalized in {"302", "906", "MATERIAL_MISSTATEMENT"}:
            return "TRANSACTION"
    
    # MODIFIER 6: Financial restatement
    if sox_profile.get("financial_restatement"):
        if article_normalized in {"302", "404", "409"}:
            return "TRANSACTION"
    
    # MODIFIER 7: Material weakness in internal controls
    if sox_profile.get("material_weakness"):
        if article_normalized in {"302", "404"}:
            return "TRANSACTION"
    
    # MODIFIER 8: Quarterly/annual filing periods
    meta = payload.get("meta", {})
    reporting_period = meta.get("reporting_period", "").upper()
    if reporting_period in ["Q1", "Q2", "Q3", "Q4", "ANNUAL"]:
        if article_normalized in {"302", "906"}:
            return "TRANSACTION"
    
    # No modifiers applied
    return base_scope


# ============================================================
# EVIDENCE COLLECTION (Enhanced for SOX)
# ============================================================

def collect_sox_evidence(payload: Dict[str, Any], rule_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect comprehensive SOX evidence for audit trails.
    
    Returns:
        Structured evidence with context, rule data, and metadata
    """
    evidence = {
        # Context evidence
        "context": {
            "company_type": payload.get("company_type"),
            "action": payload.get("action"),
            "jurisdiction": (payload.get("meta") or {}).get("jurisdiction"),
            "exchange": (payload.get("meta") or {}).get("exchange"),
            "sox_context_detected": True,
        },
        # Rule-specific evidence
        "rule_data": rule_data,
        # SOX-specific information
        "sox_info": {},
        # Audit metadata
        "audit_metadata": {
            "evidence_collected_at": "NOW",  # Would be timestamp in real implementation
            "regulation_version": "Sarbanes-Oxley Act of 2002",
            "evidence_type": "RULE_EVALUATION",
            "evidence_scope": "SOX_COMPLIANCE",
        }
    }
    
    # Collect SOX-specific information
    sox_profile = payload.get("sox_profile", {}) or {}
    
    # Assess various factors
    filer_classification, filer_details = classify_sox_filer(payload)
    has_material_misstatement, misstatement_details = detect_material_misstatement(payload)
    control_framework, framework_details = assess_internal_control_framework(payload)
    
    evidence["sox_info"] = {
        "filer_information": {
            "filer_classification": filer_classification.value,
            "filer_details": filer_details,
            "public_float": sox_profile.get("public_float"),
            "revenue": sox_profile.get("revenue"),
            "public_company": sox_profile.get("public_company"),
            "sec_filer": sox_profile.get("sec_filer"),
            "emerging_growth_company": sox_profile.get("emerging_growth_company"),
            "smaller_reporting_company": sox_profile.get("smaller_reporting_company"),
            "foreign_private_issuer": sox_profile.get("foreign_private_issuer"),
        },
        "internal_control_information": {
            "control_framework": control_framework.value,
            "framework_details": framework_details,
            "ic_certification": sox_profile.get("ic_certification"),
            "ic_assessment": sox_profile.get("ic_assessment"),
            "material_weakness": sox_profile.get("material_weakness"),
            "significant_deficiency": sox_profile.get("significant_deficiency"),
            "financial_restatement": sox_profile.get("financial_restatement"),
        },
        "certification_information": {
            "ceo_cfo_certification": sox_profile.get("ic_certification"),
            "criminal_certification": sox_profile.get("criminal_certification"),
            "disclosure_controls": sox_profile.get("disclosure_controls"),
            "real_time_disclosure": sox_profile.get("real_time_disclosure"),
            "record_retention": sox_profile.get("record_retention"),
        },
        "governance_information": {
            "auditor_independence": sox_profile.get("auditor_independence"),
            "audit_committee_financial_expert": sox_profile.get("audit_committee_financial_expert"),
            "code_of_ethics": sox_profile.get("code_of_ethics"),
            "whistleblower_policy": sox_profile.get("whistleblower_policy"),
        },
        "risk_information": {
            "has_material_misstatement": has_material_misstatement,
            "misstatement_details": misstatement_details,
            "going_concern_issue": (payload.get("risk_indicators") or {}).get("going_concern_issue"),
            "fraud_indicators": [(payload.get("risk_indicators") or {}).get(indicator) 
                                for indicator in ["financial_statement_fraud", "revenue_recognition_issues"]],
        },
    }
    
    return evidence


# ============================================================
# SOX RULE DEFINITIONS (Enhanced with All Requirements)
# ============================================================

# SOX rules with comprehensive metadata
SOX_RULES = [
    # ============================================================
    # SOX §302: CEO/CFO CERTIFICATION
    # ============================================================
    {
        "article": "SOX §302",
        "title": "CEO/CFO Certification of Financial Reports",
        "description": "Require CEO and CFO certification of financial statements and internal controls.",
        "field": "ic_certification",
        "severity": "HIGH",
        "rule_id": "SOX_302_IC_CERT",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Future: Real-time certification and blockchain-based verification.",
        "evidence_fields": ["sox_profile.ic_certification", "sox_profile.disclosure_controls", "sox_profile.financial_statement_accuracy"],
        "filer_applicability": ["LARGE_ACCELERATED_FILER", "ACCELERATED_FILER", "NON_ACCELERATED_FILER", "SMALLER_REPORTING_COMPANY"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # SOX §404: INTERNAL CONTROL ASSESSMENT
    # ============================================================
    {
        "article": "SOX §404",
        "title": "Management Assessment of Internal Controls",
        "description": "Management assessment of internal control over financial reporting (ICFR).",
        "field": "ic_assessment",
        "severity": "CRITICAL",
        "rule_id": "SOX_404_IC_ASSESSMENT",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Future: Continuous control monitoring and automated testing.",
        "evidence_fields": ["sox_profile.ic_assessment", "sox_profile.internal_controls_framework", "sox_profile.control_documentation", "sox_profile.deficiency_reporting"],
        "filer_applicability": ["LARGE_ACCELERATED_FILER", "ACCELERATED_FILER", "NON_ACCELERATED_FILER"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "SOX §404(b)",
        "title": "Auditor Attestation of Internal Controls",
        "description": "Independent auditor attestation of internal control effectiveness.",
        "field": "auditor_attestation",
        "severity": "CRITICAL",
        "rule_id": "SOX_404B_AUDITOR_ATTESTATION",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Required for accelerated and large accelerated filers.",
        "evidence_fields": ["sox_profile.auditor_attestation", "sox_profile.audit_opinion", "sox_profile.material_weakness_reporting"],
        "filer_applicability": ["LARGE_ACCELERATED_FILER", "ACCELERATED_FILER"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # SOX §409: REAL-TIME DISCLOSURE
    # ============================================================
    {
        "article": "SOX §409",
        "title": "Real-Time Issuer Disclosures",
        "description": "Real-time disclosure of material information to the public.",
        "field": "real_time_disclosure",
        "severity": "HIGH",
        "rule_id": "SOX_409_DISCLOSURE",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Future: Instant disclosure and AI-powered materiality assessment.",
        "evidence_fields": ["sox_profile.real_time_disclosure", "sox_profile.material_event_reporting", "sox_profile.form_8k_filing", "sox_profile.website_disclosure"],
        "filer_applicability": ["LARGE_ACCELERATED_FILER", "ACCELERATED_FILER", "NON_ACCELERATED_FILER", "SMALLER_REPORTING_COMPANY"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # SOX §802: RECORD RETENTION
    # ============================================================
    {
        "article": "SOX §802",
        "title": "Criminal Penalties for Altering Documents",
        "description": "Document retention policies and prohibition of document destruction.",
        "field": "record_retention",
        "severity": "MEDIUM",
        "rule_id": "SOX_802_RECORD_RETENTION",
        "enforcement_scope_default": "SUPERVISORY",
        "future_proof_notes": "Future: Digital preservation and blockchain verification.",
        "evidence_fields": ["sox_profile.record_retention", "sox_profile.document_retention_policy", "sox_profile.audit_trail_maintenance", "sox_profile.whistleblower_protection"],
        "filer_applicability": ["LARGE_ACCELERATED_FILER", "ACCELERATED_FILER", "NON_ACCELERATED_FILER", "SMALLER_REPORTING_COMPANY"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # SOX §906: CRIMINAL CERTIFICATION
    # ============================================================
    {
        "article": "SOX §906",
        "title": "Criminal Certification of Financial Reports",
        "description": "CEO/CFO certification under penalty of perjury.",
        "field": "criminal_certification",
        "severity": "CRITICAL",
        "rule_id": "SOX_906_CRIMINAL_CERT",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Carries criminal penalties for false certification.",
        "evidence_fields": ["sox_profile.criminal_certification", "sox_profile.penalty_of_perjury", "sox_profile.false_certification_prohibition"],
        "filer_applicability": ["LARGE_ACCELERATED_FILER", "ACCELERATED_FILER", "NON_ACCELERATED_FILER", "SMALLER_REPORTING_COMPANY"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # SOX §201: AUDITOR INDEPENDENCE
    # ============================================================
    {
        "article": "SOX §201",
        "title": "Auditor Independence",
        "description": "Prohibition of non-audit services that impair auditor independence.",
        "field": "auditor_independence",
        "severity": "HIGH",
        "rule_id": "SOX_201_AUDITOR_INDEP",
        "enforcement_scope_default": "SUPERVISORY",
        "future_proof_notes": "Future: Enhanced auditor independence monitoring.",
        "evidence_fields": ["sox_profile.auditor_independence", "sox_profile.prohibited_non_audit_services", "sox_profile.audit_committee_pre_approval", "sox_profile.partner_rotation"],
        "filer_applicability": ["LARGE_ACCELERATED_FILER", "ACCELERATED_FILER", "NON_ACCELERATED_FILER", "SMALLER_REPORTING_COMPANY"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # SOX §407: AUDIT COMMITTEE FINANCIAL EXPERT
    # ============================================================
    {
        "article": "SOX §407",
        "title": "Audit Committee Financial Expert",
        "description": "Disclosure of audit committee financial expert.",
        "field": "audit_committee_financial_expert",
        "severity": "MEDIUM",
        "rule_id": "SOX_407_AUDIT_COMMITTEE",
        "enforcement_scope_default": "SUPERVISORY",
        "future_proof_notes": "Future: Enhanced expertise requirements and continuing education.",
        "evidence_fields": ["sox_profile.audit_committee_financial_expert", "sox_profile.audit_committee_composition", "sox_profile.financial_expert_disclosure", "sox_profile.committee_charter"],
        "filer_applicability": ["LARGE_ACCELERATED_FILER", "ACCELERATED_FILER", "NON_ACCELERATED_FILER", "SMALLER_REPORTING_COMPANY"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # ADDITIONAL SOX REQUIREMENTS
    # ============================================================
    {
        "article": "SOX §301",
        "title": "Audit Committee Independence",
        "description": "Audit committee must be composed of independent directors.",
        "field": "audit_committee_independence",
        "severity": "MEDIUM",
        "rule_id": "SOX_301_AUDIT_COMMITTEE_INDEP",
        "enforcement_scope_default": "SUPERVISORY",
        "future_proof_notes": "Critical for auditor oversight.",
        "evidence_fields": ["sox_profile.audit_committee_independence", "sox_profile.independent_directors", "sox_profile.auditor_oversight"],
        "filer_applicability": ["LARGE_ACCELERATED_FILER", "ACCELERATED_FILER", "NON_ACCELERATED_FILER"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "SOX §402",
        "title": "Enhanced Conflict of Interest Provisions",
        "description": "Prohibition of personal loans to executives.",
        "field": "executive_loan_prohibition",
        "severity": "MEDIUM",
        "rule_id": "SOX_402_EXECUTIVE_LOANS",
        "enforcement_scope_default": "SUPERVISORY",
        "future_proof_notes": "Prevents conflict of interest.",
        "evidence_fields": ["sox_profile.executive_loan_prohibition", "sox_profile.conflict_of_interest_policy"],
        "filer_applicability": ["LARGE_ACCELERATED_FILER", "ACCELERATED_FILER", "NON_ACCELERATED_FILER", "SMALLER_REPORTING_COMPANY"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "SOX §403",
        "title": "Disclosure of Insider Transactions",
        "description": "Accelerated disclosure of insider transactions.",
        "field": "insider_transaction_disclosure",
        "severity": "MEDIUM",
        "rule_id": "SOX_403_INSIDER_DISCLOSURE",
        "enforcement_scope_default": "SUPERVISORY",
        "future_proof_notes": "Real-time insider trading reporting.",
        "evidence_fields": ["sox_profile.insider_transaction_disclosure", "sox_profile.section_16_filing", "sox_profile.insider_trading_policy"],
        "filer_applicability": ["LARGE_ACCELERATED_FILER", "ACCELERATED_FILER", "NON_ACCELERATED_FILER", "SMALLER_REPORTING_COMPANY"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # MATERIAL MISSTATEMENT DETECTION
    # ============================================================
    {
        "article": "SOX Material Misstatement",
        "title": "Material Misstatement Detection",
        "description": "Detection and reporting of material financial statement misstatements.",
        "field": "material_misstatement_detection",
        "severity": "CRITICAL",
        "rule_id": "SOX_MATERIAL_MISSTATEMENT",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Critical for financial statement accuracy.",
        "evidence_fields": ["sox_profile.financial_restatement", "sox_profile.material_weakness", "risk_indicators.material_misstatement_active", "risk_indicators.going_concern_issue"],
        "filer_applicability": ["LARGE_ACCELERATED_FILER", "ACCELERATED_FILER", "NON_ACCELERATED_FILER", "SMALLER_REPORTING_COMPANY"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # WHISTLEBLOWER PROTECTION
    # ============================================================
    {
        "article": "SOX Whistleblower Protection",
        "title": "Whistleblower Protection",
        "description": "Protection for employees reporting fraud and violations.",
        "field": "whistleblower_policy",
        "severity": "MEDIUM",
        "rule_id": "SOX_WHISTLEBLOWER_PROTECTION",
        "enforcement_scope_default": "SUPERVISORY",
        "future_proof_notes": "Critical for fraud detection and prevention.",
        "evidence_fields": ["sox_profile.whistleblower_policy", "sox_profile.anonymous_reporting", "sox_profile.non_retaliation_policy"],
        "filer_applicability": ["LARGE_ACCELERATED_FILER", "ACCELERATED_FILER", "NON_ACCELERATED_FILER", "SMALLER_REPORTING_COMPANY"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # CODE OF ETHICS
    # ============================================================
    {
        "article": "SOX Code of Ethics",
        "title": "Code of Ethics for Senior Officers",
        "description": "Code of ethics for senior financial officers.",
        "field": "code_of_ethics",
        "severity": "MEDIUM",
        "rule_id": "SOX_CODE_OF_ETHICS",
        "enforcement_scope_default": "SUPERVISORY",
        "future_proof_notes": "Establishes ethical standards for financial reporting.",
        "evidence_fields": ["sox_profile.code_of_ethics", "sox_profile.ethics_training", "sox_profile.ethics_violation_reporting"],
        "filer_applicability": ["LARGE_ACCELERATED_FILER", "ACCELERATED_FILER", "NON_ACCELERATED_FILER", "SMALLER_REPORTING_COMPANY"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # FUTURE SOX ENHANCEMENTS
    # ============================================================
    {
        "article": "SOX Future §404(c)",
        "title": "Continuous Control Monitoring",
        "description": "Continuous monitoring of internal controls using technology.",
        "field": "continuous_control_monitoring",
        "severity": "MEDIUM",
        "rule_id": "SOX_FUTURE_404C_CONTINUOUS_MONITORING",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Future: Real-time control monitoring and automated testing.",
        "evidence_fields": ["sox_profile.continuous_control_monitoring", "sox_profile.real_time_control_testing", "sox_profile.automated_control_validation"],
        "filer_applicability": ["LARGE_ACCELERATED_FILER"],
        "compliance_level": "FUTURE",
        "future_implementation": True,
    },
    {
        "article": "SOX Future §409(b)",
        "title": "AI-Powered Materiality Assessment",
        "description": "AI-powered assessment of materiality for real-time disclosure.",
        "field": "ai_materiality_assessment",
        "severity": "HIGH",
        "rule_id": "SOX_FUTURE_409B_AI_MATERIALITY",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Future: AI algorithms for instant materiality determination.",
        "evidence_fields": ["sox_profile.ai_materiality_assessment", "sox_profile.real_time_materiality_scoring", "sox_profile.predictive_disclosure"],
        "filer_applicability": ["LARGE_ACCELERATED_FILER", "ACCELERATED_FILER"],
        "compliance_level": "FUTURE",
        "future_implementation": True,
    },
]


# ============================================================
# MAIN EVALUATION FUNCTION (Future-Proof Architecture)
# ============================================================

def evaluate_sox_rules(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Future-proof SOX evaluation with comprehensive context gating.
    
    Features:
    1. Enhanced public company detection with confidence scoring
    2. Comprehensive filer classification with dynamic thresholds
    3. Materiality assessment with quantitative impact analysis
    4. Internal control framework evaluation
    5. Material misstatement detection with severity scoring
    6. Enhanced enforcement scope resolution with risk-aware escalation
    7. Comprehensive evidence collection for audit trails
    8. Detailed context tracking and decision logging
    9. Emerging growth company and SRC exemption handling
    10. Future SEC reporting requirement readiness
    
    Returns:
        (policies, summary)
        - policies: List with enforcement_scope, evidence, and context
        - summary: Aggregate statistics with detailed context info
    """
    policies: List[Dict[str, Any]] = []
    
    # ============================================================
    # FUTURE-PROOF: CONTEXT GATING DECISION
    # ============================================================
    is_sox_context, detection_reason, context_evidence = detect_sox_context(payload)
    
    if not is_sox_context:
        # SOX doesn't apply - return with NOT_APPLICABLE
        policies.append({
            "domain": SOX_DOMAIN,
            "regime": SOX_REGIME_ID,
            "framework": SOX_FRAMEWORK,
            "domain_id": SOX_REGIME_ID,
            "article": "SOX Applicability",
            "category": "Applicability",
            "title": "Applicability",
            "status": "NOT_APPLICABLE",
            "severity": "LOW",
            "impact_on_verdict": "COMPLIANT",
            "trigger_type": "NOT_APPLICABLE",
            "rule_ids": ["SOX_APPLICABILITY_NA"],
            "enforcement_scope": "SUPERVISORY",
            "notes": f"SOX evaluation skipped: {detection_reason}",
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
            "regime": SOX_REGIME_ID,
            "context_gated": True,
            "evaluation_decision": detection_reason,
            "context_evidence": context_evidence,
            "notes": f"SOX evaluation skipped: {detection_reason}"
        }
        return policies, summary
    
    # ============================================================
    # CONTEXT INFORMATION COLLECTION
    # ============================================================
    sox_profile = payload.get("sox_profile", {}) or {}
    risk_indicators = payload.get("risk_indicators", {}) or {}
    
    # Assess various factors
    filer_classification, filer_details = classify_sox_filer(payload)
    has_material_misstatement, misstatement_details = detect_material_misstatement(payload)
    control_framework, framework_details = assess_internal_control_framework(payload)
    
    # Extract key flags
    is_large_accelerated = filer_classification == FilerClassification.LARGE_ACCELERATED
    is_emerging_growth = filer_classification == FilerClassification.EMERGING_GROWTH
    is_smaller_reporting = filer_classification == FilerClassification.SMALLER_REPORTING
    is_foreign_private = filer_classification == FilerClassification.FOREIGN_PRIVATE
    
    # ============================================================
    # RULE EVALUATION (Enhanced with Evidence Collection)
    # ============================================================
    
    evaluation_errors = []
    
    for rule_def in SOX_RULES:
        # Skip future implementation rules if not ready
        if rule_def.get("future_implementation") and not sox_profile.get("enable_future_requirements"):
            continue
        
        # Check if rule applies to this filer classification
        applicable_filers = rule_def.get("filer_applicability", [])
        if applicable_filers and filer_classification.value not in applicable_filers:
            continue
        
        # Check for emerging growth company exemptions
        if is_emerging_growth:
            # EGCs can opt out of SOX 404(b) for up to 5 years
            if rule_def["article"] == "SOX §404(b)":
                if sox_profile.get("egc_opted_out_404b"):
                    continue  # Skip if opted out
        
        # Check for smaller reporting company exemptions
        if is_smaller_reporting:
            # SRCs have scaled disclosure requirements
            if rule_def["article"] in ["SOX §404(b)", "SOX Future §404(c)"]:
                continue  # SRCs are exempt from auditor attestation
        
        # Check for foreign private issuer modifications
        if is_foreign_private:
            # FPIs follow Form 20-F requirements
            if rule_def["article"] in ["SOX §409", "SOX §407"]:
                # FPIs have modified disclosure requirements
                pass
        
        try:
            # Check if the required field exists and is compliant
            field_value = sox_profile.get(rule_def["field"])
            
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
            enforcement_scope = resolve_sox_enforcement_scope(rule_def["article"], payload)
            
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
                if has_material_misstatement:
                    if severity == "MEDIUM":
                        severity = "HIGH"
                    elif severity == "HIGH":
                        severity = "CRITICAL"
                
                if is_large_accelerated:
                    if severity == "MEDIUM":
                        severity = "HIGH"
                
                if rule_def["article"] in ["SOX §302", "SOX §906"] and status == "VIOLATED":
                    # CEO/CFO certification violations are critical
                    severity = "CRITICAL"
                
                if rule_def["article"] == "SOX §404" and sox_profile.get("material_weakness"):
                    # Material weakness in internal controls
                    severity = "CRITICAL"
            
            # Create policy
            policy = {
                "domain": SOX_DOMAIN,
                "regime": SOX_REGIME_ID,
                "framework": SOX_FRAMEWORK,
                "domain_id": SOX_REGIME_ID,
                "article": rule_def["article"],
                "category": rule_def["title"],
                "title": rule_def["title"],
                "status": status,
                "severity": severity if status == "VIOLATED" else "LOW",
                "enforcement_scope": enforcement_scope,
                "impact_on_verdict": impact_on_verdict,
                "trigger_type": "SOX_CONTROL",
                "rule_ids": [rule_def["rule_id"]],
                "notes": rule_def["description"],
                "evidence": collect_sox_evidence(payload, rule_evidence),
                "remediation": (
                    f"Implement {rule_def['title']} controls per SOX requirements. "
                    "Document procedures and re-run GNCE after remediation."
                    if status == "VIOLATED" else "No remediation required."
                ),
                "violation_detail": rule_def["description"] if status == "VIOLATED" else "",
                "control_severity": rule_def["severity"],
                # Future-proof metadata
                "metadata": {
                    "filer_classification": filer_classification.value,
                    "filer_applicability": applicable_filers,
                    "compliance_level": rule_def.get("compliance_level", "REQUIRED"),
                    "material_misstatement_detected": has_material_misstatement,
                    "control_framework": control_framework.value,
                    "emerging_growth_exemption": is_emerging_growth,
                    "smaller_reporting_exemption": is_smaller_reporting,
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
        "company_type": payload.get("company_type"),
        "action": payload.get("action"),
        "jurisdiction": (payload.get("meta") or {}).get("jurisdiction"),
        "exchange": (payload.get("meta") or {}).get("exchange"),
        "filer_classification": filer_classification.value,
    }
    
    # Count by requirement type
    certification_violations = sum(1 for p in policies 
                                 if p["status"] == "VIOLATED" and any(
                                     term in p["article"] for term in ["302", "906", "CERTIFICATION"]
                                 ))
    internal_control_violations = sum(1 for p in policies 
                                    if p["status"] == "VIOLATED" and "404" in p["article"])
    disclosure_violations = sum(1 for p in policies 
                              if p["status"] == "VIOLATED" and "409" in p["article"])
    governance_violations = sum(1 for p in policies 
                              if p["status"] == "VIOLATED" and any(
                                  term in p["article"] for term in ["201", "407", "301", "AUDIT"]
                              ))
    misstatement_violations = sum(1 for p in policies 
                                if p["status"] == "VIOLATED" and "MATERIAL_MISSTATEMENT" in p["article"])
    
    # Materiality assessment
    materiality_assessment = {
        "has_material_misstatement": has_material_misstatement,
        "misstatement_severity_score": misstatement_details.get("severity_score", 0),
        "misstatement_indicators": misstatement_details.get("misstatement_indicators", []),
        "material_weakness": sox_profile.get("material_weakness"),
        "significant_deficiency": sox_profile.get("significant_deficiency"),
        "financial_restatement": sox_profile.get("financial_restatement"),
    }
    
    # Internal control assessment
    internal_control_assessment = {
        "control_framework": control_framework.value,
        "framework_details": framework_details,
        "ic_certification": sox_profile.get("ic_certification"),
        "ic_assessment": sox_profile.get("ic_assessment"),
        "auditor_attestation": sox_profile.get("auditor_attestation"),
    }
    
    # Determine overall SOX compliance status
    sox_compliance_status = "COMPLIANT"
    if has_material_misstatement:
        sox_compliance_status = "NON-COMPLIANT"
    elif failed > 0:
        sox_compliance_status = "DEFICIENT"
    elif is_emerging_growth:
        sox_compliance_status = "EGC_EXEMPTIONS_APPLIED"
    elif is_smaller_reporting:
        sox_compliance_status = "SRC_SCALED_DISCLOSURES"
    
    summary = {
        "total_rules": len(policies),
        "passed": passed,
        "failed": failed,
        "blocking_failures": blocking,
        "regime": SOX_REGIME_ID,
        "context_gated": False,
        "evaluation_decision": detection_reason,
        # Context information
        "context": context_info,
        "context_evidence": context_evidence,
        # Filer information
        "filer_classification": filer_classification.value,
        "filer_details": filer_details,
        "is_large_accelerated": is_large_accelerated,
        "is_emerging_growth": is_emerging_growth,
        "is_smaller_reporting": is_smaller_reporting,
        "is_foreign_private": is_foreign_private,
        # Materiality assessment
        "materiality_assessment": materiality_assessment,
        "has_material_misstatement": has_material_misstatement,
        "misstatement_details": misstatement_details,
        # Internal control assessment
        "internal_control_assessment": internal_control_assessment,
        "control_framework": control_framework.value,
        # Violation breakdown
        "certification_violations": certification_violations,
        "internal_control_violations": internal_control_violations,
        "disclosure_violations": disclosure_violations,
        "governance_violations": governance_violations,
        "misstatement_violations": misstatement_violations,
        "large_accelerated_violations": sum(1 for p in policies 
                                          if p["status"] == "VIOLATED" and 
                                          is_large_accelerated),
        # Compliance level breakdown
        "required_violations": sum(1 for p in policies 
                                 if p["status"] == "VIOLATED" and 
                                 p.get("metadata", {}).get("compliance_level") == "REQUIRED"),
        "future_violations": sum(1 for p in policies 
                               if p["status"] == "VIOLATED" and 
                               p.get("metadata", {}).get("compliance_level") == "FUTURE"),
        # Scope breakdown
        "platform_audit_violations": sum(1 for p in policies 
                                       if p["status"] == "VIOLATED" and p.get("enforcement_scope") == "PLATFORM_AUDIT"),
        "transaction_violations": sum(1 for p in policies 
                                    if p["status"] == "VIOLATED" and p.get("enforcement_scope") == "TRANSACTION"),
        "supervisory_violations": sum(1 for p in policies 
                                    if p["status"] == "VIOLATED" and p.get("enforcement_scope") == "SUPERVISORY"),
        # Risk indicators
        "going_concern_issue": risk_indicators.get("going_concern_issue", False),
        "financial_statement_fraud": risk_indicators.get("financial_statement_fraud", False),
        "revenue_recognition_issues": risk_indicators.get("revenue_recognition_issues", False),
        "investigation_active": risk_indicators.get("investigation_active", False),
        # SOX profile information
        "public_company": sox_profile.get("public_company", False),
        "sec_filer": sox_profile.get("sec_filer", False),
        "public_float": sox_profile.get("public_float", 0),
        "revenue": sox_profile.get("revenue", 0),
        # Exemptions and modifications
        "egc_opted_out_404b": sox_profile.get("egc_opted_out_404b", False),
        "egc_transition_period": sox_profile.get("egc_transition_period"),
        "src_scaled_disclosures": sox_profile.get("src_scaled_disclosures", False),
        # Reporting requirements
        "requires_404b_attestation": is_large_accelerated or filer_classification == FilerClassification.ACCELERATED,
        "filing_deadlines": FILER_CLASSIFICATIONS.get(filer_classification, {}).get("filing_deadlines", {}),
        "sox_404b_required": FILER_CLASSIFICATIONS.get(filer_classification, {}).get("sox_404b_required", False),
        # Overall compliance
        "sox_compliance_status": sox_compliance_status,
        "compliance_score": (passed / len(policies)) * 100 if policies else 100,
        # Rule statistics
        "core_rules_evaluated": len([r for r in SOX_RULES if not r.get("future_implementation")]),
        "future_rules_available": len([r for r in SOX_RULES if r.get("future_implementation")]),
        "future_rules_evaluated": len([r for r in SOX_RULES if r.get("future_implementation") 
                                      and sox_profile.get("enable_future_requirements")]),
        # Error tracking
        "evaluation_errors": evaluation_errors if evaluation_errors else None,
    }
    
    return policies, summary