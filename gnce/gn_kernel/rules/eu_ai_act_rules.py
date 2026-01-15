# gnce/gn_kernel/rules/eu_ai_act_rules.py
"""
EU AI Act Rule Evaluator with Constitutional Binding (v0.7.2-RC-FUTUREPROOF)

CRITICAL UPDATES FOR FUTURE-PROOFING:
1. Complete AI system detection with multiple verification methods
2. Comprehensive risk classification (prohibited, high-risk, low-risk, minimal)
3. Enforcement scope resolution with context-aware escalation
4. Industry-aware AI applicability
5. Action-specific AI relevance filtering
6. Enhanced evidence collection for audit trails
7. Cross-domain safety (won't misfire on non-AI systems)
8. Ready for AI Act expansion and amendments

EU AI Act Reality (Future-Proof):
- Art 5: Prohibited practices (TRANSACTION - always blocks)
- Art 6-8: General purpose AI models (TRANSACTION/PLATFORM_AUDIT)
- Art 9-12, 15: Organizational controls (PLATFORM_AUDIT baseline)
- Art 13: Transparency (TRANSACTION - per-interaction)
- Art 14: Human oversight (TRANSACTION - per-decision for high-risk)
- Art 16-29: High-risk AI systems (strict obligations)
- Art 30-39: Transparency obligations for limited-risk AI
- Art 40-52: Governance and enforcement

High-risk escalation: PLATFORM_AUDIT → TRANSACTION for critical obligations
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Set, Tuple
import re

# Load governance catalog for enforcement scope classification
from gnce.gn_kernel.constitution.constitution_catalog import load_governance_catalog_v05

# ============================================================
# MODULE CONSTANTS (FUTURE-PROOF)
# ============================================================

EU_AI_ACT_FRAMEWORK = "AI Governance & Risk Management"
AI_ACT_REGIME_ID = "EU_AI_ACT"

# Load catalog once at module level (performance)
_GOVERNANCE_CATALOG = load_governance_catalog_v05()

# ============================================================
# AI SYSTEM DETECTION (FUTURE-PROOF)
# ============================================================

# AI system indicators (expanded for future-proofing)
AI_SYSTEM_INDICATORS: Set[str] = {
    "machine_learning",
    "deep_learning",
    "neural_network",
    "ai_model",
    "llm",
    "generative_ai",
    "computer_vision",
    "nlp",
    "natural_language_processing",
    "recommendation_system",
    "predictive_analytics",
    "clustering",
    "classification",
    "regression",
    "reinforcement_learning",
    "transformer",
    "diffusion_model",
    "autonomous_system",
    "robotic_process_automation",
    "expert_system",
}

# AI use case categories (future-proof classification)
AI_USE_CASE_CATEGORIES: Set[str] = {
    # High-risk categories (Annex III)
    "biometric_identification",
    "critical_infrastructure",
    "education_vocational",
    "employment_workers",
    "essential_services",
    "law_enforcement",
    "migration_border",
    "justice_democratic",
    "healthcare_diagnosis",
    "medical_device",
    "transportation_safety",
    
    # Limited-risk categories (transparency obligations)
    "chatbot",
    "emotional_recognition",
    "biometric_categorization",
    "deepfake_generation",
    "content_recommendation",
    "ad_targeting",
    "spam_filter",
    "automated_moderation",
    "translation_service",
    "text_summarization",
    
    # Minimal-risk categories (no specific obligations)
    "spell_check",
    "grammar_correction",
    "simple_filter",
    "basic_automation",
    "data_validation",
    "document_classification",
}

# Industries where AI Act typically applies
AI_ACT_INDUSTRIES: Set[str] = {
    "HEALTHCARE",
    "FINTECH",
    "SOCIAL_MEDIA",
    "ECOMMERCE",
    "TRANSPORTATION",
    "EDUCATION",
    "LAW_ENFORCEMENT",
    "GOVERNMENT",
    "INSURANCE",
    "MANUFACTURING",
    "ENERGY",
    "SAAS_B2B",
    "MEDIA",
    "GAMING",
}

# Actions where AI Act obligations are relevant
AI_ACT_RELEVANT_ACTIONS: Set[str] = {
    # High-risk actions
    "diagnose_patient",
    "assess_credit",
    "screen_candidate",
    "monitor_behavior",
    "control_infrastructure",
    "predict_outcome",
    "recommend_treatment",
    "assess_risk",
    "detect_fraud",
    "identify_person",
    
    # Limited-risk actions (transparency required)
    "generate_content",
    "recommend_content",
    "moderate_content",
    "translate_content",
    "summarize_content",
    "classify_content",
    "filter_content",
    "target_advertisement",
    "analyze_sentiment",
    "extract_information",
    
    # Minimal-risk actions
    "correct_spelling",
    "suggest_completion",
    "validate_format",
    "extract_metadata",
    "organize_data",
    "match_patterns",
}

# Actions where AI Act likely doesn't apply (future-proof exclusions)
NON_AI_ACT_ACTIONS: Set[str] = {
    # Non-AI actions
    "login",
    "logout",
    "view_content",
    "download_file",
    "print_document",
    "copy_data",
    "manual_review",
    "human_decision",
    "physical_action",
    
    # System management actions
    "system_backup",
    "update_software",
    "monitor_performance",
    "generate_report",
    "audit_log",
    
    # Simple data operations
    "store_data",
    "retrieve_data",
    "delete_data",
    "list_records",
    "count_items",
}

# ============================================================
# ENFORCEMENT SCOPE RESOLUTION (FUTURE-PROOF)
# ============================================================

def _normalize_article(article: str) -> str:
    """Normalize EU AI Act article references to a stable key.

    Future-proof examples:
      - "AI Act Art. 5" -> "5"
      - "Article 6(1)" -> "6"
      - "Art. 52" -> "52"
      - "Annex III" -> "ANNEX_III"
      - "Art. 28a" -> "28a"
    """
    if not article:
        return ""
    
    s = str(article).strip()
    
    # Remove common prefixes
    s = re.sub(r"(?i)^(eu\s*)?(ai\s*act\s*)?(article|art\.)\s*", "", s)
    
    # Handle annexes
    if "annex" in s.lower():
        # Extract annex number/letter
        match = re.search(r"(?i)annex\s*([ivxlc]+|[a-z])", s)
        if match:
            return f"ANNEX_{match.group(1).upper()}"
    
    # Extract main article number with optional letter (e.g., "28a")
    match = re.match(r"^(\d+[a-z]?)", s)
    if match:
        return match.group(1)
    
    # Return cleaned string for non-standard articles
    return s.strip().upper().replace(" ", "_").replace(".", "")


def _get_ai_act_base_enforcement_scope(article: str) -> str:
    """
    Get base enforcement scope from governance catalog.
    
    Future-proof EU AI Act Classification:
    - Art 5: TRANSACTION (prohibited practices - immediate block)
    - Art 6-8: TRANSACTION/PLATFORM_AUDIT (general purpose AI)
    - Art 9-12: PLATFORM_AUDIT (organizational controls - baseline)
    - Art 13: TRANSACTION (transparency - per-interaction)
    - Art 14: TRANSACTION (human oversight - per-decision)
    - Art 15: PLATFORM_AUDIT (cybersecurity - technical controls)
    - Art 16-29: TRANSACTION (high-risk AI specific obligations)
    - Art 30-39: TRANSACTION (transparency for limited-risk AI)
    - Art 40-52: PLATFORM_AUDIT/SUPERVISORY (governance & enforcement)
    
    High-risk escalation applied separately in _resolve_enforcement_scope
    
    Returns: "TRANSACTION" | "PLATFORM_AUDIT" | "SUPERVISORY"
    Default: "PLATFORM_AUDIT" (safe - logs but doesn't block)
    """
    article_normalized = _normalize_article(article)
    
    for regime in _GOVERNANCE_CATALOG.get("regimes", []):
        if regime.get("id") == AI_ACT_REGIME_ID:
            for domain in regime.get("domains", []):
                for art_def in domain.get("articles", []):
                    art_num = _normalize_article(art_def.get("article", ""))
                    if art_num == article_normalized:
                        return art_def.get("enforcement_scope", "PLATFORM_AUDIT")
    
    # SAFE DEFAULT: PLATFORM_AUDIT (logged, not blocking)
    # Prevents surprise DENYs for new/unmapped articles
    return "PLATFORM_AUDIT"


def _detect_ai_system(payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Future-proof AI system detection with comprehensive verification.
    
    Returns:
        (is_ai_system, detection_evidence)
    """
    detection_evidence = {
        "methods_used": [],
        "indicators_found": [],
        "confidence": "LOW",
    }
    
    ai_profile = payload.get("ai_profile", {})
    meta = payload.get("meta", {})
    
    # Method 1: Explicit AI flags (most reliable)
    if payload.get("is_ai_system") or ai_profile.get("is_ai_system"):
        detection_evidence["methods_used"].append("EXPLICIT_FLAG")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["indicators_found"].append("explicit_ai_flag")
        return True, detection_evidence
    
    # Method 2: AI profile with meaningful content
    if isinstance(ai_profile, dict) and ai_profile:
        meaningful_keys = [
            k for k, v in ai_profile.items() 
            if v not in (None, "", [], {}, False) and k not in ["notes", "description"]
        ]
        if meaningful_keys:
            detection_evidence["methods_used"].append("AI_PROFILE_CONTENT")
            detection_evidence["confidence"] = "MEDIUM"
            detection_evidence["indicators_found"].extend(meaningful_keys[:5])  # Limit to top 5
    
    # Method 3: Model/system type indicators
    model_type = str(ai_profile.get("model_type") or ai_profile.get("system_type") or "").lower()
    if model_type:
        detection_evidence["methods_used"].append("MODEL_TYPE")
        detection_evidence["indicators_found"].append(f"model_type:{model_type}")
        
        # Check if model type contains AI indicators
        if any(indicator in model_type for indicator in AI_SYSTEM_INDICATORS):
            detection_evidence["confidence"] = "HIGH"
            return True, detection_evidence
    
    # Method 4: Use case indicators
    use_case = str(ai_profile.get("use_case") or ai_profile.get("use_case_category") or "").lower()
    if use_case:
        detection_evidence["methods_used"].append("USE_CASE")
        detection_evidence["indicators_found"].append(f"use_case:{use_case}")
        
        if any(indicator in use_case for indicator in AI_SYSTEM_INDICATORS):
            detection_evidence["confidence"] = "MEDIUM"
            return True, detection_evidence
    
    # Method 5: Industry + action context
    industry = str(payload.get("industry_id", "")).upper().strip()
    action = str(payload.get("action", "")).lower().strip()
    
    if industry in AI_ACT_INDUSTRIES and action in AI_ACT_RELEVANT_ACTIONS:
        detection_evidence["methods_used"].append("CONTEXTUAL")
        detection_evidence["confidence"] = "LOW"
        detection_evidence["indicators_found"].append(f"industry:{industry}")
        detection_evidence["indicators_found"].append(f"action:{action}")
        
        # In AI-relevant context, more likely to be AI system
        if detection_evidence["confidence"] != "HIGH":
            detection_evidence["confidence"] = "MEDIUM"
            return True, detection_evidence
    
    # Method 6: Meta/platform signals
    platform_type = str(meta.get("platform_type", "")).lower()
    if "ai" in platform_type or "machine_learning" in platform_type:
        detection_evidence["methods_used"].append("PLATFORM_SIGNAL")
        detection_evidence["confidence"] = "MEDIUM"
        detection_evidence["indicators_found"].append(f"platform_type:{platform_type}")
        return True, detection_evidence
    
    # No AI system detected
    return False, detection_evidence


def _classify_ai_risk(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Classify AI system risk level according to EU AI Act.
    
    Returns:
        (risk_level, classification_evidence)
        risk_level: "PROHIBITED" | "HIGH_RISK" | "LIMITED_RISK" | "MINIMAL_RISK" | "UNKNOWN"
    """
    classification_evidence = {
        "factors_considered": [],
        "category": "UNKNOWN",
        "confidence": "LOW",
    }
    
    ai_profile = payload.get("ai_profile", {})
    
    # Factor 1: Prohibited practices
    if ai_profile.get("prohibited_practice"):
        classification_evidence["factors_considered"].append("PROHIBITED_PRACTICE")
        classification_evidence["category"] = "PROHIBITED"
        classification_evidence["confidence"] = "HIGH"
        return "PROHIBITED", classification_evidence
    
    # Factor 2: Explicit high-risk flag
    if ai_profile.get("high_risk") or ai_profile.get("is_high_risk"):
        classification_evidence["factors_considered"].append("EXPLICIT_HIGH_RISK_FLAG")
        classification_evidence["category"] = "HIGH_RISK"
        classification_evidence["confidence"] = "HIGH"
        return "HIGH_RISK", classification_evidence
    
    # Factor 3: Use case category
    use_case = str(ai_profile.get("use_case_category", "")).lower().strip()
    if use_case:
        classification_evidence["factors_considered"].append(f"USE_CASE:{use_case}")
        
        # Check against known risk categories
        if use_case in {
            "biometric_identification", "critical_infrastructure", "healthcare_diagnosis",
            "law_enforcement", "employment_workers", "education_vocational"
        }:
            classification_evidence["category"] = "HIGH_RISK"
            classification_evidence["confidence"] = "HIGH"
            return "HIGH_RISK", classification_evidence
        elif use_case in {
            "chatbot", "emotional_recognition", "biometric_categorization",
            "deepfake_generation", "content_recommendation"
        }:
            classification_evidence["category"] = "LIMITED_RISK"
            classification_evidence["confidence"] = "MEDIUM"
            return "LIMITED_RISK", classification_evidence
    
    # Factor 4: Risk level from profile
    risk_level = str(ai_profile.get("risk_level", "")).upper().strip()
    if risk_level:
        classification_evidence["factors_considered"].append(f"RISK_LEVEL:{risk_level}")
        
        if risk_level in {"CRITICAL", "HIGH"}:
            classification_evidence["category"] = "HIGH_RISK"
            classification_evidence["confidence"] = "MEDIUM"
            return "HIGH_RISK", classification_evidence
        elif risk_level == "MEDIUM":
            classification_evidence["category"] = "LIMITED_RISK"
            classification_evidence["confidence"] = "MEDIUM"
            return "LIMITED_RISK", classification_evidence
    
    # Factor 5: Industry context
    industry = str(payload.get("industry_id", "")).upper().strip()
    if industry in {"HEALTHCARE", "LAW_ENFORCEMENT", "TRANSPORTATION"}:
        classification_evidence["factors_considered"].append(f"INDUSTRY:{industry}")
        classification_evidence["category"] = "HIGH_RISK"
        classification_evidence["confidence"] = "LOW"  # Industry alone isn't definitive
        return "HIGH_RISK", classification_evidence
    
    # Factor 6: Action context
    action = str(payload.get("action", "")).lower().strip()
    if action in {"diagnose_patient", "assess_credit", "screen_candidate"}:
        classification_evidence["factors_considered"].append(f"ACTION:{action}")
        classification_evidence["category"] = "HIGH_RISK"
        classification_evidence["confidence"] = "MEDIUM"
        return "HIGH_RISK", classification_evidence
    
    # Default: Limited risk (most common for deployed AI)
    classification_evidence["category"] = "LIMITED_RISK"
    classification_evidence["confidence"] = "LOW"
    return "LIMITED_RISK", classification_evidence


def _should_evaluate_ai_act(payload: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Future-proof decision: Should AI Act evaluation run for this payload?
    
    Returns:
        (should_evaluate, evaluation_reason, context_evidence)
    """
    context_evidence = {
        "ai_detection": {},
        "risk_classification": {},
        "context_checks": {},
    }
    
    # Check 1: AI system detection
    is_ai_system, ai_evidence = _detect_ai_system(payload)
    context_evidence["ai_detection"] = ai_evidence
    
    if not is_ai_system:
        return False, "NOT_AI_SYSTEM", context_evidence
    
    # Check 2: Jurisdiction
    meta = payload.get("meta", {})
    jurisdiction = str(meta.get("jurisdiction", "")).upper().strip()
    context_evidence["context_checks"]["jurisdiction"] = jurisdiction
    
    if jurisdiction not in {"EU", "EEA", "EUROPE"}:
        return False, f"JURISDICTION_OUTSIDE_EU: {jurisdiction}", context_evidence
    
    # Check 3: Action relevance
    action = str(payload.get("action", "")).lower().strip()
    context_evidence["context_checks"]["action"] = action
    
    if action in NON_AI_ACT_ACTIONS:
        return False, f"ACTION_EXCLUDED: {action}", context_evidence
    
    # Check 4: Industry relevance
    industry = str(payload.get("industry_id", "")).upper().strip()
    context_evidence["context_checks"]["industry"] = industry
    
    if industry not in AI_ACT_INDUSTRIES:
        # Not a typical AI Act industry, but might still be relevant
        # We'll evaluate anyway but note the industry
        pass
    
    # Check 5: Risk classification
    risk_level, risk_evidence = _classify_ai_risk(payload)
    context_evidence["risk_classification"] = risk_evidence
    
    # All checks passed - evaluate AI Act
    return True, f"EVALUATE_AI_ACT_RISK:{risk_level}", context_evidence


def _resolve_enforcement_scope(article: str, payload: Dict[str, Any]) -> str:
    """
    Resolve final enforcement scope with future-proof modifiers.
    
    EU AI Act Escalation Logic:
    1. Base scope from catalog
    2. Prohibited practices: always TRANSACTION
    3. High-risk AI: escalate critical obligations
    4. Limited-risk AI: escalate transparency obligations
    5. Action-specific escalation
    
    Returns:
        Final enforcement scope after applying modifiers
    """
    base_scope = _get_ai_act_base_enforcement_scope(article)
    article_num = _normalize_article(article)
    
    # Get risk classification
    risk_level, _ = _classify_ai_risk(payload)
    action = str(payload.get("action", "")).lower().strip()
    
    # MODIFIER 1: Prohibited practices always block
    if risk_level == "PROHIBITED" and article_num == "5":
        return "TRANSACTION"
    
    # MODIFIER 2: High-risk AI escalation
    if risk_level == "HIGH_RISK":
        # Critical obligations become transactional for high-risk AI
        if base_scope == "PLATFORM_AUDIT" and article_num in {"9", "10", "14", "15"}:
            # Risk management, data governance, human oversight, cybersecurity
            return "TRANSACTION"
    
    # MODIFIER 3: Limited-risk AI transparency escalation
    if risk_level == "LIMITED_RISK" and article_num == "13":
        # Transparency obligations become transactional for limited-risk AI
        return "TRANSACTION"
    
    # MODIFIER 4: Action-specific escalation
    if base_scope == "PLATFORM_AUDIT":
        # Real-time decisions need transactional enforcement
        if action in {"diagnose_patient", "assess_credit", "screen_candidate"}:
            if article_num in {"9", "14"}:  # Risk management, human oversight
                return "TRANSACTION"
    
    # No modifiers applied - return base scope
    return base_scope


# ============================================================
# RULE DEFINITIONS (Enhanced for Future-Proofing)
# ============================================================

@dataclass(frozen=True)
class EUAIActRule:
    """
    EU AI Act rule definition with future-proof metadata.
    
    Enhanced with:
    - Evidence requirements
    - Risk level applicability
    - Future-proof notes
    - Version compatibility
    """
    rule_id: str
    article: str
    category: str
    severity: str                 # inherent severity
    impact_on_verdict: str
    description: str
    remediation: str
    applies: Callable[[Dict[str, Any]], bool]
    violated: Callable[[Dict[str, Any]], bool]
    evidence_keys: List[str]
    risk_levels: Set[str] = None  # Which risk levels this rule applies to
    future_proof_notes: str = ""
    version_added: str = "v0.7.2"


# ============================================================
# RULE REGISTRY (Enhanced with Future Articles)
# ============================================================

EU_AI_ACT_RULES: List[EUAIActRule] = [
    # ---------------------------
    # Art. 5 – Prohibited practices (PROHIBITED RISK)
    # ---------------------------
    EUAIActRule(
        rule_id="AI_ACT_A5_PROHIBITED_PRACTICE",
        article="AI Act Art. 5",
        category="Prohibited AI practices",
        severity="CRITICAL",
        impact_on_verdict="BLOCKING_FAILURE",
        description="Prohibited practice present (e.g., manipulative/deceptive, social scoring, etc.).",
        remediation=(
            "Remove prohibited AI functionality immediately. Disable deployment, "
            "conduct legal review, and re-run GNCE after full remediation."
        ),
        applies=lambda p: True,  # Applies to all AI systems
        violated=lambda p: bool((p.get("ai_profile") or {}).get("prohibited_practice", False)),
        evidence_keys=["ai_profile.prohibited_practice", "ai_profile.is_ai_system"],
        risk_levels={"PROHIBITED", "HIGH_RISK", "LIMITED_RISK", "MINIMAL_RISK"},
        future_proof_notes="Covers AI systems listed in Article 5: subliminal techniques, exploitation, social scoring, real-time biometric identification.",
    ),

    # ---------------------------
    # High-risk controls (Arts. 9–15) - HIGH_RISK only
    # ---------------------------
    EUAIActRule(
        rule_id="AI_ACT_A9_RISK_MGMT_MISSING",
        article="AI Act Art. 9",
        category="Risk management system",
        severity="HIGH",
        impact_on_verdict="BLOCKING_FAILURE",
        description="High-risk AI requires a risk management system; missing/disabled.",
        remediation="Implement and document a continuous AI risk management system. Re-run GNCE.",
        applies=lambda p: True,  # Applied based on risk level, not lambda
        violated=lambda p: not bool((p.get("ai_profile") or {}).get("risk_management_system", False)),
        evidence_keys=["ai_profile.high_risk", "ai_profile.risk_management_system"],
        risk_levels={"HIGH_RISK"},
        future_proof_notes="Continuous risk management throughout AI lifecycle per Article 9.",
    ),
    EUAIActRule(
        rule_id="AI_ACT_A10_DATA_GOV_MISSING",
        article="AI Act Art. 10",
        category="Data governance",
        severity="HIGH",
        impact_on_verdict="BLOCKING_FAILURE",
        description="High-risk AI requires data governance; missing/disabled.",
        remediation="Establish data governance controls for quality, bias, and relevance. Re-run GNCE.",
        applies=lambda p: True,
        violated=lambda p: not bool((p.get("ai_profile") or {}).get("data_governance", False)),
        evidence_keys=["ai_profile.high_risk", "ai_profile.data_governance"],
        risk_levels={"HIGH_RISK"},
        future_proof_notes="Training, validation, testing data quality and governance per Article 10.",
    ),
    EUAIActRule(
        rule_id="AI_ACT_A11_TECH_DOC_MISSING",
        article="AI Act Art. 11",
        category="Technical documentation",
        severity="MEDIUM",
        impact_on_verdict="NON_BLOCKING",
        description="High-risk AI requires technical documentation; missing/disabled.",
        remediation="Create and maintain technical documentation per AI Act requirements.",
        applies=lambda p: True,
        violated=lambda p: not bool((p.get("ai_profile") or {}).get("technical_documentation", False)),
        evidence_keys=["ai_profile.high_risk", "ai_profile.technical_documentation"],
        risk_levels={"HIGH_RISK"},
        future_proof_notes="Technical documentation must be kept up-to-date per Article 11.",
    ),
    EUAIActRule(
        rule_id="AI_ACT_A12_LOGGING_MISSING",
        article="AI Act Art. 12",
        category="Logging and traceability",
        severity="MEDIUM",
        impact_on_verdict="NON_BLOCKING",
        description="High-risk AI requires logging/traceability; missing/disabled.",
        remediation="Enable logging and traceability mechanisms for AI system outputs.",
        applies=lambda p: True,
        violated=lambda p: not bool((p.get("ai_profile") or {}).get("logging", False)),
        evidence_keys=["ai_profile.high_risk", "ai_profile.logging"],
        risk_levels={"HIGH_RISK"},
        future_proof_notes="Automatically generated logs for traceability per Article 12.",
    ),
    EUAIActRule(
        rule_id="AI_ACT_A13_TRANSPARENCY_MISSING",
        article="AI Act Art. 13",
        category="Transparency to users",
        severity="MEDIUM",
        impact_on_verdict="NON_BLOCKING",
        description="Transparency notice missing for AI system where required.",
        remediation="Provide clear transparency notices to users interacting with the AI system.",
        applies=lambda p: True,
        violated=lambda p: not bool((p.get("ai_profile") or {}).get("transparency_notice", False)),
        evidence_keys=["ai_profile.is_ai_system", "ai_profile.transparency_notice"],
        risk_levels={"HIGH_RISK", "LIMITED_RISK"},
        future_proof_notes="Applies to all high-risk AI and limited-risk AI with transparency obligations.",
    ),
    EUAIActRule(
        rule_id="AI_ACT_A14_HUMAN_OVERSIGHT_MISSING",
        article="AI Act Art. 14",
        category="Human oversight",
        severity="HIGH",
        impact_on_verdict="BLOCKING_FAILURE",
        description="High-risk AI requires human oversight; missing/disabled.",
        remediation="Implement human oversight procedures and escalation paths. Re-run GNCE.",
        applies=lambda p: True,
        violated=lambda p: not bool((p.get("ai_profile") or {}).get("human_oversight", False)),
        evidence_keys=["ai_profile.high_risk", "ai_profile.human_oversight"],
        risk_levels={"HIGH_RISK"},
        future_proof_notes="Human oversight measures to minimize risks per Article 14.",
    ),
    EUAIActRule(
        rule_id="AI_ACT_A15_CYBERSEC_MISSING",
        article="AI Act Art. 15",
        category="Accuracy, robustness, cybersecurity",
        severity="HIGH",
        impact_on_verdict="BLOCKING_FAILURE",
        description="High-risk AI requires robustness/cybersecurity controls; missing/disabled.",
        remediation="Implement robustness testing and cybersecurity controls. Re-run GNCE.",
        applies=lambda p: True,
        violated=lambda p: not bool((p.get("ai_profile") or {}).get("cybersecurity_controls", False)),
        evidence_keys=["ai_profile.high_risk", "ai_profile.cybersecurity_controls"],
        risk_levels={"HIGH_RISK"},
        future_proof_notes="Accuracy, robustness, cybersecurity throughout lifecycle per Article 15.",
    ),

    # ---------------------------
    # General Purpose AI Models (Arts. 6-8) - FUTURE PROOFING
    # ---------------------------
    EUAIActRule(
        rule_id="AI_ACT_A6_GPAI_DOC_MISSING",
        article="AI Act Art. 6",
        category="GPAI model documentation",
        severity="MEDIUM",
        impact_on_verdict="NON_BLOCKING",
        description="General purpose AI model requires technical documentation.",
        remediation="Create technical documentation for GPAI model capabilities and limitations.",
        applies=lambda p: bool((p.get("ai_profile") or {}).get("is_general_purpose", False)),
        violated=lambda p: not bool((p.get("ai_profile") or {}).get("gpai_documentation", False)),
        evidence_keys=["ai_profile.is_general_purpose", "ai_profile.gpai_documentation"],
        risk_levels={"HIGH_RISK", "LIMITED_RISK"},
        future_proof_notes="Placeholder for Article 6 GPAI model documentation.",
        version_added="v0.8.0",
    ),
    EUAIActRule(
        rule_id="AI_ACT_A7_GPAI_COPYRIGHT",
        article="AI Act Art. 7",
        category="GPAI copyright compliance",
        severity="MEDIUM",
        impact_on_verdict="NON_BLOCKING",
        description="General purpose AI model must comply with copyright disclosure.",
        remediation="Implement copyright summary policies and documentation.",
        applies=lambda p: bool((p.get("ai_profile") or {}).get("is_general_purpose", False)),
        violated=lambda p: not bool((p.get("ai_profile") or {}).get("copyright_compliance", False)),
        evidence_keys=["ai_profile.is_general_purpose", "ai_profile.copyright_compliance"],
        risk_levels={"HIGH_RISK", "LIMITED_RISK"},
        future_proof_notes="Placeholder for Article 7 copyright summary policies.",
        version_added="v0.8.0",
    ),

    # ---------------------------
    # Limited-Risk AI (Arts. 50-52) - FUTURE PROOFING
    # ---------------------------
    EUAIActRule(
        rule_id="AI_ACT_A50_EMOTION_RECOGNITION",
        article="AI Act Art. 50",
        category="Emotion recognition transparency",
        severity="LOW",
        impact_on_verdict="NON_BLOCKING",
        description="Emotion recognition AI requires explicit transparency notice.",
        remediation="Provide clear notice when using emotion recognition AI.",
        applies=lambda p: bool((p.get("ai_profile") or {}).get("is_emotion_recognition", False)),
        violated=lambda p: not bool((p.get("ai_profile") or {}).get("emotion_recognition_notice", False)),
        evidence_keys=["ai_profile.is_emotion_recognition", "ai_profile.emotion_recognition_notice"],
        risk_levels={"LIMITED_RISK"},
        future_proof_notes="Placeholder for Article 50 emotion/biometric categorization.",
        version_added="v0.9.0",
    ),
]


# ============================================================
# EVIDENCE COLLECTION (Enhanced for Future-Proofing)
# ============================================================

def _collect_ai_act_evidence(payload: Dict[str, Any], rule: EUAIActRule) -> Dict[str, Any]:
    """
    Collect comprehensive AI Act evidence for audit trails.
    
    Returns:
        Structured evidence with context, rule data, and metadata
    """
    evidence = {
        # Context evidence
        "context": {
            "industry_id": payload.get("industry_id"),
            "action": payload.get("action"),
            "jurisdiction": (payload.get("meta") or {}).get("jurisdiction"),
            "ai_system_detected": True,  # We only evaluate if AI detected
        },
        # Rule-specific evidence
        "rule_data": {},
        # Risk classification
        "risk_classification": {},
        # Metadata
        "metadata": {
            "rule_id": rule.rule_id,
            "article": rule.article,
            "category": rule.category,
            "version_added": rule.version_added,
            "risk_levels": list(rule.risk_levels) if rule.risk_levels else [],
        }
    }
    
    # Collect risk classification
    risk_level, risk_evidence = _classify_ai_risk(payload)
    evidence["risk_classification"] = {
        "level": risk_level,
        "evidence": risk_evidence,
    }
    
    # Collect rule-specific evidence fields
    for field_path in rule.evidence_keys:
        if "." in field_path:
            # Nested field path (e.g., "ai_profile.transparency_notice")
            parts = field_path.split(".")
            obj = payload
            for part in parts[:-1]:
                obj = obj.get(part, {})
            value = obj.get(parts[-1])
            evidence["rule_data"][field_path] = value
        else:
            # Simple field
            evidence["rule_data"][field_path] = payload.get(field_path)
    
    return evidence


# ============================================================
# MAIN EVALUATION FUNCTION (Future-Proof Architecture)
# ============================================================

def evaluate_eu_ai_act_rules(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Future-proof EU AI Act evaluation with comprehensive context gating.
    
    Features:
    1. Multi-method AI system detection
    2. Comprehensive risk classification
    3. Jurisdiction and action filtering
    4. Industry-aware applicability
    5. Enforcement scope resolution with risk escalation
    6. Enhanced evidence collection
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
    should_evaluate, evaluation_reason, context_evidence = _should_evaluate_ai_act(payload)
    
    if not should_evaluate:
        # AI Act doesn't apply to this context - return early with explanation
        summary = {
            "total_rules": 0,
            "passed": 0,
            "failed": 0,
            "blocking_failures": 0,
            "regime": "EU_AI_ACT",
            "context_gated": True,
            "evaluation_decision": evaluation_reason,
            "context_evidence": context_evidence,
            "notes": f"EU AI Act evaluation skipped: {evaluation_reason}"
        }
        return policies, summary
    
    # ============================================================
    # GET RISK CLASSIFICATION
    # ============================================================
    risk_level, risk_evidence = _classify_ai_risk(payload)
    
    # ============================================================
    # RULE EVALUATION (Enhanced with Risk Filtering)
    # ============================================================
    
    evaluation_errors = []
    
    for rule in EU_AI_ACT_RULES:
        # Check if rule applies based on risk level
        if rule.risk_levels and risk_level not in rule.risk_levels:
            # Rule doesn't apply to this risk level
            status = "NOT_APPLICABLE"
            runtime_severity = "LOW"
            notes = f"Not applicable: rule only applies to {rule.risk_levels}, system is {risk_level}"
        else:
            # Rule applies - evaluate it
            try:
                applies = bool(rule.applies(payload))
            except Exception as e:
                applies = False
                evaluation_errors.append({
                    "rule_id": rule.rule_id,
                    "error": f"applies check failed: {str(e)}",
                })

            if not applies:
                status = "NOT_APPLICABLE"
                runtime_severity = "LOW"
                notes = f"Not applicable: {rule.description}"
            else:
                try:
                    violated = bool(rule.violated(payload))
                except Exception as e:
                    violated = False
                    evaluation_errors.append({
                        "rule_id": rule.rule_id,
                        "error": f"violated check failed: {str(e)}",
                    })

                status = "VIOLATED" if violated else "SATISFIED"
                runtime_severity = rule.severity if violated else "LOW"
                notes = rule.description if violated else f"Not triggered: {rule.description}"
        
        # Get enforcement scope with risk-based escalation
        enforcement_scope = _resolve_enforcement_scope(rule.article, payload)
        
        # Create policy with comprehensive evidence
        policies.append(
            {
                "domain": "EU AI Act",
                "regime": "EU_AI_ACT",
                "framework": EU_AI_ACT_FRAMEWORK,
                "domain_id": "EU_AI_ACT",
                "article": rule.article,
                "category": rule.category,
                "title": rule.category,
                "status": status,
                "severity": runtime_severity,
                "control_severity": rule.severity,
                "impact_on_verdict": (
                    rule.impact_on_verdict
                    if status == "VIOLATED"
                    else ("Neutral non-applicable surface." if status == "NOT_APPLICABLE" else "Compliant under tested AI Act obligations.")
                ),
                "trigger_type": "AI_ACT_OBLIGATION",
                "rule_ids": [rule.rule_id],
                "enforcement_scope": enforcement_scope,
                "notes": notes,
                "evidence": _collect_ai_act_evidence(payload, rule),
                "remediation": rule.remediation if status == "VIOLATED" else "No remediation required.",
                "violation_detail": rule.description if status == "VIOLATED" else "",
                # Future-proof metadata
                "metadata": {
                    "risk_level": risk_level,
                    "risk_evidence": risk_evidence,
                    "version_added": rule.version_added,
                    "future_proof_notes": rule.future_proof_notes,
                }
            }
        )
    
    # ============================================================
    # SUMMARY STATISTICS (Comprehensive)
    # ============================================================
    
    # Count ONLY transaction-scoped violations (can block)
    blocking_failures = sum(
        p["status"] == "VIOLATED" 
        and p.get("enforcement_scope") == "TRANSACTION"
        and p["control_severity"] in {"HIGH", "CRITICAL"}
        for p in policies
    )
    
    # Context information for debugging
    context_info = {
        "industry": payload.get("industry_id"),
        "action": payload.get("action"),
        "jurisdiction": (payload.get("meta") or {}).get("jurisdiction"),
        "risk_level": risk_level,
        "ai_profile_exists": bool(payload.get("ai_profile")),
    }
    
    summary = {
        "total_rules": len(policies),
        "passed": sum(p["status"] == "SATISFIED" for p in policies),
        "failed": sum(p["status"] == "VIOLATED" for p in policies),
        "blocking_failures": blocking_failures,
        "regime": "EU_AI_ACT",
        "context_gated": False,
        "evaluation_decision": evaluation_reason,
        "risk_classification": {
            "level": risk_level,
            "evidence": risk_evidence,
        },
        "context_evidence": context_evidence,
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
        # Risk-based statistics
        "rules_by_risk_level": {
            "PROHIBITED": sum(1 for r in EU_AI_ACT_RULES if r.risk_levels and "PROHIBITED" in r.risk_levels),
            "HIGH_RISK": sum(1 for r in EU_AI_ACT_RULES if r.risk_levels and "HIGH_RISK" in r.risk_levels),
            "LIMITED_RISK": sum(1 for r in EU_AI_ACT_RULES if r.risk_levels and "LIMITED_RISK" in r.risk_levels),
            "MINIMAL_RISK": sum(1 for r in EU_AI_ACT_RULES if r.risk_levels and "MINIMAL_RISK" in r.risk_levels),
        },
        # Error tracking
        "evaluation_errors": evaluation_errors if evaluation_errors else None,
    }
    
    return policies, summary