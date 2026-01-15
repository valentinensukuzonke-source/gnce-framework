# gnce/gn_kernel/rules/pci_dss_rules.py
"""
PCI DSS Rule Evaluator with Constitutional Binding and Future-Proofing (v1.0-FUTUREPROOF)

CRITICAL FUTURE-PROOF UPDATES:
1. Enhanced payment card context detection with multi-method verification
2. Merchant/Service Provider classification with dynamic risk assessment
3. Comprehensive PAN (Primary Account Number) detection with Luhn validation
4. Sensitive Authentication Data (SAD) detection with pattern matching
5. PCI DSS v4.0 readiness with requirement mapping
6. Enhanced enforcement scope resolution with risk-aware escalation
7. Comprehensive evidence collection for QSA/ISA audits
8. Cross-domain safety with detailed context gating
9. Breach detection with automated response recommendations
10. Future PCI DSS updates integration ready

PCI DSS REALITY (Future-Proof):
- PCI DSS v3.2.1 (current) with v4.0 migration readiness
- Covers merchants, service providers, and all entities handling payment card data
- Risk-based approach with customized implementations
- 12 core requirements with 250+ sub-requirements
- SAQ (Self-Assessment Questionnaire) or ROC (Report on Compliance) based on level
- Quarterly ASV scans and annual assessments
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple, Set, Optional, Pattern, Callable
import re
import datetime
from enum import Enum

# Load governance catalog for enforcement scope classification
from gnce.gn_kernel.constitution.constitution_catalog import load_governance_catalog_v05

# ============================================================
# MODULE CONSTANTS (FUTURE-PROOF)
# ============================================================

PCI_DSS_DOMAIN = "Payment Card Industry Data Security Standard (PCI DSS)"
PCI_DSS_FRAMEWORK = "Payment Security & Compliance"
PCI_DSS_REGIME_ID = "PCI_DSS"

# PCI DSS versions
PCI_VERSION_CURRENT = "3.2.1"
PCI_VERSION_FUTURE = "4.0"

# Load catalog once at module level (performance)
_GOVERNANCE_CATALOG = load_governance_catalog_v05()

# ============================================================
# PAYMENT CARD DETECTION (FUTURE-PROOF)
# ============================================================

# Payment card data contexts where PCI DSS applies
PAYMENT_CARD_CONTEXTS: Set[str] = {
    "process_payment",
    "authorize_card",
    "settle_transaction",
    "process_refund",
    "charge_customer",
    "store_card_on_file",
    "tokenize_payment",
    "detokenize_payment",
    "manage_recurring_billing",
    "process_chargeback",
    "validate_payment",
    "checkout",
    "point_of_sale",
    "mobile_payment",
    "contactless_payment",
    "card_issuance",
    "card_management",
    "payment_gateway",
    "payment_processor",
    "acquirer_processing",
}

# Industries with payment card handling
PAYMENT_CARD_INDUSTRIES: Set[str] = {
    "RETAIL",
    "E_COMMERCE",
    "FINANCIAL_SERVICES",
    "BANKING",
    "PAYMENT_PROCESSOR",
    "PAYMENT_GATEWAY",
    "ACQUIRER",
    "ISSUER",
    "HOSPITALITY",
    "TRAVEL",
    "GAMING",
    "TELECOM",
    "UTILITIES",
    "INSURANCE",
    "HEALTHCARE",
    "EDUCATION",
    "GOVERNMENT",
    "NONPROFIT",
    "SAAS",
    "MARKETPLACE",
}

# Enhanced PAN patterns for detection with validation
class CardType(Enum):
    VISA = "Visa"
    MASTERCARD = "MasterCard"
    AMEX = "American Express"
    DISCOVER = "Discover"
    DINERS_CLUB = "Diners Club"
    JCB = "JCB"
    MAESTRO = "Maestro"
    UNIONPAY = "UnionPay"
    UNKNOWN = "Unknown"

PAN_PATTERNS: List[Dict[str, Any]] = [
    {
        "type": CardType.VISA,
        "patterns": [re.compile(r'^4[0-9]{12}(?:[0-9]{3})?$')],
        "lengths": [13, 16, 19],
        "iin_ranges": [(400000, 499999)],
    },
    {
        "type": CardType.MASTERCARD,
        "patterns": [
            re.compile(r'^5[1-5][0-9]{14}$'),
            re.compile(r'^2[2-7][0-9]{14}$'),  # Mastercard 2-series
            re.compile(r'^222[1-9][0-9]{12}$'),
            re.compile(r'^22[3-9][0-9]{13}$'),
            re.compile(r'^2[3-6][0-9]{14}$'),
            re.compile(r'^27[0-1][0-9]{13}$'),
            re.compile(r'^2720[0-9]{12}$'),
        ],
        "lengths": [16],
        "iin_ranges": [(510000, 559999), (222100, 272099)],
    },
    {
        "type": CardType.AMEX,
        "patterns": [re.compile(r'^3[47][0-9]{13}$')],
        "lengths": [15],
        "iin_ranges": [(340000, 349999), (370000, 379999)],
    },
    {
        "type": CardType.DISCOVER,
        "patterns": [
            re.compile(r'^6(?:011|5[0-9]{2})[0-9]{12}$'),
            re.compile(r'^64[4-9][0-9]{13}$'),
            re.compile(r'^65[0-9]{14}$'),
            re.compile(r'^622[1-9][0-9]{12}$'),
            re.compile(r'^62212[6-9][0-9]{10}$'),
            re.compile(r'^6221[3-9][0-9]{11}$'),
            re.compile(r'^622[2-8][0-9]{12}$'),
            re.compile(r'^6229[0-1][0-9]{11}$'),
            re.compile(r'^62292[0-5][0-9]{10}$'),
        ],
        "lengths": [16, 19],
        "iin_ranges": [(601100, 601199), (622126, 622925), (644000, 659999)],
    },
    {
        "type": CardType.DINERS_CLUB,
        "patterns": [
            re.compile(r'^3(?:0[0-5]|[68][0-9])[0-9]{11}$'),
            re.compile(r'^30[0-5][0-9]{11}$'),
            re.compile(r'^36[0-9]{12}$'),
            re.compile(r'^38[0-9]{12}$'),
        ],
        "lengths": [14, 15],
        "iin_ranges": [(300000, 305999), (360000, 369999), (380000, 389999)],
    },
    {
        "type": CardType.JCB,
        "patterns": [re.compile(r'^(?:2131|1800|35\d{3})\d{11}$')],
        "lengths": [16, 19],
        "iin_ranges": [(352800, 358999)],
    },
    {
        "type": CardType.MAESTRO,
        "patterns": [re.compile(r'^(?:5018|5020|5038|6304|6759|6761|6763)[0-9]{8,15}$')],
        "lengths": [12, 19],
        "iin_ranges": [(501800, 501899), (502000, 502099), (503800, 503899),
                      (630400, 630499), (675900, 675999), (676100, 676199),
                      (676300, 676399)],
    },
    {
        "type": CardType.UNIONPAY,
        "patterns": [re.compile(r'^62[0-9]{14,17}$')],
        "lengths": [16, 17, 18, 19],
        "iin_ranges": [(620000, 629999)],
    },
]

# Sensitive Authentication Data (SAD) - Full Track Data prohibited
SAD_KEYWORDS: Set[str] = {
    "cvv", "cvc", "cid", "csc", "cvn",  # Card Verification Values
    "cvv2", "cvc2", "cid2",             # Secondary CVV
    "pin", "pin_block",                 # PIN data
    "track", "track1", "track2",        # Track data
    "full_track", "magnetic_stripe",
    "chip", "emv", "icc",               # Chip data
    "caav", "pvv", "dvv", "icvv",       # Other verification values
    "ksn", "derivation_key",            # Key serial numbers
    "cavv", "eci", "xid",               # 3-D Secure data
    "pan", "primary_account_number",    # PAN detection
}

# SAE (Sensitive Authentication Elements) for v4.0
SAE_KEYWORDS: Set[str] = {
    "card_authentication_data",
    "cardholder_authentication_data",
    "authentication_value",
    "authorization_response_cryptogram",
    "cryptogram",
    "token_cryptogram",
}

# ============================================================
# PCI DSS MERCHANT CLASSIFICATION (FUTURE-PROOF)
# ============================================================

# Merchant Levels based on transaction volume (annual)
PCI_MERCHANT_LEVELS = {
    "LEVEL_1": {
        "min_transactions": 6000000,
        "max_transactions": float('inf'),
        "requirements": ["ROC", "QSA", "QUARTERLY_SCANS", "ANNUAL_ASSESSMENT"],
        "description": "Large merchants (>6M transactions annually)",
        "future_requirements": ["CONTINUOUS_MONITORING", "AUTOMATED_CONTROLS"],
    },
    "LEVEL_2": {
        "min_transactions": 1000000,
        "max_transactions": 5999999,
        "requirements": ["ROC", "SAQ_D", "QUARTERLY_SCANS", "ANNUAL_ASSESSMENT"],
        "description": "Medium merchants (1M-6M transactions annually)",
        "future_requirements": ["RISK_ASSESSMENT", "AUTOMATED_REPORTING"],
    },
    "LEVEL_3": {
        "min_transactions": 20000,
        "max_transactions": 999999,
        "requirements": ["SAQ_D", "QUARTERLY_SCANS"],
        "description": "Small merchants (20K-1M e-commerce transactions)",
        "future_requirements": ["BASIC_MONITORING", "VULNERABILITY_SCANNING"],
    },
    "LEVEL_4": {
        "min_transactions": 0,
        "max_transactions": 19999,
        "requirements": ["SAQ_A", "SAQ_A_EP", "SAQ_B", "SAQ_B_IP", "SAQ_C", "SAQ_C_VT", "SAQ_D", "SAQ_P2PE"],
        "description": "Small merchants (<20K e-commerce transactions)",
        "future_requirements": ["BASIC_CONTROLS", "SELF_ASSESSMENT"],
    },
}

# Service Provider Levels
PCI_SERVICE_PROVIDER_LEVELS = {
    "LEVEL_1": {
        "min_transactions": 300000,
        "max_transactions": float('inf'),
        "requirements": ["ROC", "QSA", "ATTESTATION", "QUARTERLY_SCANS"],
        "description": "Large service providers (>300K transactions)",
        "future_requirements": ["ADVANCED_CONTROLS", "REAL_TIME_MONITORING"],
    },
    "LEVEL_2": {
        "min_transactions": 0,
        "max_transactions": 299999,
        "requirements": ["ROC", "ISA", "ATTESTATION"],
        "description": "Small service providers (<300K transactions)",
        "future_requirements": ["BASIC_CONTROLS", "REGULAR_ASSESSMENT"],
    },
}

# PCI DSS v4.0 Customized Approach readiness
PCI_V4_CUSTOMIZED_CONTROLS = {
    "CONTINUOUS_SECURITY_MONITORING": {
        "v3_requirement": "Req. 10",
        "v4_requirement": "Req. 10.2.4",
        "description": "Continuous security monitoring and alerting",
        "maturity_level": "ADVANCED",
    },
    "AUTOMATED_VULNERABILITY_MANAGEMENT": {
        "v3_requirement": "Req. 11",
        "v4_requirement": "Req. 11.3.2",
        "description": "Automated vulnerability management and remediation",
        "maturity_level": "INTERMEDIATE",
    },
    "RISK_BASED_AUTHENTICATION": {
        "v3_requirement": "Req. 8",
        "v4_requirement": "Req. 8.4.2",
        "description": "Risk-based authentication and adaptive controls",
        "maturity_level": "ADVANCED",
    },
    "SECURE_SOFTWARE_DEVELOPMENT": {
        "v3_requirement": "Req. 6",
        "v4_requirement": "Req. 6.2.4",
        "description": "Secure software development lifecycle",
        "maturity_level": "INTERMEDIATE",
    },
}

# ============================================================
# PAYMENT CARD DETECTION (ENHANCED FOR FUTURE-PROOFING)
# ============================================================

def luhn_check(card_number: str) -> bool:
    """
    Luhn algorithm (mod 10) validation for credit card numbers.
    
    Returns:
        True if card number passes Luhn check
        False otherwise
    """
    # Remove non-digit characters
    digits = re.sub(r'\D', '', card_number)
    
    if not digits:
        return False
    
    # Reverse the digits
    reversed_digits = digits[::-1]
    
    total = 0
    for i, digit in enumerate(reversed_digits):
        n = int(digit)
        
        if i % 2 == 1:  # Every second digit (0-indexed, so odd positions)
            n *= 2
            if n > 9:
                n -= 9
        
        total += n
    
    return total % 10 == 0


def detect_pan_type(card_number: str) -> Tuple[Optional[CardType], Dict[str, Any]]:
    """
    Enhanced PAN detection with type identification and validation.
    
    Returns:
        (card_type, detection_details)
    """
    detection_details = {
        "normalized_pan": "",
        "length": 0,
        "iin": None,
        "luhn_valid": False,
        "pattern_matched": False,
        "iin_matched": False,
    }
    
    # Clean and normalize
    clean_pan = re.sub(r'\D', '', card_number)
    if not clean_pan:
        return None, detection_details
    
    detection_details["normalized_pan"] = clean_pan
    detection_details["length"] = len(clean_pan)
    
    # Check IIN (first 6 digits)
    if len(clean_pan) >= 6:
        iin = int(clean_pan[:6])
        detection_details["iin"] = iin
    
    # Check Luhn
    detection_details["luhn_valid"] = luhn_check(clean_pan)
    
    # Check against patterns
    for pattern_info in PAN_PATTERNS:
        for pattern in pattern_info["patterns"]:
            if pattern.match(clean_pan):
                detection_details["pattern_matched"] = True
                
                # Check IIN ranges
                if detection_details["iin"] is not None:
                    for iin_range in pattern_info["iin_ranges"]:
                        if iin_range[0] <= detection_details["iin"] <= iin_range[1]:
                            detection_details["iin_matched"] = True
                            return pattern_info["type"], detection_details
    
    return None, detection_details


def detect_sensitive_authentication_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect Sensitive Authentication Data (SAD) and elements.
    
    Returns:
        Dictionary with SAD detection results
    """
    detection_results = {
        "sad_detected": False,
        "sae_detected": False,
        "sad_types": [],
        "sad_keywords_found": [],
        "context": {},
    }
    
    # Check data_types field
    dts = payload.get("data_types") or payload.get("pci_profile", {}).get("data_types") or []
    if isinstance(dts, str):
        dts = [dts]
    
    dts_lower = [str(x).lower() for x in dts if x is not None]
    
    # Check for SAD keywords
    sad_found = []
    for sad_keyword in SAD_KEYWORDS:
        for dt in dts_lower:
            if sad_keyword in dt:
                sad_found.append(sad_keyword)
                detection_results["sad_detected"] = True
    
    # Check for SAE keywords (v4.0)
    sae_found = []
    for sae_keyword in SAE_KEYWORDS:
        for dt in dts_lower:
            if sae_keyword in dt:
                sae_found.append(sae_keyword)
                detection_results["sae_detected"] = True
    
    detection_results["sad_keywords_found"] = sad_found + sae_found
    
    # Check raw payload fields
    for key, value in payload.items():
        if isinstance(value, str):
            value_lower = value.lower()
            for sad_keyword in SAD_KEYWORDS:
                if sad_keyword in value_lower:
                    if sad_keyword not in detection_results["sad_keywords_found"]:
                        detection_results["sad_keywords_found"].append(sad_keyword)
                    detection_results["sad_detected"] = True
    
    # Classify SAD types
    if detection_results["sad_detected"]:
        sad_types = set()
        for keyword in detection_results["sad_keywords_found"]:
            if keyword in ["cvv", "cvc", "cid", "csc"]:
                sad_types.add("CVV")
            elif keyword in ["pin", "pin_block"]:
                sad_types.add("PIN")
            elif keyword in ["track", "track1", "track2"]:
                sad_types.add("TRACK_DATA")
            elif keyword in ["chip", "emv"]:
                sad_types.add("CHIP_DATA")
            elif keyword == "pan":
                sad_types.add("PAN")
        
        detection_results["sad_types"] = list(sad_types)
    
    return detection_results


def should_evaluate_pci_dss(payload: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Future-proof decision: Should PCI DSS evaluation run for this payload?
    
    Returns:
        (should_evaluate, evaluation_reason, context_evidence)
    """
    context_evidence = {
        "payment_card_detection": {},
        "sad_detection": {},
        "merchant_classification": {},
        "context_checks": {},
    }
    
    # Check 1: Explicit PCI DSS flags
    if payload.get("pci_compliance_required") or payload.get("pci_in_scope"):
        context_evidence["context_checks"]["explicit_pci_flag"] = True
        return True, "EXPLICIT_PCI_FLAG", context_evidence
    
    # Check 2: Action classification
    action = str(payload.get("action", "")).lower().strip()
    context_evidence["context_checks"]["action"] = action
    
    if action in PAYMENT_CARD_CONTEXTS:
        context_evidence["context_checks"]["action_is_payment"] = True
        return True, f"PAYMENT_ACTION: {action}", context_evidence
    
    # Check 3: Industry classification
    industry = str(payload.get("industry_id", "")).upper().strip()
    context_evidence["context_checks"]["industry"] = industry
    
    if industry in PAYMENT_CARD_INDUSTRIES:
        context_evidence["context_checks"]["industry_is_payment"] = True
        
        # Check for payment-specific actions within payment industries
        if any(payment_action in action for payment_action in ["payment", "card", "transaction"]):
            return True, f"PAYMENT_INDUSTRY_WITH_PAYMENT_ACTION: {industry}", context_evidence
    
    # Check 4: PAN detection
    # First check data_types
    dts = payload.get("data_types") or []
    if isinstance(dts, str):
        dts = [dts]
    
    dts_lower = [str(x).lower() for x in dts if x is not None]
    
    pan_keywords = ["pan", "payment card", "card number", "credit card", "debit card"]
    pan_in_datatypes = any(any(kw in dt for kw in pan_keywords) for dt in dts_lower)
    
    context_evidence["payment_card_detection"]["pan_in_datatypes"] = pan_in_datatypes
    
    # Check raw PAN detection
    raw_pan_found = False
    for value in payload.values():
        if isinstance(value, str):
            card_type, detection_details = detect_pan_type(value)
            if card_type:
                raw_pan_found = True
                context_evidence["payment_card_detection"]["raw_pan_found"] = True
                context_evidence["payment_card_detection"]["card_type"] = card_type.value
                context_evidence["payment_card_detection"]["detection_details"] = detection_details
                break
    
    if pan_in_datatypes or raw_pan_found:
        return True, "PAN_DETECTED", context_evidence
    
    # Check 5: SAD detection
    sad_results = detect_sensitive_authentication_data(payload)
    context_evidence["sad_detection"] = sad_results
    
    if sad_results["sad_detected"]:
        return True, "SENSITIVE_AUTHENTICATION_DATA_DETECTED", context_evidence
    
    # Check 6: PCI profile
    pci_profile = payload.get("pci_profile", {})
    if pci_profile.get("in_scope"):
        context_evidence["context_checks"]["pci_profile_in_scope"] = True
        return True, "PCI_PROFILE_IN_SCOPE", context_evidence
    
    # No PCI DSS indicators found
    return False, "NO_PCI_DSS_INDICATORS", context_evidence


# ============================================================
# MERCHANT CLASSIFICATION (ENHANCED)
# ============================================================

def classify_pci_entity(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Classify PCI DSS entity (merchant or service provider) with level.
    
    Returns:
        (entity_classification, classification_details)
        entity_classification: "MERCHANT_LEVEL_1", "SERVICE_PROVIDER_LEVEL_2", etc.
    """
    classification_details = {
        "entity_type": "UNKNOWN",
        "classification_method": "DEFAULT",
        "transaction_volume": 0,
        "annual_transactions": 0,
        "compliance_requirements": [],
        "future_requirements": [],
        "confidence": "LOW",
    }
    
    pci_profile = payload.get("pci_profile", {})
    
    # Method 1: Explicit classification
    explicit_merchant_level = pci_profile.get("merchant_level", "").upper()
    if explicit_merchant_level and explicit_merchant_level.startswith("LEVEL_"):
        classification_details["entity_type"] = "MERCHANT"
        classification_details["classification_method"] = "EXPLICIT"
        classification_details["confidence"] = "HIGH"
        
        # Determine level
        for level_name, level_info in PCI_MERCHANT_LEVELS.items():
            if level_name == explicit_merchant_level:
                classification_details["compliance_requirements"] = level_info["requirements"]
                classification_details["future_requirements"] = level_info.get("future_requirements", [])
                return f"MERCHANT_{level_name}", classification_details
    
    # Method 2: Service provider check
    is_service_provider = pci_profile.get("is_service_provider", False)
    if is_service_provider:
        classification_details["entity_type"] = "SERVICE_PROVIDER"
        classification_details["classification_method"] = "SERVICE_PROVIDER_FLAG"
        
        # Get transaction volume
        annual_transactions = pci_profile.get("annual_transactions", 0)
        classification_details["annual_transactions"] = annual_transactions
        
        # Classify level
        for level_name, level_info in PCI_SERVICE_PROVIDER_LEVELS.items():
            if level_info["min_transactions"] <= annual_transactions <= level_info["max_transactions"]:
                classification_details["compliance_requirements"] = level_info["requirements"]
                classification_details["future_requirements"] = level_info.get("future_requirements", [])
                classification_details["confidence"] = "HIGH"
                return f"SERVICE_PROVIDER_{level_name}", classification_details
    
    # Method 3: Transaction volume classification (merchants)
    annual_transactions = pci_profile.get("annual_transactions", 0)
    classification_details["annual_transactions"] = annual_transactions
    
    for level_name, level_info in PCI_MERCHANT_LEVELS.items():
        if level_info["min_transactions"] <= annual_transactions <= level_info["max_transactions"]:
            classification_details["entity_type"] = "MERCHANT"
            classification_details["classification_method"] = "TRANSACTION_VOLUME"
            classification_details["compliance_requirements"] = level_info["requirements"]
            classification_details["future_requirements"] = level_info.get("future_requirements", [])
            classification_details["confidence"] = "MEDIUM"
            return f"MERCHANT_{level_name}", classification_details
    
    # Default: Level 4 merchant (lowest risk)
    classification_details["entity_type"] = "MERCHANT"
    classification_details["classification_method"] = "DEFAULT"
    classification_details["compliance_requirements"] = PCI_MERCHANT_LEVELS["LEVEL_4"]["requirements"]
    classification_details["future_requirements"] = PCI_MERCHANT_LEVELS["LEVEL_4"].get("future_requirements", [])
    classification_details["confidence"] = "LOW"
    
    return "MERCHANT_LEVEL_4", classification_details


def assess_pci_compliance_status(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assess PCI DSS compliance status with evidence collection.
    
    Returns:
        Compliance assessment results
    """
    assessment = {
        "overall_status": "UNKNOWN",
        "requirements_assessed": {},
        "last_assessment_date": None,
        "next_assessment_due": None,
        "compliance_gaps": [],
        "evidence_collected": {},
    }
    
    pci_profile = payload.get("pci_profile", {})
    
    # Get compliance status
    compliance_status = pci_profile.get("compliance_status", "UNKNOWN")
    assessment["overall_status"] = compliance_status
    
    # Get assessment dates
    assessment["last_assessment_date"] = pci_profile.get("last_assessment_date")
    assessment["next_assessment_due"] = pci_profile.get("next_assessment_due")
    
    # Assess key requirements
    requirements = {
        "REQ_3": {
            "description": "Protect stored cardholder data",
            "status": "NOT_ASSESSED",
            "evidence": {
                "stores_pan": pci_profile.get("stores_pan"),
                "stored_pan_encrypted": pci_profile.get("stored_pan_encrypted"),
                "encryption_standard": pci_profile.get("encryption_standard"),
                "key_management": pci_profile.get("key_management"),
            }
        },
        "REQ_4": {
            "description": "Encrypt transmission of cardholder data",
            "status": "NOT_ASSESSED",
            "evidence": {
                "transmits_pan": pci_profile.get("transmits_pan"),
                "pan_encrypted_in_transit": pci_profile.get("pan_encrypted_in_transit"),
                "tls_version": pci_profile.get("tls_version"),
                "certificate_management": pci_profile.get("certificate_management"),
            }
        },
        "REQ_7": {
            "description": "Restrict access to cardholder data",
            "status": "NOT_ASSESSED",
            "evidence": {
                "access_controls_enforced": pci_profile.get("access_controls_enforced"),
                "rbac_implemented": pci_profile.get("rbac_implemented"),
                "least_privilege": pci_profile.get("least_privilege"),
                "access_reviews": pci_profile.get("access_reviews"),
            }
        },
        "REQ_10": {
            "description": "Log and monitor all access",
            "status": "NOT_ASSESSED",
            "evidence": {
                "logging_enabled": pci_profile.get("logging_enabled"),
                "log_retention": pci_profile.get("log_retention"),
                "siem_implemented": pci_profile.get("siem_implemented"),
                "alerting_configured": pci_profile.get("alerting_configured"),
            }
        },
        "REQ_11": {
            "description": "Regularly test security systems",
            "status": "NOT_ASSESSED",
            "evidence": {
                "vuln_scanning": pci_profile.get("vuln_scanning"),
                "last_vuln_scan": pci_profile.get("last_vuln_scan"),
                "penetration_testing": pci_profile.get("penetration_testing"),
                "last_pen_test": pci_profile.get("last_pen_test"),
                "asv_scans": pci_profile.get("asv_scans"),
            }
        },
    }
    
    # Determine requirement statuses
    for req_id, req_info in requirements.items():
        evidence = req_info["evidence"]
        
        # Simple compliance check (in real implementation would be more sophisticated)
        compliant_indicators = sum(1 for k, v in evidence.items() 
                                 if v is True or (isinstance(v, str) and v.strip()))
        total_indicators = len(evidence)
        
        if total_indicators == 0:
            req_info["status"] = "NOT_ASSESSED"
        elif compliant_indicators == total_indicators:
            req_info["status"] = "COMPLIANT"
        elif compliant_indicators >= total_indicators / 2:
            req_info["status"] = "PARTIALLY_COMPLIANT"
        else:
            req_info["status"] = "NON_COMPLIANT"
            
            # Add to compliance gaps
            gap_details = {
                "requirement": req_id,
                "description": req_info["description"],
                "missing_evidence": [k for k, v in evidence.items() 
                                   if not v or (isinstance(v, str) and not v.strip())],
            }
            assessment["compliance_gaps"].append(gap_details)
    
    assessment["requirements_assessed"] = requirements
    assessment["evidence_collected"] = {
        "pci_profile_summary": {
            "in_scope": pci_profile.get("in_scope"),
            "is_service_provider": pci_profile.get("is_service_provider"),
            "merchant_level": pci_profile.get("merchant_level"),
            "annual_transactions": pci_profile.get("annual_transactions"),
        }
    }
    
    return assessment


# ============================================================
# ENFORCEMENT SCOPE RESOLUTION (FUTURE-PROOF)
# ============================================================

def normalize_pci_article(article: str) -> str:
    """
    Normalize PCI DSS article identifier for consistent comparison.
    
    Future-proof examples:
        "PCI DSS Req. 3" → "3"
        "Req. 3.2.1" → "3.2.1"
        "PCI DSS v4.0 Req. 3.5.1" → "3.5.1"
        "Requirement 12" → "12"
    """
    if not article:
        return ""
    
    article = article.strip()
    
    # Extract requirement number with optional sub-sections
    import re
    
    # Match patterns like: "3", "3.2", "3.2.1", "11.3.2"
    match = re.search(r'(\d+(?:\.\d+)*(?:\.\d+)?)', article)
    if match:
        return match.group(1)
    
    # For non-standard references
    if "BREACH" in article.upper():
        return "BREACH_RESPONSE"
    elif "APPLICABILITY" in article.upper():
        return "APPLICABILITY"
    elif "TOKENIZATION" in article.upper():
        return "TOKENIZATION"
    
    # Return cleaned version
    return re.sub(r'[^\d\.]', '', article)


def get_pci_base_enforcement_scope(article: str) -> str:
    """
    Get base enforcement scope from governance catalog.
    
    Future-proof PCI DSS Classification:
    - Data protection requirements: TRANSACTION (immediate enforcement)
    - Technical controls: PLATFORM_AUDIT (periodic/configuration)
    - Governance requirements: SUPERVISORY (reporting/audit)
    
    Returns: "TRANSACTION" | "PLATFORM_AUDIT" | "SUPERVISORY"
    Default: "TRANSACTION" (sensitive regime - safe default)
    """
    article_normalized = normalize_pci_article(article)
    
    # First check catalog for PCI DSS regime
    for regime in _GOVERNANCE_CATALOG.get("regimes", []):
        if regime.get("id") == PCI_DSS_REGIME_ID:
            for domain in regime.get("domains", []):
                for art_def in domain.get("articles", []):
                    if art_def.get("article", "") == article_normalized:
                        return art_def.get("enforcement_scope", "TRANSACTION")
    
    # Local mapping based on requirement type (v3.2.1 with v4.0 readiness)
    pci_scopes = {
        # Data Protection Requirements (Transaction)
        "3": "TRANSACTION",    # Protect stored cardholder data
        "3.2": "TRANSACTION",  # PAN display masking
        "3.4": "TRANSACTION",  # PAN rendering
        "4": "TRANSACTION",    # Encrypt transmission
        
        # Access Control (Transaction/Platform)
        "7": "TRANSACTION",    # Access control
        "8": "PLATFORM_AUDIT", # Identity and authentication
        "9": "PLATFORM_AUDIT", # Physical access
        
        # Monitoring and Testing (Platform)
        "10": "PLATFORM_AUDIT", # Logging and monitoring
        "11": "PLATFORM_AUDIT", # Security testing
        "11.3": "PLATFORM_AUDIT", # External vulnerability scanning
        
        # Network and Systems (Platform)
        "1": "PLATFORM_AUDIT", # Network security
        "2": "PLATFORM_AUDIT", # Vendor defaults
        "5": "PLATFORM_AUDIT", # Malware protection
        "6": "PLATFORM_AUDIT", # Secure systems
        
        # Governance and Policy (Supervisory)
        "12": "SUPERVISORY",   # Security policy
        
        # Special requirements
        "BREACH_RESPONSE": "TRANSACTION",
        "TOKENIZATION": "TRANSACTION",
        "APPLICABILITY": "SUPERVISORY",
        
        # v4.0 requirements
        "3.5.1": "TRANSACTION",  # v4.0: Account data protection
        "6.2.4": "PLATFORM_AUDIT", # v4.0: Secure software development
        "8.4.2": "TRANSACTION",  # v4.0: Risk-based authentication
        "10.2.4": "PLATFORM_AUDIT", # v4.0: Continuous monitoring
        "11.3.2": "PLATFORM_AUDIT", # v4.0: Automated vulnerability management
    }
    
    # Check for exact match first
    if article_normalized in pci_scopes:
        return pci_scopes[article_normalized]
    
    # Check for parent requirement
    parts = article_normalized.split(".")
    if len(parts) > 1:
        parent_article = parts[0]
        if parent_article in pci_scopes:
            return pci_scopes[parent_article]
    
    return "TRANSACTION"  # Safe default for PCI DSS


def resolve_pci_enforcement_scope(article: str, payload: Dict[str, Any]) -> str:
    """
    Resolve final enforcement scope with future-proof modifiers.
    
    PCI DSS enforcement scope modifiers:
    1. Level 1 merchant/service provider escalation
    2. Active payment card breach escalation
    3. PAN storage/transmission requirements
    4. Sensitive Authentication Data handling
    5. High-risk transactions
    6. Compliance deadline escalation
    
    Returns:
        Final enforcement scope after applying modifiers
    """
    base_scope = get_pci_base_enforcement_scope(article)
    article_normalized = normalize_pci_article(article)
    
    # Get context information
    entity_classification, _ = classify_pci_entity(payload)
    pci_profile = payload.get("pci_profile", {})
    risk_indicators = payload.get("risk_indicators", {})
    
    # Extract entity type and level
    is_level_1 = "LEVEL_1" in entity_classification
    is_service_provider = "SERVICE_PROVIDER" in entity_classification
    
    # MODIFIER 1: Level 1 entity escalation
    if is_level_1:
        if base_scope in {"PLATFORM_AUDIT", "SUPERVISORY"}:
            # Level 1 entities need stricter enforcement
            if article_normalized in {"3", "4", "7", "10"}:  # Critical controls
                return "TRANSACTION"
    
    # MODIFIER 2: Active payment card breach
    if risk_indicators.get("payment_card_breach_active"):
        if base_scope in {"PLATFORM_AUDIT", "SUPERVISORY"}:
            # Breaches escalate all requirements
            return "TRANSACTION"
    
    # MODIFIER 3: PAN handling requirements always transactional
    if article_normalized in {"3", "4", "BREACH_RESPONSE"}:
        return "TRANSACTION"
    
    # MODIFIER 4: Sensitive Authentication Data detection
    sad_detection = detect_sensitive_authentication_data(payload)
    if sad_detection["sad_detected"] and article_normalized == "3":
        # SAD handling requires immediate attention
        return "TRANSACTION"
    
    # MODIFIER 5: High-risk payment activities
    action = str(payload.get("action", "")).lower()
    high_risk_actions = {
        "process_payment", "authorize_card", "settle_transaction", 
        "store_card_on_file", "tokenize_payment"
    }
    
    if action in high_risk_actions and base_scope == "PLATFORM_AUDIT":
        # High-risk payment activities need immediate controls
        return "TRANSACTION"
    
    # MODIFIER 6: Compliance deadlines
    next_assessment_due = pci_profile.get("next_assessment_due")
    if next_assessment_due and base_scope == "SUPERVISORY":
        # Past-due assessments need immediate attention
        # (In real implementation, would parse date and check if overdue)
        return "TRANSACTION"
    
    # MODIFIER 7: Service provider specific escalation
    if is_service_provider and article_normalized in {"3", "4", "7"}:
        # Service providers have stricter data protection requirements
        return "TRANSACTION"
    
    # No modifiers applied
    return base_scope


# ============================================================
# EVIDENCE COLLECTION (Enhanced for PCI DSS)
# ============================================================

def collect_pci_evidence(payload: Dict[str, Any], rule_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect comprehensive PCI DSS evidence for QSA/ISA audits.
    
    Returns:
        Structured evidence with context, rule data, and metadata
    """
    evidence = {
        # Context evidence
        "context": {
            "industry_id": payload.get("industry_id"),
            "action": payload.get("action"),
            "jurisdiction": (payload.get("meta") or {}).get("jurisdiction"),
            "pci_context_detected": True,
        },
        # Rule-specific evidence
        "rule_data": rule_data,
        # PCI DSS-specific information
        "pci_info": {},
        # Audit metadata
        "audit_metadata": {
            "evidence_collected_at": "NOW",  # Would be timestamp in real implementation
            "pci_version": PCI_VERSION_CURRENT,
            "evidence_type": "RULE_EVALUATION",
            "evidence_scope": "PCI_DSS_COMPLIANCE",
        }
    }
    
    # Collect PCI-specific information
    pci_profile = payload.get("pci_profile", {})
    entity_classification, class_details = classify_pci_entity(payload)
    compliance_assessment = assess_pci_compliance_status(payload)
    sad_detection = detect_sensitive_authentication_data(payload)
    
    evidence["pci_info"] = {
        "entity_classification": entity_classification,
        "entity_type": class_details.get("entity_type"),
        "merchant_level": pci_profile.get("merchant_level"),
        "is_service_provider": pci_profile.get("is_service_provider"),
        "annual_transactions": pci_profile.get("annual_transactions"),
        "compliance_status": pci_profile.get("compliance_status"),
        "last_assessment_date": pci_profile.get("last_assessment_date"),
        "next_assessment_due": pci_profile.get("next_assessment_due"),
        "sad_detection": sad_detection,
        "pan_present": detect_pan_type(payload.get("card_number", ""))[0] is not None,
        "compliance_assessment": compliance_assessment,
        "qsa_attested": pci_profile.get("qsa_attested"),
        "roc_on_file": pci_profile.get("roc_on_file"),
        "asv_scans_current": pci_profile.get("asv_scans_current"),
    }
    
    return evidence


# ============================================================
# PCI DSS RULE DEFINITIONS (Enhanced with All Requirements)
# ============================================================

# PCI DSS rules with comprehensive metadata
PCI_DSS_RULES = [
    # ============================================================
    # REQ 1: Install and maintain network security controls
    # ============================================================
    {
        "article": "PCI DSS Req. 1",
        "title": "Network Security Controls",
        "description": "Install and maintain network security controls (firewalls, segmentation).",
        "field": "network_security",
        "severity": "HIGH",
        "rule_id": "PCI_REQ_1_NETWORK_SECURITY",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "v4.0 adds requirements for network segmentation verification.",
        "evidence_fields": ["pci_profile.network_security", "pci_profile.firewall_configuration", "pci_profile.network_segmentation"],
        "entity_applicability": ["MERCHANT_LEVEL_1", "MERCHANT_LEVEL_2", "MERCHANT_LEVEL_3", "MERCHANT_LEVEL_4", "SERVICE_PROVIDER_LEVEL_1", "SERVICE_PROVIDER_LEVEL_2"],
        "compliance_level": "REQUIRED",
        "pci_version": ["3.2.1", "4.0"],
    },
    
    # ============================================================
    # REQ 2: Apply secure configurations
    # ============================================================
    {
        "article": "PCI DSS Req. 2",
        "title": "Secure Configurations",
        "description": "Apply secure configurations to all system components.",
        "field": "secure_configurations",
        "severity": "MEDIUM",
        "rule_id": "PCI_REQ_2_SECURE_CONFIG",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "v4.0 emphasizes automated configuration management.",
        "evidence_fields": ["pci_profile.secure_configurations", "pci_profile.configuration_management", "pci_profile.default_passwords_changed"],
        "entity_applicability": ["MERCHANT_LEVEL_1", "MERCHANT_LEVEL_2", "MERCHANT_LEVEL_3", "MERCHANT_LEVEL_4", "SERVICE_PROVIDER_LEVEL_1", "SERVICE_PROVIDER_LEVEL_2"],
        "compliance_level": "REQUIRED",
        "pci_version": ["3.2.1", "4.0"],
    },
    
    # ============================================================
    # REQ 3: Protect stored account data
    # ============================================================
    {
        "article": "PCI DSS Req. 3",
        "title": "Protect Stored Account Data",
        "description": "Protect stored cardholder data (PAN, SAD) with encryption and other controls.",
        "field": "stores_pan",
        "severity": "CRITICAL",
        "rule_id": "PCI_REQ_3_PROTECT_STORED_DATA",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "v4.0 adds requirements for PAN rendering and display controls.",
        "evidence_fields": ["pci_profile.stores_pan", "pci_profile.stored_pan_encrypted", "pci_profile.encryption_standard", "pci_profile.key_management", "pci_profile.pan_display_masking"],
        "entity_applicability": ["MERCHANT_LEVEL_1", "MERCHANT_LEVEL_2", "MERCHANT_LEVEL_3", "MERCHANT_LEVEL_4", "SERVICE_PROVIDER_LEVEL_1", "SERVICE_PROVIDER_LEVEL_2"],
        "compliance_level": "REQUIRED",
        "pci_version": ["3.2.1", "4.0"],
    },
    {
        "article": "PCI DSS Req. 3.2",
        "title": "PAN Display Masking",
        "description": "Mask PAN when displayed (first 6, last 4 digits only).",
        "field": "pan_display_masking",
        "severity": "HIGH",
        "rule_id": "PCI_REQ_3_2_PAN_MASKING",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Essential for display and logging controls.",
        "evidence_fields": ["pci_profile.pan_display_masking", "pci_profile.display_controls"],
        "entity_applicability": ["MERCHANT_LEVEL_1", "MERCHANT_LEVEL_2", "MERCHANT_LEVEL_3", "MERCHANT_LEVEL_4", "SERVICE_PROVIDER_LEVEL_1", "SERVICE_PROVIDER_LEVEL_2"],
        "compliance_level": "REQUIRED",
        "pci_version": ["3.2.1", "4.0"],
    },
    {
        "article": "PCI DSS Req. 3.4",
        "title": "PAN Rendering",
        "description": "Render PAN unreadable anywhere it is stored.",
        "field": "pan_rendering",
        "severity": "CRITICAL",
        "rule_id": "PCI_REQ_3_4_PAN_RENDERING",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Critical for data at rest protection.",
        "evidence_fields": ["pci_profile.pan_rendering", "pci_profile.encryption_method", "pci_profile.truncation_method"],
        "entity_applicability": ["MERCHANT_LEVEL_1", "MERCHANT_LEVEL_2", "MERCHANT_LEVEL_3", "MERCHANT_LEVEL_4", "SERVICE_PROVIDER_LEVEL_1", "SERVICE_PROVIDER_LEVEL_2"],
        "compliance_level": "REQUIRED",
        "pci_version": ["3.2.1", "4.0"],
    },
    
    # ============================================================
    # REQ 4: Encrypt transmission of cardholder data
    # ============================================================
    {
        "article": "PCI DSS Req. 4",
        "title": "Encrypt Transmission of CHD",
        "description": "Encrypt transmission of cardholder data across open, public networks.",
        "field": "transmits_pan",
        "severity": "CRITICAL",
        "rule_id": "PCI_REQ_4_ENCRYPT_TRANSMISSION",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "v4.0 emphasizes TLS 1.2+ and proper certificate management.",
        "evidence_fields": ["pci_profile.transmits_pan", "pci_profile.pan_encrypted_in_transit", "pci_profile.tls_version", "pci_profile.certificate_management", "pci_profile.cipher_suites"],
        "entity_applicability": ["MERCHANT_LEVEL_1", "MERCHANT_LEVEL_2", "MERCHANT_LEVEL_3", "MERCHANT_LEVEL_4", "SERVICE_PROVIDER_LEVEL_1", "SERVICE_PROVIDER_LEVEL_2"],
        "compliance_level": "REQUIRED",
        "pci_version": ["3.2.1", "4.0"],
    },
    
    # ============================================================
    # REQ 5: Protect all systems against malware
    # ============================================================
    {
        "article": "PCI DSS Req. 5",
        "title": "Malware Protection",
        "description": "Protect all systems against malware and regularly update anti-virus software.",
        "field": "malware_protection",
        "severity": "HIGH",
        "rule_id": "PCI_REQ_5_MALWARE_PROTECTION",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "v4.0 expands to include behavioral analysis and advanced threats.",
        "evidence_fields": ["pci_profile.malware_protection", "pci_profile.antivirus_software", "pci_profile.signature_updates", "pci_profile.behavioral_analysis"],
        "entity_applicability": ["MERCHANT_LEVEL_1", "MERCHANT_LEVEL_2", "MERCHANT_LEVEL_3", "MERCHANT_LEVEL_4", "SERVICE_PROVIDER_LEVEL_1", "SERVICE_PROVIDER_LEVEL_2"],
        "compliance_level": "REQUIRED",
        "pci_version": ["3.2.1", "4.0"],
    },
    
    # ============================================================
    # REQ 6: Develop and maintain secure systems and applications
    # ============================================================
    {
        "article": "PCI DSS Req. 6",
        "title": "Secure Systems and Applications",
        "description": "Develop and maintain secure systems and applications.",
        "field": "secure_development",
        "severity": "HIGH",
        "rule_id": "PCI_REQ_6_SECURE_DEVELOPMENT",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "v4.0 adds requirements for secure software development lifecycle.",
        "evidence_fields": ["pci_profile.secure_development", "pci_profile.sdlc_process", "pci_profile.code_reviews", "pci_profile.vulnerability_management"],
        "entity_applicability": ["MERCHANT_LEVEL_1", "MERCHANT_LEVEL_2", "MERCHANT_LEVEL_3", "MERCHANT_LEVEL_4", "SERVICE_PROVIDER_LEVEL_1", "SERVICE_PROVIDER_LEVEL_2"],
        "compliance_level": "REQUIRED",
        "pci_version": ["3.2.1", "4.0"],
    },
    
    # ============================================================
    # REQ 7: Restrict access to system components and cardholder data
    # ============================================================
    {
        "article": "PCI DSS Req. 7",
        "title": "Restrict Access to CHD",
        "description": "Restrict access to system components and cardholder data by business need to know.",
        "field": "access_controls_enforced",
        "severity": "CRITICAL",
        "rule_id": "PCI_REQ_7_ACCESS_CONTROL",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "v4.0 emphasizes least privilege and just-in-time access.",
        "evidence_fields": ["pci_profile.access_controls_enforced", "pci_profile.rbac_implemented", "pci_profile.least_privilege", "pci_profile.access_reviews", "pci_profile.just_in_time_access"],
        "entity_applicability": ["MERCHANT_LEVEL_1", "MERCHANT_LEVEL_2", "MERCHANT_LEVEL_3", "MERCHANT_LEVEL_4", "SERVICE_PROVIDER_LEVEL_1", "SERVICE_PROVIDER_LEVEL_2"],
        "compliance_level": "REQUIRED",
        "pci_version": ["3.2.1", "4.0"],
    },
    
    # ============================================================
    # REQ 8: Identify and authenticate access to system components
    # ============================================================
    {
        "article": "PCI DSS Req. 8",
        "title": "Identity and Authentication",
        "description": "Identify and authenticate access to system components.",
        "field": "authentication_controls",
        "severity": "HIGH",
        "rule_id": "PCI_REQ_8_AUTHENTICATION",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "v4.0 adds risk-based authentication and MFA for all access.",
        "evidence_fields": ["pci_profile.authentication_controls", "pci_profile.mfa_implemented", "pci_profile.password_policy", "pci_profile.risk_based_auth", "pci_profile.session_management"],
        "entity_applicability": ["MERCHANT_LEVEL_1", "MERCHANT_LEVEL_2", "MERCHANT_LEVEL_3", "MERCHANT_LEVEL_4", "SERVICE_PROVIDER_LEVEL_1", "SERVICE_PROVIDER_LEVEL_2"],
        "compliance_level": "REQUIRED",
        "pci_version": ["3.2.1", "4.0"],
    },
    
    # ============================================================
    # REQ 9: Restrict physical access to cardholder data
    # ============================================================
    {
        "article": "PCI DSS Req. 9",
        "title": "Physical Access Control",
        "description": "Restrict physical access to cardholder data.",
        "field": "physical_access_controls",
        "severity": "MEDIUM",
        "rule_id": "PCI_REQ_9_PHYSICAL_ACCESS",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Important for on-premises systems and data centers.",
        "evidence_fields": ["pci_profile.physical_access_controls", "pci_profile.access_logs", "pci_profile.visitor_management", "pci_profile.surveillance"],
        "entity_applicability": ["MERCHANT_LEVEL_1", "MERCHANT_LEVEL_2", "MERCHANT_LEVEL_3", "MERCHANT_LEVEL_4", "SERVICE_PROVIDER_LEVEL_1", "SERVICE_PROVIDER_LEVEL_2"],
        "compliance_level": "REQUIRED",
        "pci_version": ["3.2.1", "4.0"],
    },
    
    # ============================================================
    # REQ 10: Log and monitor all access to system components and cardholder data
    # ============================================================
    {
        "article": "PCI DSS Req. 10",
        "title": "Logging and Monitoring",
        "description": "Log and monitor all access to system components and cardholder data.",
        "field": "logging_enabled",
        "severity": "HIGH",
        "rule_id": "PCI_REQ_10_LOGGING",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "v4.0 adds continuous security monitoring requirements.",
        "evidence_fields": ["pci_profile.logging_enabled", "pci_profile.log_retention", "pci_profile.siem_implemented", "pci_profile.alerting_configured", "pci_profile.continuous_monitoring"],
        "entity_applicability": ["MERCHANT_LEVEL_1", "MERCHANT_LEVEL_2", "MERCHANT_LEVEL_3", "MERCHANT_LEVEL_4", "SERVICE_PROVIDER_LEVEL_1", "SERVICE_PROVIDER_LEVEL_2"],
        "compliance_level": "REQUIRED",
        "pci_version": ["3.2.1", "4.0"],
    },
    
    # ============================================================
    # REQ 11: Regularly test security systems and processes
    # ============================================================
    {
        "article": "PCI DSS Req. 11",
        "title": "Security Testing",
        "description": "Regularly test security systems and processes.",
        "field": "vuln_scanning",
        "severity": "HIGH",
        "rule_id": "PCI_REQ_11_SECURITY_TESTING",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "v4.0 adds automated vulnerability management requirements.",
        "evidence_fields": ["pci_profile.vuln_scanning", "pci_profile.last_vuln_scan", "pci_profile.penetration_testing", "pci_profile.last_pen_test", "pci_profile.asv_scans", "pci_profile.automated_vuln_management"],
        "entity_applicability": ["MERCHANT_LEVEL_1", "MERCHANT_LEVEL_2", "MERCHANT_LEVEL_3", "MERCHANT_LEVEL_4", "SERVICE_PROVIDER_LEVEL_1", "SERVICE_PROVIDER_LEVEL_2"],
        "compliance_level": "REQUIRED",
        "pci_version": ["3.2.1", "4.0"],
    },
    
    # ============================================================
    # REQ 12: Maintain a policy that addresses information security
    # ============================================================
    {
        "article": "PCI DSS Req. 12",
        "title": "Security Policy",
        "description": "Maintain a policy that addresses information security for all personnel.",
        "field": "security_policy",
        "severity": "MEDIUM",
        "rule_id": "PCI_REQ_12_SECURITY_POLICY",
        "enforcement_scope_default": "SUPERVISORY",
        "future_proof_notes": "v4.0 adds risk assessment and targeted risk analysis requirements.",
        "evidence_fields": ["pci_profile.security_policy", "pci_profile.policy_review_frequency", "pci_profile.risk_assessment", "pci_profile.security_awareness_training", "pci_profile.incident_response_plan"],
        "entity_applicability": ["MERCHANT_LEVEL_1", "MERCHANT_LEVEL_2", "MERCHANT_LEVEL_3", "MERCHANT_LEVEL_4", "SERVICE_PROVIDER_LEVEL_1", "SERVICE_PROVIDER_LEVEL_2"],
        "compliance_level": "REQUIRED",
        "pci_version": ["3.2.1", "4.0"],
    },
    
    # ============================================================
    # BREACH DETECTION AND RESPONSE
    # ============================================================
    {
        "article": "PCI DSS Breach Response",
        "title": "Breach Detection & Response",
        "description": "Detect and respond to payment card data breaches.",
        "field": "breach_detection",
        "severity": "CRITICAL",
        "rule_id": "PCI_BREACH_RESPONSE",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Critical for compliance and incident management.",
        "evidence_fields": ["pci_profile.breach_detection", "pci_profile.incident_response_plan", "pci_profile.breach_investigation_active", "pci_profile.forensic_readiness"],
        "entity_applicability": ["MERCHANT_LEVEL_1", "MERCHANT_LEVEL_2", "MERCHANT_LEVEL_3", "MERCHANT_LEVEL_4", "SERVICE_PROVIDER_LEVEL_1", "SERVICE_PROVIDER_LEVEL_2"],
        "compliance_level": "REQUIRED",
        "pci_version": ["3.2.1", "4.0"],
    },
    
    # ============================================================
    # TOKENIZATION
    # ============================================================
    {
        "article": "PCI DSS Tokenization",
        "title": "Tokenization",
        "description": "Implement tokenization to reduce PCI DSS scope.",
        "field": "tokenization_implemented",
        "severity": "MEDIUM",
        "rule_id": "PCI_TOKENIZATION",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Critical for scope reduction and security.",
        "evidence_fields": ["pci_profile.tokenization_implemented", "pci_profile.tokenization_method", "pci_profile.token_vault_security", "pci_profile.detokenization_controls"],
        "entity_applicability": ["MERCHANT_LEVEL_1", "MERCHANT_LEVEL_2", "MERCHANT_LEVEL_3", "MERCHANT_LEVEL_4", "SERVICE_PROVIDER_LEVEL_1", "SERVICE_PROVIDER_LEVEL_2"],
        "compliance_level": "ADDRESSABLE",
        "pci_version": ["3.2.1", "4.0"],
    },
    
    # ============================================================
    # PCI DSS v4.0 CUSTOMIZED APPROACH (Future readiness)
    # ============================================================
    {
        "article": "PCI DSS v4.0 Continuous Monitoring",
        "title": "Continuous Security Monitoring",
        "description": "Implement continuous security monitoring per PCI DSS v4.0.",
        "field": "continuous_monitoring",
        "severity": "HIGH",
        "rule_id": "PCI_V4_CONTINUOUS_MONITORING",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "v4.0 requirement 10.2.4: Continuous security monitoring.",
        "evidence_fields": ["pci_profile.continuous_monitoring", "pci_profile.real_time_alerting", "pci_profile.security_analytics", "pci_profile.threat_intelligence"],
        "entity_applicability": ["MERCHANT_LEVEL_1", "SERVICE_PROVIDER_LEVEL_1"],
        "compliance_level": "FUTURE",
        "pci_version": ["4.0"],
        "future_implementation": True,
    },
    {
        "article": "PCI DSS v4.0 Automated Vulnerability Management",
        "title": "Automated Vulnerability Management",
        "description": "Implement automated vulnerability management per PCI DSS v4.0.",
        "field": "automated_vuln_management",
        "severity": "HIGH",
        "rule_id": "PCI_V4_AUTOMATED_VULN_MGMT",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "v4.0 requirement 11.3.2: Automated vulnerability management.",
        "evidence_fields": ["pci_profile.automated_vuln_management", "pci_profile.vuln_remediation", "pci_profile.patch_management", "pci_profile.vulnerability_scoring"],
        "entity_applicability": ["MERCHANT_LEVEL_1", "SERVICE_PROVIDER_LEVEL_1"],
        "compliance_level": "FUTURE",
        "pci_version": ["4.0"],
        "future_implementation": True,
    },
    {
        "article": "PCI DSS v4.0 Risk-Based Authentication",
        "title": "Risk-Based Authentication",
        "description": "Implement risk-based authentication per PCI DSS v4.0.",
        "field": "risk_based_auth",
        "severity": "HIGH",
        "rule_id": "PCI_V4_RISK_BASED_AUTH",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "v4.0 requirement 8.4.2: Risk-based authentication.",
        "evidence_fields": ["pci_profile.risk_based_auth", "pci_profile.adaptive_auth", "pci_profile.risk_scoring", "pci_profile.behavioral_analysis"],
        "entity_applicability": ["MERCHANT_LEVEL_1", "SERVICE_PROVIDER_LEVEL_1"],
        "compliance_level": "FUTURE",
        "pci_version": ["4.0"],
        "future_implementation": True,
    },
    {
        "article": "PCI DSS v4.0 Secure Software Development",
        "title": "Secure Software Development",
        "description": "Implement secure software development lifecycle per PCI DSS v4.0.",
        "field": "secure_sdlc",
        "severity": "HIGH",
        "rule_id": "PCI_V4_SECURE_SDLC",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "v4.0 requirement 6.2.4: Secure software development.",
        "evidence_fields": ["pci_profile.secure_sdlc", "pci_profile.developer_training", "pci_profile.code_analysis", "pci_profile.software_composition_analysis"],
        "entity_applicability": ["MERCHANT_LEVEL_1", "SERVICE_PROVIDER_LEVEL_1"],
        "compliance_level": "FUTURE",
        "pci_version": ["4.0"],
        "future_implementation": True,
    },
]


# ============================================================
# MAIN EVALUATION FUNCTION (Future-Proof Architecture)
# ============================================================

def evaluate_pci_dss_rules(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Future-proof PCI DSS evaluation with comprehensive context gating.
    
    Features:
    1. Enhanced payment card detection with multi-method verification
    2. Merchant/service provider classification with dynamic level assessment
    3. Sensitive Authentication Data detection
    4. PCI DSS v4.0 readiness with requirement mapping
    5. Enhanced enforcement scope resolution with risk-aware escalation
    6. Comprehensive evidence collection for QSA/ISA audits
    7. Detailed context tracking and decision logging
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
    should_evaluate, evaluation_reason, context_evidence = should_evaluate_pci_dss(payload)
    
    if not should_evaluate:
        # PCI DSS doesn't apply - return with NOT_APPLICABLE
        policies.append({
            "domain": PCI_DSS_DOMAIN,
            "regime": PCI_DSS_REGIME_ID,
            "framework": PCI_DSS_FRAMEWORK,
            "domain_id": PCI_DSS_REGIME_ID,
            "article": "PCI DSS Applicability",
            "category": "Applicability",
            "title": "Applicability",
            "status": "NOT_APPLICABLE",
            "severity": "LOW",
            "impact_on_verdict": "COMPLIANT",
            "trigger_type": "NOT_APPLICABLE",
            "rule_ids": ["PCI_DSS_APPLICABILITY_NA"],
            "enforcement_scope": "SUPERVISORY",
            "notes": f"PCI DSS evaluation skipped: {evaluation_reason}",
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
            "regime": PCI_DSS_REGIME_ID,
            "context_gated": True,
            "evaluation_decision": evaluation_reason,
            "context_evidence": context_evidence,
            "notes": f"PCI DSS evaluation skipped: {evaluation_reason}"
        }
        return policies, summary
    
    # ============================================================
    # CONTEXT INFORMATION COLLECTION
    # ============================================================
    entity_classification, classification_details = classify_pci_entity(payload)
    compliance_assessment = assess_pci_compliance_status(payload)
    sad_detection = detect_sensitive_authentication_data(payload)
    pci_profile = payload.get("pci_profile", {}) or {}
    risk_indicators = payload.get("risk_indicators", {}) or {}
    
    # Extract entity type and level
    is_level_1 = "LEVEL_1" in entity_classification
    is_service_provider = "SERVICE_PROVIDER" in entity_classification
    
    # ============================================================
    # RULE EVALUATION (Enhanced with Evidence Collection)
    # ============================================================
    
    evaluation_errors = []
    
    for rule_def in PCI_DSS_RULES:
        # Skip future implementation rules if not ready
        if rule_def.get("future_implementation") and not pci_profile.get("enable_future_requirements"):
            continue
        
        # Check if rule applies to this entity type
        applicable_entities = rule_def.get("entity_applicability", [])
        if applicable_entities and entity_classification not in applicable_entities:
            continue
        
        try:
            # Check if the required field exists and is compliant
            field_value = pci_profile.get(rule_def["field"])
            
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
                elif compliance_level == "ADDRESSABLE":
                    status = "NOT_APPLICABLE"  # Addressable means can choose to implement
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
            enforcement_scope = resolve_pci_enforcement_scope(rule_def["article"], payload)
            
            # Determine impact on verdict
            if status == "VIOLATED" and rule_def["severity"] in {"HIGH", "CRITICAL"}:
                impact_on_verdict = "BLOCKING_FAILURE"
            elif status == "VIOLATED":
                impact_on_verdict = "NON_BLOCKING"
            else:
                impact_on_verdict = "COMPLIANT"
            
            # Determine severity based on context
            severity = rule_def["severity"]
            if status == "VIOLATED" and is_level_1:
                # Escalate severity for Level 1 entities
                if severity == "MEDIUM":
                    severity = "HIGH"
                elif severity == "HIGH":
                    severity = "CRITICAL"
            
            # Check for active breaches that escalate severity
            if status == "VIOLATED" and risk_indicators.get("payment_card_breach_active"):
                if severity == "MEDIUM":
                    severity = "HIGH"
                elif severity == "HIGH":
                    severity = "CRITICAL"
            
            # Check for SAD detection that escalates severity
            if status == "VIOLATED" and sad_detection["sad_detected"] and rule_def["article"] in {"PCI DSS Req. 3", "3"}:
                severity = "CRITICAL"
            
            # Create policy
            policy = {
                "domain": PCI_DSS_DOMAIN,
                "regime": PCI_DSS_REGIME_ID,
                "framework": PCI_DSS_FRAMEWORK,
                "domain_id": PCI_DSS_REGIME_ID,
                "article": rule_def["article"],
                "category": rule_def["title"],
                "title": rule_def["title"],
                "status": status,
                "severity": severity if status == "VIOLATED" else "LOW",
                "enforcement_scope": enforcement_scope,
                "impact_on_verdict": impact_on_verdict,
                "trigger_type": "PCI_DSS_CONTROL",
                "rule_ids": [rule_def["rule_id"]],
                "notes": rule_def["description"],
                "evidence": collect_pci_evidence(payload, rule_evidence),
                "remediation": (
                    f"Implement {rule_def['title']} controls per PCI DSS requirements. "
                    "Document procedures and re-run GNCE after remediation."
                    if status == "VIOLATED" else "No remediation required."
                ),
                "violation_detail": rule_def["description"] if status == "VIOLATED" else "",
                "control_severity": rule_def["severity"],
                # Future-proof metadata
                "metadata": {
                    "entity_classification": entity_classification,
                    "entity_applicability": applicable_entities,
                    "compliance_level": rule_def.get("compliance_level", "REQUIRED"),
                    "pci_version": rule_def.get("pci_version", ["3.2.1"]),
                    "sad_detected": sad_detection["sad_detected"],
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
        "entity_classification": entity_classification,
        "payment_card_detected": True,
    }
    
    # Count by requirement type
    data_protection_violations = sum(1 for p in policies 
                                   if p["status"] == "VIOLATED" and any(
                                       req in p["article"] for req in ["3", "4", "PCI DSS Req. 3", "PCI DSS Req. 4"]
                                   ))
    access_control_violations = sum(1 for p in policies 
                                  if p["status"] == "VIOLATED" and any(
                                      req in p["article"] for req in ["7", "8", "PCI DSS Req. 7", "PCI DSS Req. 8"]
                                  ))
    monitoring_violations = sum(1 for p in policies 
                              if p["status"] == "VIOLATED" and any(
                                  req in p["article"] for req in ["10", "11", "PCI DSS Req. 10", "PCI DSS Req. 11"]
                              ))
    breach_violations = sum(1 for p in policies 
                          if p["status"] == "VIOLATED" and "Breach" in p.get("category", ""))
    
    # Compliance assessment statistics
    compliance_stats = {
        "overall_status": compliance_assessment.get("overall_status"),
        "compliance_gaps": len(compliance_assessment.get("compliance_gaps", [])),
        "requirements_assessed": len(compliance_assessment.get("requirements_assessed", {})),
    }
    
    summary = {
        "total_rules": len(policies),
        "passed": passed,
        "failed": failed,
        "blocking_failures": blocking,
        "regime": PCI_DSS_REGIME_ID,
        "context_gated": False,
        "evaluation_decision": evaluation_reason,
        # Context information
        "context": context_info,
        "context_evidence": context_evidence,
        # Entity classification
        "entity_classification": entity_classification,
        "classification_details": classification_details,
        # SAD detection
        "sad_detection": sad_detection,
        # Compliance assessment
        "compliance_assessment": compliance_assessment,
        "compliance_stats": compliance_stats,
        # Violation breakdown
        "data_protection_violations": data_protection_violations,
        "access_control_violations": access_control_violations,
        "monitoring_violations": monitoring_violations,
        "breach_violations": breach_violations,
        "level_1_violations": sum(1 for p in policies 
                                if p["status"] == "VIOLATED" and 
                                is_level_1),
        # Compliance level breakdown
        "required_violations": sum(1 for p in policies 
                                 if p["status"] == "VIOLATED" and 
                                 p.get("metadata", {}).get("compliance_level") == "REQUIRED"),
        "addressable_violations": sum(1 for p in policies 
                                    if p["status"] == "VIOLATED" and 
                                    p.get("metadata", {}).get("compliance_level") == "ADDRESSABLE"),
        # Scope breakdown
        "platform_audit_violations": sum(1 for p in policies 
                                       if p["status"] == "VIOLATED" and p.get("enforcement_scope") == "PLATFORM_AUDIT"),
        "transaction_violations": sum(1 for p in policies 
                                    if p["status"] == "VIOLATED" and p.get("enforcement_scope") == "TRANSACTION"),
        "supervisory_violations": sum(1 for p in policies 
                                    if p["status"] == "VIOLATED" and p.get("enforcement_scope") == "SUPERVISORY"),
        # Risk indicators
        "active_payment_card_breach": risk_indicators.get("payment_card_breach_active", False),
        "breach_detected": risk_indicators.get("payment_card_breach_detected", False),
        "breach_investigation_active": pci_profile.get("breach_investigation_active", False),
        # Rule statistics
        "v3_rules_evaluated": len([r for r in PCI_DSS_RULES if "3.2.1" in r.get("pci_version", [])]),
        "v4_rules_available": len([r for r in PCI_DSS_RULES if "4.0" in r.get("pci_version", [])]),
        "v4_rules_evaluated": len([r for r in PCI_DSS_RULES if "4.0" in r.get("pci_version", []) 
                                   and pci_profile.get("enable_future_requirements")]),
        # PCI DSS reporting requirements
        "requires_saq": not is_service_provider and "LEVEL_4" in entity_classification,
        "requires_roc": is_service_provider or "LEVEL_1" in entity_classification or "LEVEL_2" in entity_classification,
        "requires_asv_scans": is_level_1 or (is_service_provider and "LEVEL_1" in entity_classification),
        # Entity details
        "is_service_provider": is_service_provider,
        "is_level_1": is_level_1,
        "annual_transactions": pci_profile.get("annual_transactions", 0),
        # Error tracking
        "evaluation_errors": evaluation_errors if evaluation_errors else None,
    }
    
    return policies, summary