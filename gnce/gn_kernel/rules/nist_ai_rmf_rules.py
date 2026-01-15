# gnce/gn_kernel/rules/nist_ai_rmf_rules.py
"""
NIST AI Risk Management Framework (AI RMF) Evaluator with Constitutional Binding (v0.7.2-RC-FUTUREPROOF)

CRITICAL UPDATES FOR FUTURE-PROOFING:
1. Comprehensive AI system detection with multi-method verification
2. NIST AI RMF 1.0 core functions: GOVERN, MAP, MEASURE, MANAGE
3. AI system risk profiling and categorization
4. Trustworthy AI characteristics with evidence-based assessment
5. Cross-framework alignment with ISO 42001, EU AI Act, and NIST CSF
6. Enhanced enforcement scope resolution with risk-aware escalation
7. Comprehensive evidence collection for audit trails
8. Cross-domain safety (won't misfire on non-AI systems)
9. Future NIST AI RMF updates ready for implementation

NIST AI RMF 1.0 Reality (Future-Proof):
- Core Functions: GOVERN, MAP, MEASURE, MANAGE
- Trustworthy AI Characteristics: Valid/Reliable, Safe/Secure, Resilient/Robust, Accountable/Transparent, Explainable/Interpretable, Privacy-Enhanced, Fair with Harmful Bias Managed
- AI System Lifecycle Integration: Design, Development, Deployment, Operation, Monitoring
- Risk-based approach to AI governance and management
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple, Set, Optional
import re

# Load governance catalog for enforcement scope classification
from gnce.gn_kernel.constitution.constitution_catalog import load_governance_catalog_v05

# ============================================================
# MODULE CONSTANTS (FUTURE-PROOF)
# ============================================================

NIST_AI_RMF_DOMAIN = "AI Risk Management Framework (NIST AI RMF 1.0)"
NIST_AI_RMF_FRAMEWORK = "AI Risk Management"
NIST_AI_RMF_REGIME_ID = "NIST_AI_RMF"

# Load catalog once at module level (performance)
_GOVERNANCE_CATALOG = load_governance_catalog_v05()

# ============================================================
# AI SYSTEM DETECTION (FUTURE-PROOF)
# ============================================================

# NIST AI RMF AI system types
NIST_AI_SYSTEM_TYPES: Set[str] = {
    "machine_learning",
    "deep_learning",
    "neural_network",
    "llm",
    "large_language_model",
    "generative_ai",
    "computer_vision",
    "natural_language_processing",
    "predictive_analytics",
    "recommendation_system",
    "autonomous_system",
    "robotic_process_automation",
    "expert_system",
    "reinforcement_learning",
    "transformer_model",
    "diffusion_model",
    "decision_support_system",
    "chatbot",
    "virtual_assistant",
    "content_moderation",
    "fraud_detection",
    "anomaly_detection",
    "sentiment_analysis",
    "image_generation",
    "speech_recognition",
    "machine_translation",
}

# NIST AI RMF risk categories
NIST_AI_RISK_CATEGORIES = {
    "HARMFUL_OUTPUTS": {
        "description": "AI system generates harmful, biased, or inappropriate outputs",
        "indicators": ["harmful_content", "toxic_language", "misinformation", "hate_speech"],
    },
    "HUMAN_AI_INTERACTION": {
        "description": "Risks from interaction between humans and AI systems",
        "indicators": ["automation_bias", "over_reliance", "skill_degradation", "lack_of_control"],
    },
    "CYBERSECURITY": {
        "description": "Security risks to AI systems and their data",
        "indicators": ["adversarial_attacks", "data_poisoning", "model_theft", "inference_attacks"],
    },
    "PRIVACY": {
        "description": "Risks to individual privacy from AI systems",
        "indicators": ["data_leakage", "membership_inference", "re_identification", "inference_attacks"],
    },
    "BIAS_FAIRNESS": {
        "description": "Unfair bias and discrimination in AI systems",
        "indicators": ["disparate_impact", "historical_bias", "measurement_bias", "aggregation_bias"],
    },
    "TRANSPARENCY_EXPLAINABILITY": {
        "description": "Lack of transparency and explainability in AI systems",
        "indicators": ["black_box", "lack_of_interpretability", "insufficient_documentation"],
    },
    "SAFETY": {
        "description": "Safety risks from AI system failures or malfunctions",
        "indicators": ["physical_harm", "safety_critical_failures", "unintended_consequences"],
    },
    "RELIABILITY_ROBUSTNESS": {
        "description": "AI system reliability and robustness issues",
        "indicators": ["model_drift", "distribution_shift", "edge_case_failures", "adversarial_vulnerability"],
    },
    "ACCOUNTABILITY_GOVERNANCE": {
        "description": "Governance and accountability gaps in AI systems",
        "indicators": ["lack_of_oversight", "unclear_ownership", "insufficient_testing", "poor_documentation"],
    },
    "SYSTEM_INTEGRITY": {
        "description": "System integrity and operational risks",
        "indicators": ["data_corruption", "model_degradation", "integration_failures", "scaling_issues"],
    },
}

# NIST AI RMF Trustworthy AI Characteristics (7 Core Characteristics)
TRUSTWORTHY_AI_CHARACTERISTICS = {
    "VALID_RELIABLE": {
        "description": "AI systems are valid and reliable",
        "subcharacteristics": ["accuracy", "precision", "recall", "f1_score", "auc_roc"],
        "evidence_fields": ["governance.testing_procedures", "governance.eval_metrics", "ai_profile.validated"],
    },
    "SAFE_SECURE": {
        "description": "AI systems are safe and secure",
        "subcharacteristics": ["robustness", "resilience", "security_controls", "adversarial_robustness"],
        "evidence_fields": ["governance.security_controls", "governance.robustness_testing"],
    },
    "RESILIENT_ROBUST": {
        "description": "AI systems are resilient and robust",
        "subcharacteristics": ["fault_tolerance", "graceful_degradation", "recovery_mechanisms"],
        "evidence_fields": ["governance.resilience_planning", "governance.disaster_recovery"],
    },
    "ACCOUNTABLE_TRANSPARENT": {
        "description": "AI systems are accountable and transparent",
        "subcharacteristics": ["auditability", "traceability", "documentation", "disclosure"],
        "evidence_fields": ["governance.roles_defined", "governance.transparency_reporting", "governance.audit_trail"],
    },
    "EXPLAINABLE_INTERPRETABLE": {
        "description": "AI systems are explainable and interpretable",
        "subcharacteristics": ["interpretability", "explainability", "feature_importance", "decision_rationale"],
        "evidence_fields": ["governance.explainability_framework", "ai_profile.explainability_score"],
    },
    "PRIVACY_ENHANCED": {
        "description": "AI systems are privacy-enhanced",
        "subcharacteristics": ["data_minimization", "purpose_limitation", "access_control", "encryption"],
        "evidence_fields": ["governance.privacy_protections", "governance.data_governance"],
    },
    "FAIR_BIAS_MANAGED": {
        "description": "AI systems are fair with harmful bias managed",
        "subcharacteristics": ["fairness_metrics", "bias_testing", "mitigation_strategies", "diverse_data"],
        "evidence_fields": ["governance.bias_testing", "governance.fairness_assessment"],
    },
}

# NIST AI RMF Core Functions and Subcategories
NIST_CORE_FUNCTIONS = {
    "GOVERN": {
        "description": "Cultivate a culture of AI risk management",
        "categories": ["leadership", "accountability", "policy", "oversight", "workforce"],
    },
    "MAP": {
        "description": "Understand and map AI risks and contexts",
        "categories": ["inventory", "context", "stakeholders", "requirements", "risk_assessment"],
    },
    "MEASURE": {
        "description": "Measure, assess, and analyze AI risks",
        "categories": ["testing", "evaluation", "metrics", "validation", "verification"],
    },
    "MANAGE": {
        "description": "Manage and mitigate AI risks",
        "categories": ["monitoring", "response", "remediation", "continuous_improvement"],
    },
}

# Industries where NIST AI RMF applies
NIST_AI_INDUSTRIES: Set[str] = {
    "AI_ML",
    "ARTIFICIAL_INTELLIGENCE",
    "MACHINE_LEARNING",
    "GENERATIVE_AI",
    "COMPUTER_VISION",
    "NATURAL_LANGUAGE_PROCESSING",
    "ROBOTICS",
    "AUTONOMOUS_VEHICLES",
    "HEALTHCARE_AI",
    "FINTECH_AI",
    "EDTECH_AI",
    "GOVERNMENT_AI",
    "DEFENSE_AI",
    "ENERGY_AI",
    "TRANSPORTATION_AI",
    "RETAIL_AI",
    "MANUFACTURING_AI",
    "AGRICULTURE_AI",
}

# AI system impact levels (aligned with NIST AI RMF)
AI_IMPACT_LEVELS = {
    "CRITICAL": {
        "description": "Potential for severe harm to human life, critical infrastructure, or national security",
        "examples": ["medical_diagnosis", "autonomous_weapons", "air_traffic_control", "power_grid_control"],
        "enforcement_scope_default": "TRANSACTION",
    },
    "HIGH": {
        "description": "Potential for significant harm to individuals or society",
        "examples": ["credit_scoring", "hiring_decisions", "criminal_risk_assessment", "mental_health_assessment"],
        "enforcement_scope_default": "TRANSACTION",
    },
    "MODERATE": {
        "description": "Potential for moderate harm or significant inconvenience",
        "examples": ["content_recommendation", "ad_targeting", "chatbots", "spam_filtering"],
        "enforcement_scope_default": "PLATFORM_AUDIT",
    },
    "LOW": {
        "description": "Minimal risk of harm",
        "examples": ["spell_check", "photo_filters", "basic_automation", "simple_classification"],
        "enforcement_scope_default": "POSTURE",
    },
}

# Actions where NIST AI RMF likely doesn't apply
NON_AI_ACTIONS: Set[str] = {
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
# AI SYSTEM DETECTION (FUTURE-PROOF)
# ============================================================

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
    
    # Method 1: Explicit AI flags
    if payload.get("is_ai_system") or payload.get("handles_ai"):
        detection_evidence["methods_used"].append("EXPLICIT_FLAG")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["indicators_found"].append("explicit_ai_flag")
        return True, detection_evidence
    
    # Method 2: AI profile detection
    ai_profile = payload.get("ai_profile", {})
    if ai_profile:
        detection_evidence["methods_used"].append("AI_PROFILE")
        detection_evidence["indicators_found"].append("ai_profile_exists")
        
        if ai_profile.get("system_type") or ai_profile.get("use_case"):
            detection_evidence["confidence"] = "HIGH"
            return True, detection_evidence
    
    # Method 3: Action classification
    action = str(payload.get("action", "")).lower().strip()
    if any(ai_term in action for ai_term in ["ai_", "_ai", "model_", "_model", "ml_", "_ml"]):
        detection_evidence["methods_used"].append("ACTION_PATTERN")
        detection_evidence["confidence"] = "MEDIUM"
        detection_evidence["indicators_found"].append(f"action:{action}")
        return True, detection_evidence
    
    # Method 4: Industry classification
    industry = str(payload.get("industry_id", "")).upper().strip()
    if industry in NIST_AI_INDUSTRIES:
        detection_evidence["methods_used"].append("INDUSTRY_CLASSIFICATION")
        detection_evidence["confidence"] = "MEDIUM"
        detection_evidence["indicators_found"].append(f"industry:{industry}")
        return True, detection_evidence
    
    # Method 5: System type detection
    system_type = str(payload.get("system_type", "")).lower()
    if any(ai_type in system_type for ai_type in NIST_AI_SYSTEM_TYPES):
        detection_evidence["methods_used"].append("SYSTEM_TYPE")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["indicators_found"].append(f"system_type:{system_type}")
        return True, detection_evidence
    
    # Method 6: Governance indicators
    governance = payload.get("governance", {})
    if governance and governance.get("ai_risk_framework") == "NIST_AI_RMF":
        detection_evidence["methods_used"].append("GOVERNANCE_FRAMEWORK")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["indicators_found"].append("nist_ai_rmf_framework")
        return True, detection_evidence
    
    return False, detection_evidence


def _classify_ai_impact(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Classify AI system impact level according to NIST AI RMF.
    
    Returns:
        (impact_level, classification_evidence)
        impact_level: "CRITICAL", "HIGH", "MODERATE", "LOW", "UNKNOWN"
    """
    classification_evidence = {
        "factors_considered": [],
        "impact_level": "UNKNOWN",
        "confidence": "LOW",
    }
    
    ai_profile = payload.get("ai_profile", {})
    
    # Factor 1: Explicit impact classification
    impact = str(ai_profile.get("impact_level", "")).upper()
    if impact in AI_IMPACT_LEVELS:
        classification_evidence["factors_considered"].append("EXPLICIT_IMPACT")
        classification_evidence["impact_level"] = impact
        classification_evidence["confidence"] = "HIGH"
        return impact, classification_evidence
    
    # Factor 2: Use case classification
    use_case = str(ai_profile.get("use_case", "")).lower()
    classification_evidence["factors_considered"].append(f"USE_CASE:{use_case}")
    
    for impact_level, details in AI_IMPACT_LEVELS.items():
        for example in details["examples"]:
            if example in use_case:
                classification_evidence["impact_level"] = impact_level
                classification_evidence["confidence"] = "MEDIUM"
                return impact_level, classification_evidence
    
    # Factor 3: Risk indicators
    risk_indicators = payload.get("risk_indicators", {})
    if risk_indicators.get("critical_risk") or risk_indicators.get("safety_critical"):
        classification_evidence["factors_considered"].append("CRITICAL_RISK_INDICATORS")
        classification_evidence["impact_level"] = "CRITICAL"
        classification_evidence["confidence"] = "MEDIUM"
        return "CRITICAL", classification_evidence
    
    # Factor 4: Industry context
    industry = str(payload.get("industry_id", "")).upper()
    classification_evidence["factors_considered"].append(f"INDUSTRY:{industry}")
    
    if industry in {"HEALTHCARE_AI", "DEFENSE_AI", "ENERGY_AI", "TRANSPORTATION_AI"}:
        classification_evidence["impact_level"] = "CRITICAL"
        classification_evidence["confidence"] = "LOW"
        return "CRITICAL", classification_evidence
    
    # Default: MODERATE (most common for deployed AI)
    classification_evidence["impact_level"] = "MODERATE"
    classification_evidence["confidence"] = "LOW"
    return "MODERATE", classification_evidence


def _assess_trustworthy_ai_characteristics(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Assess Trustworthy AI characteristics.
    
    Returns:
        (characteristic_scores, assessment_evidence)
    """
    assessment_evidence = {
        "characteristics_assessed": [],
        "methods_used": [],
        "confidence": "LOW",
    }
    
    ai_profile = payload.get("ai_profile", {})
    governance = payload.get("governance", {})
    risk_indicators = payload.get("risk_indicators", {})
    
    characteristic_scores = {}
    
    for char_id, char_info in TRUSTWORTHY_AI_CHARACTERISTICS.items():
        score = 0
        max_score = len(char_info["evidence_fields"])
        
        for evidence_field in char_info["evidence_fields"]:
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
        characteristic_scores[char_id] = normalized_score
        
        assessment_evidence["characteristics_assessed"].append({
            "characteristic": char_id,
            "score": normalized_score,
            "evidence_fields": char_info["evidence_fields"],
        })
    
    assessment_evidence["methods_used"].append("EVIDENCE_BASED_SCORING")
    assessment_evidence["confidence"] = "MEDIUM"
    
    return characteristic_scores, assessment_evidence


def _should_evaluate_nist_ai_rmf(payload: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Future-proof decision: Should NIST AI RMF evaluation run for this payload?
    
    Returns:
        (should_evaluate, evaluation_reason, context_evidence)
    """
    context_evidence = {
        "ai_system_detection": {},
        "impact_classification": {},
        "trustworthy_ai_assessment": {},
        "context_checks": {},
    }
    
    # Check 1: AI system detection
    is_ai_system, ai_evidence = _detect_ai_system(payload)
    context_evidence["ai_system_detection"] = ai_evidence
    
    if not is_ai_system:
        return False, "NOT_AI_SYSTEM", context_evidence
    
    # Check 2: Action relevance
    action = str(payload.get("action", "")).lower().strip()
    context_evidence["context_checks"]["action"] = action
    
    if action in NON_AI_ACTIONS:
        return False, f"ACTION_EXCLUDED: {action}", context_evidence
    
    # Check 3: Impact classification
    impact_level, impact_evidence = _classify_ai_impact(payload)
    context_evidence["impact_classification"] = impact_evidence
    
    # Check 4: Trustworthy AI assessment
    trustworthy_scores, trustworthy_evidence = _assess_trustworthy_ai_characteristics(payload)
    context_evidence["trustworthy_ai_assessment"] = trustworthy_evidence
    
    # All checks passed - evaluate NIST AI RMF
    return True, f"EVALUATE_NIST_AI_RMF_IMPACT:{impact_level}", context_evidence


# ============================================================
# ENFORCEMENT SCOPE RESOLUTION (FUTURE-PROOF)
# ============================================================

def _normalize_nist_ai_rmf_article(article: str) -> str:
    """
    Normalize NIST AI RMF article identifier for consistent comparison.
    
    Future-proof examples:
        "NIST AI RMF: GOVERN" → "GOVERN"
        "Core GOVERN" → "GOVERN"
        "GOVERN 1.1" → "GOVERN_1.1"
        "MAP Context" → "MAP_CONTEXT"
        "MEASURE Testing" → "MEASURE_TESTING"
    """
    if not article:
        return ""
    
    article = article.strip()
    
    # Remove common prefixes
    article = re.sub(r"(?i)^(nist\s*ai\s*rmf\s*:?\s*)", "", article)
    article = re.sub(r"(?i)^(core\s*)", "", article)
    
    # Extract function and subcategory
    if " " in article:
        parts = article.split(" ", 1)
        function = parts[0].upper()
        subcategory = parts[1].replace(" ", "_").upper()
        return f"{function}_{subcategory}"
    
    # Return as uppercase
    return article.upper()


def _get_nist_ai_rmf_base_enforcement_scope(article: str) -> str:
    """
    Get base enforcement scope from governance catalog.
    
    Future-proof NIST AI RMF Classification:
    - GOVERN: GOVERNANCE (organizational leadership and culture)
    - MAP: PLATFORM_AUDIT (context mapping and risk assessment)
    - MEASURE: TECHNICAL (testing, evaluation, metrics)
    - MANAGE: TRANSACTION (monitoring, response, remediation)
    
    Returns: "TRANSACTION" | "PLATFORM_AUDIT" | "GOVERNANCE" | "TECHNICAL" | "POSTURE" | "ADMINISTRATIVE"
    Default: "PLATFORM_AUDIT" (safe - logs but doesn't block unknown articles)
    """
    article_normalized = _normalize_nist_ai_rmf_article(article)
    
    # First check catalog for NIST AI RMF regime
    for regime in _GOVERNANCE_CATALOG.get("regimes", []):
        if regime.get("id") == NIST_AI_RMF_REGIME_ID:
            for domain in regime.get("domains", []):
                for art_def in domain.get("articles", []):
                    if art_def.get("article", "") == article_normalized:
                        return art_def.get("enforcement_scope", "PLATFORM_AUDIT")
    
    # Local mapping based on core functions
    nist_ai_rmf_scopes = {
        # Core Functions
        "GOVERN": "GOVERNANCE",
        "GOVERN_LEADERSHIP": "GOVERNANCE",
        "GOVERN_ACCOUNTABILITY": "GOVERNANCE",
        "GOVERN_POLICY": "GOVERNANCE",
        
        "MAP": "PLATFORM_AUDIT",
        "MAP_CONTEXT": "PLATFORM_AUDIT",
        "MAP_INVENTORY": "PLATFORM_AUDIT",
        "MAP_RISK_ASSESSMENT": "PLATFORM_AUDIT",
        
        "MEASURE": "TECHNICAL",
        "MEASURE_TESTING": "TECHNICAL",
        "MEASURE_EVALUATION": "TECHNICAL",
        "MEASURE_METRICS": "TECHNICAL",
        
        "MANAGE": "TRANSACTION",
        "MANAGE_MONITORING": "TRANSACTION",
        "MANAGE_RESPONSE": "TRANSACTION",
        "MANAGE_REMEDIATION": "TRANSACTION",
        
        # Trustworthy AI Characteristics
        "VALID_RELIABLE": "TECHNICAL",
        "SAFE_SECURE": "TRANSACTION",
        "RESILIENT_ROBUST": "TECHNICAL",
        "ACCOUNTABLE_TRANSPARENT": "GOVERNANCE",
        "EXPLAINABLE_INTERPRETABLE": "TECHNICAL",
        "PRIVACY_ENHANCED": "TRANSACTION",
        "FAIR_BIAS_MANAGED": "GOVERNANCE",
    }
    
    return nist_ai_rmf_scopes.get(article_normalized, "PLATFORM_AUDIT")


def _resolve_nist_ai_rmf_enforcement_scope(article: str, payload: Dict[str, Any]) -> str:
    """
    Resolve final enforcement scope with future-proof modifiers.
    
    NIST AI RMF enforcement scope modifiers:
    1. AI system impact level escalation
    2. Trustworthy AI characteristic gaps
    3. Regulatory compliance requirements
    4. Active incidents or high-risk indicators
    
    Returns:
        Final enforcement scope after applying modifiers
    """
    base_scope = _get_nist_ai_rmf_base_enforcement_scope(article)
    article_normalized = _normalize_nist_ai_rmf_article(article)
    
    # Get context information
    impact_level, _ = _classify_ai_impact(payload)
    trustworthy_scores, _ = _assess_trustworthy_ai_characteristics(payload)
    risk_indicators = payload.get("risk_indicators", {})
    ai_profile = payload.get("ai_profile", {})
    
    # MODIFIER 1: High-impact AI system escalation
    if impact_level in {"CRITICAL", "HIGH"}:
        if base_scope in {"PLATFORM_AUDIT", "GOVERNANCE", "POSTURE"}:
            # High-impact systems need stricter enforcement
            if article_normalized.startswith("MANAGE") or article_normalized.startswith("MEASURE"):
                return "TRANSACTION"
    
    # MODIFIER 2: Trustworthy AI characteristic gaps
    low_trustworthy_scores = [char for char, score in trustworthy_scores.items() if score < 50]
    if len(low_trustworthy_scores) >= 2:
        if base_scope in {"PLATFORM_AUDIT", "GOVERNANCE"}:
            # Multiple trustworthy AI gaps require immediate attention
            return "TRANSACTION"
    
    # MODIFIER 3: Active incidents or high-risk indicators
    if risk_indicators.get("ai_incident_active") or risk_indicators.get("harmful_content_flag"):
        if article_normalized.startswith("MANAGE"):
            return "TRANSACTION"
    
    # MODIFIER 4: Safety-critical or autonomous systems
    if ai_profile.get("safety_critical") or ai_profile.get("autonomous_decision_making"):
        if base_scope in {"PLATFORM_AUDIT", "GOVERNANCE"}:
            return "TRANSACTION"
    
    # MODIFIER 5: Regulatory context
    regulatory_context = str(payload.get("meta", {}).get("regulatory_context", "")).upper()
    if "EU_AI_ACT" in regulatory_context and impact_level in {"HIGH", "CRITICAL"}:
        # High-risk AI under EU AI Act needs strict enforcement
        return "TRANSACTION"
    
    # No modifiers applied
    return base_scope


# ============================================================
# EVIDENCE COLLECTION (Enhanced for Future-Proofing)
# ============================================================

def _collect_nist_ai_rmf_evidence(payload: Dict[str, Any], rule_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect comprehensive NIST AI RMF evidence for audit trails.
    
    Returns:
        Structured evidence with context, rule data, and metadata
    """
    evidence = {
        # Context evidence
        "context": {
            "industry_id": payload.get("industry_id"),
            "action": payload.get("action"),
            "regulatory_context": (payload.get("meta") or {}).get("regulatory_context"),
            "ai_system_detected": True,
        },
        # Rule-specific evidence
        "rule_data": rule_data,
        # NIST AI RMF-specific information
        "nist_ai_rmf_info": {},
        # Metadata
        "metadata": {
            "evidence_collected_at": "NOW",  # Would be timestamp in real implementation
            "framework_version": "NIST AI RMF 1.0",
        }
    }
    
    # Collect NIST AI RMF-specific information
    ai_profile = payload.get("ai_profile", {})
    governance = payload.get("governance", {})
    trustworthy_scores, _ = _assess_trustworthy_ai_characteristics(payload)
    
    evidence["nist_ai_rmf_info"] = {
        "impact_level": ai_profile.get("impact_level"),
        "trustworthy_ai_scores": trustworthy_scores,
        "governance_framework": governance.get("ai_risk_framework"),
        "risk_assessment_date": governance.get("risk_assessment_date"),
        "last_monitoring_date": governance.get("last_monitoring_date"),
    }
    
    return evidence


# ============================================================
# NIST AI RMF RULE DEFINITIONS (Enhanced with All Core Functions)
# ============================================================

# NIST AI RMF rules with comprehensive metadata
NIST_AI_RMF_RULES = [
    # ============================================================
    # GOVERN: Cultivate a culture of AI risk management
    # ============================================================
    {
        "article": "NIST AI RMF: GOVERN",
        "title": "AI Governance and Leadership",
        "description": "Establish organizational culture, leadership, and accountability for AI risk management.",
        "field": "ai_governance_established",
        "severity": "HIGH",
        "rule_id": "NIST_AI_RMF_GOVERN_LEADERSHIP",
        "enforcement_scope_default": "GOVERNANCE",
        "future_proof_notes": "Must include top management commitment, AI policy, roles and responsibilities.",
        "evidence_fields": ["governance.roles_defined", "governance.owner", "governance.raci", "governance.ai_policy"],
        "trustworthy_characteristic": "ACCOUNTABLE_TRANSPARENT",
        "compliance_level": "REQUIRED",
    },
    {
        "article": "NIST AI RMF: GOVERN Accountability",
        "title": "AI Accountability Framework",
        "description": "Define clear accountability for AI system development, deployment, and operation.",
        "field": "accountability_framework",
        "severity": "HIGH",
        "rule_id": "NIST_AI_RMF_GOVERN_ACCOUNTABILITY",
        "enforcement_scope_default": "GOVERNANCE",
        "future_proof_notes": "Includes AI system owner, risk owner, compliance officer roles with clear responsibilities.",
        "evidence_fields": ["governance.accountability_framework", "governance.owner", "governance.risk_owner"],
        "trustworthy_characteristic": "ACCOUNTABLE_TRANSPARENT",
        "compliance_level": "REQUIRED",
    },
    {
        "article": "NIST AI RMF: GOVERN Policy",
        "title": "AI Risk Management Policy",
        "description": "Develop and implement AI risk management policy aligned with organizational objectives.",
        "field": "ai_policy",
        "severity": "HIGH",
        "rule_id": "NIST_AI_RMF_GOVERN_POLICY",
        "enforcement_scope_default": "GOVERNANCE",
        "future_proof_notes": "Policy must address all trustworthy AI characteristics and risk categories.",
        "evidence_fields": ["governance.ai_policy", "governance.policy_url", "governance.policy_version"],
        "trustworthy_characteristic": "ACCOUNTABLE_TRANSPARENT",
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # MAP: Understand and map AI risks and contexts
    # ============================================================
    {
        "article": "NIST AI RMF: MAP",
        "title": "AI System Context and Inventory",
        "description": "Map AI system context, stakeholders, and maintain comprehensive inventory.",
        "field": "ai_system_inventory",
        "severity": "MEDIUM",
        "rule_id": "NIST_AI_RMF_MAP_INVENTORY",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Includes system boundaries, dependencies, data sources, and stakeholder analysis.",
        "evidence_fields": ["governance.model_inventory", "ai_profile.system_id", "ai_profile.model_id", "governance.stakeholder_analysis"],
        "trustworthy_characteristic": "ACCOUNTABLE_TRANSPARENT",
        "compliance_level": "REQUIRED",
    },
    {
        "article": "NIST AI RMF: MAP Risk Assessment",
        "title": "AI Risk Assessment and Categorization",
        "description": "Conduct comprehensive AI risk assessment across all risk categories.",
        "field": "risk_assessment",
        "severity": "HIGH",
        "rule_id": "NIST_AI_RMF_MAP_RISK_ASSESSMENT",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Must address all NIST AI RMF risk categories: harmful outputs, bias, privacy, security, etc.",
        "evidence_fields": ["governance.risk_assessment", "governance.risk_register", "ai_profile.risk_categories"],
        "trustworthy_characteristic": "VALID_RELIABLE",
        "compliance_level": "REQUIRED",
    },
    {
        "article": "NIST AI RMF: MAP Requirements",
        "title": "AI System Requirements and Constraints",
        "description": "Define functional, non-functional, and regulatory requirements for AI systems.",
        "field": "requirements_defined",
        "severity": "MEDIUM",
        "rule_id": "NIST_AI_RMF_MAP_REQUIREMENTS",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Includes accuracy thresholds, latency requirements, fairness constraints, regulatory compliance.",
        "evidence_fields": ["governance.requirements_defined", "governance.performance_requirements", "governance.fairness_requirements"],
        "trustworthy_characteristic": "VALID_RELIABLE",
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # MEASURE: Measure, assess, and analyze AI risks
    # ============================================================
    {
        "article": "NIST AI RMF: MEASURE",
        "title": "AI System Testing and Evaluation",
        "description": "Implement comprehensive testing and evaluation framework for AI systems.",
        "field": "testing_procedures",
        "severity": "HIGH",
        "rule_id": "NIST_AI_RMF_MEASURE_TESTING",
        "enforcement_scope_default": "TECHNICAL",
        "future_proof_notes": "Includes unit testing, integration testing, adversarial testing, and edge case evaluation.",
        "evidence_fields": ["governance.testing_procedures", "governance.test_results", "ai_profile.validated"],
        "trustworthy_characteristic": "VALID_RELIABLE",
        "compliance_level": "REQUIRED",
    },
    {
        "article": "NIST AI RMF: MEASURE Metrics",
        "title": "AI Performance and Risk Metrics",
        "description": "Define and monitor metrics for AI system performance and risk management.",
        "field": "eval_metrics",
        "severity": "MEDIUM",
        "rule_id": "NIST_AI_RMF_MEASURE_METRICS",
        "enforcement_scope_default": "TECHNICAL",
        "future_proof_notes": "Includes accuracy, fairness, robustness, explainability, and privacy metrics.",
        "evidence_fields": ["governance.eval_metrics", "governance.metrics_dashboard", "governance.metric_thresholds"],
        "trustworthy_characteristic": "VALID_RELIABLE",
        "compliance_level": "REQUIRED",
    },
    {
        "article": "NIST AI RMF: MEASURE Bias Assessment",
        "title": "Bias and Fairness Assessment",
        "description": "Conduct bias and fairness assessment across protected attributes and demographic groups.",
        "field": "bias_testing",
        "severity": "HIGH",
        "rule_id": "NIST_AI_RMF_MEASURE_BIAS",
        "enforcement_scope_default": "TECHNICAL",
        "future_proof_notes": "Must test for disparate impact, historical bias, measurement bias across all protected classes.",
        "evidence_fields": ["governance.bias_testing", "governance.fairness_assessment", "governance.bias_mitigation"],
        "trustworthy_characteristic": "FAIR_BIAS_MANAGED",
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # MANAGE: Manage and mitigate AI risks
    # ============================================================
    {
        "article": "NIST AI RMF: MANAGE",
        "title": "AI System Monitoring and Oversight",
        "description": "Implement continuous monitoring and oversight for AI system operation.",
        "field": "monitoring",
        "severity": "HIGH",
        "rule_id": "NIST_AI_RMF_MANAGE_MONITORING",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Includes performance monitoring, drift detection, anomaly detection, and compliance monitoring.",
        "evidence_fields": ["governance.monitoring", "governance.drift_monitoring", "governance.anomaly_detection"],
        "trustworthy_characteristic": "SAFE_SECURE",
        "compliance_level": "REQUIRED",
    },
    {
        "article": "NIST AI RMF: MANAGE Incident Response",
        "title": "AI Incident Response and Remediation",
        "description": "Establish incident response procedures for AI system failures and risks.",
        "field": "incident_response",
        "severity": "HIGH",
        "rule_id": "NIST_AI_RMF_MANAGE_INCIDENT",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Includes detection, analysis, containment, eradication, recovery, and lessons learned.",
        "evidence_fields": ["governance.incident_response", "governance.incident_playbook", "governance.incident_contact"],
        "trustworthy_characteristic": "RESILIENT_ROBUST",
        "compliance_level": "REQUIRED",
    },
    {
        "article": "NIST AI RMF: MANAGE Human Oversight",
        "title": "Human Oversight and Control",
        "description": "Implement human oversight mechanisms for AI system decisions and outputs.",
        "field": "human_oversight",
        "severity": "MEDIUM",
        "rule_id": "NIST_AI_RMF_MANAGE_HUMAN",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Includes human-in-the-loop, human-on-the-loop, human-over-the-loop mechanisms.",
        "evidence_fields": ["governance.human_oversight", "governance.human_in_the_loop", "governance.escalation_procedures"],
        "trustworthy_characteristic": "ACCOUNTABLE_TRANSPARENT",
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # TRUSTWORTHY AI CHARACTERISTICS (Additional Controls)
    # ============================================================
    {
        "article": "NIST AI RMF: VALID_RELIABLE",
        "title": "Valid and Reliable AI Systems",
        "description": "Ensure AI systems are valid and reliable for their intended use.",
        "field": "validated",
        "severity": "HIGH",
        "rule_id": "NIST_AI_RMF_VALID_RELIABLE",
        "enforcement_scope_default": "TECHNICAL",
        "future_proof_notes": "Requires rigorous validation, testing, and quality assurance processes.",
        "evidence_fields": ["ai_profile.validated", "governance.validation_process", "governance.quality_assurance"],
        "trustworthy_characteristic": "VALID_RELIABLE",
        "compliance_level": "REQUIRED",
    },
    {
        "article": "NIST AI RMF: SAFE_SECURE",
        "title": "Safe and Secure AI Systems",
        "description": "Implement safety and security controls for AI systems.",
        "field": "security_controls",
        "severity": "HIGH",
        "rule_id": "NIST_AI_RMF_SAFE_SECURE",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Includes adversarial robustness, data protection, access controls, and secure deployment.",
        "evidence_fields": ["governance.security_controls", "governance.adversarial_testing", "governance.access_controls"],
        "trustworthy_characteristic": "SAFE_SECURE",
        "compliance_level": "REQUIRED",
    },
    {
        "article": "NIST AI RMF: EXPLAINABLE_INTERPRETABLE",
        "title": "Explainable and Interpretable AI Systems",
        "description": "Ensure AI system decisions are explainable and interpretable.",
        "field": "explainability_framework",
        "severity": "MEDIUM",
        "rule_id": "NIST_AI_RMF_EXPLAINABLE",
        "enforcement_scope_default": "TECHNICAL",
        "future_proof_notes": "Includes feature importance, decision rationale, counterfactual explanations, and uncertainty quantification.",
        "evidence_fields": ["governance.explainability_framework", "ai_profile.explainability_score", "governance.interpretability_tools"],
        "trustworthy_characteristic": "EXPLAINABLE_INTERPRETABLE",
        "compliance_level": "ADDRESSABLE",
    },
    {
        "article": "NIST AI RMF: PRIVACY_ENHANCED",
        "title": "Privacy-Enhanced AI Systems",
        "description": "Implement privacy protections throughout AI system lifecycle.",
        "field": "privacy_protections",
        "severity": "HIGH",
        "rule_id": "NIST_AI_RMF_PRIVACY_ENHANCED",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Includes data minimization, differential privacy, federated learning, and privacy impact assessments.",
        "evidence_fields": ["governance.privacy_protections", "governance.data_minimization", "governance.privacy_impact_assessment"],
        "trustworthy_characteristic": "PRIVACY_ENHANCED",
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # FUTURE CONTROLS (NIST AI RMF 2.0+ readiness)
    # ============================================================
    {
        "article": "NIST AI RMF: AI SUPPLY CHAIN",
        "title": "AI Supply Chain Risk Management",
        "description": "Manage risks from AI system components, data, and third-party services.",
        "field": "supply_chain_risk",
        "severity": "MEDIUM",
        "rule_id": "NIST_AI_RMF_SUPPLY_CHAIN",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Includes vendor assessment, component verification, dependency analysis, and continuity planning.",
        "evidence_fields": ["governance.supply_chain_risk", "governance.vendor_assessment", "governance.component_verification"],
        "trustworthy_characteristic": "SAFE_SECURE",
        "compliance_level": "ADDRESSABLE",
        "future_implementation": True,
    },
    {
        "article": "NIST AI RMF: AI ASSURANCE",
        "title": "AI System Assurance and Certification",
        "description": "Implement assurance processes and consider third-party certification.",
        "field": "ai_assurance",
        "severity": "MEDIUM",
        "rule_id": "NIST_AI_RMF_ASSURANCE",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Includes internal assurance processes, external audits, and compliance with certification schemes.",
        "evidence_fields": ["governance.ai_assurance", "governance.assurance_framework", "governance.certification_status"],
        "trustworthy_characteristic": "ACCOUNTABLE_TRANSPARENT",
        "compliance_level": "ADDRESSABLE",
        "future_implementation": True,
    },
]


# ============================================================
# MAIN EVALUATION FUNCTION (Future-Proof Architecture)
# ============================================================

def evaluate_nist_ai_rmf_rules(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Future-proof NIST AI RMF evaluation with comprehensive context gating.
    
    Features:
    1. Multi-method AI system detection
    2. AI system impact classification
    3. Trustworthy AI characteristic assessment
    4. Core function evaluation (GOVERN, MAP, MEASURE, MANAGE)
    5. Enhanced enforcement scope resolution
    6. Comprehensive evidence collection
    7. Detailed context tracking
    8. Future control support
    
    Returns:
        (policies, summary)
        - policies: List with enforcement_scope, evidence, and context
        - summary: Aggregate statistics with detailed context info
    """
    policies: List[Dict[str, Any]] = []
    
    # ============================================================
    # FUTURE-PROOF: CONTEXT GATING DECISION
    # ============================================================
    should_evaluate, evaluation_reason, context_evidence = _should_evaluate_nist_ai_rmf(payload)
    
    if not should_evaluate:
        # NIST AI RMF doesn't apply - return with NOT_APPLICABLE
        policies.append({
            "domain": NIST_AI_RMF_DOMAIN,
            "regime": "NIST_AI_RMF",
            "framework": NIST_AI_RMF_FRAMEWORK,
            "domain_id": "NIST_AI_RMF",
            "article": "NIST AI RMF:APPLICABILITY",
            "category": "Applicability",
            "title": "Applicability",
            "status": "NOT_APPLICABLE",
            "severity": "LOW",
            "impact_on_verdict": "COMPLIANT",
            "trigger_type": "NOT_APPLICABLE",
            "rule_ids": ["NIST_AI_RMF_APPLICABILITY_NA"],
            "enforcement_scope": "SUPERVISORY",
            "notes": f"NIST AI RMF evaluation skipped: {evaluation_reason}",
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
            "regime": "NIST_AI_RMF",
            "context_gated": True,
            "evaluation_decision": evaluation_reason,
            "context_evidence": context_evidence,
            "notes": f"NIST AI RMF evaluation skipped: {evaluation_reason}"
        }
        return policies, summary
    
    # ============================================================
    # CONTEXT INFORMATION COLLECTION
    # ============================================================
    impact_level, impact_evidence = _classify_ai_impact(payload)
    trustworthy_scores, trustworthy_evidence = _assess_trustworthy_ai_characteristics(payload)
    ai_profile = payload.get("ai_profile", {}) or {}
    governance = payload.get("governance", {}) or {}
    risk_indicators = payload.get("risk_indicators", {}) or {}
    
    # ============================================================
    # RULE EVALUATION (Enhanced with Evidence Collection)
    # ============================================================
    
    evaluation_errors = []
    
    for rule_def in NIST_AI_RMF_RULES:
        # Skip future implementation rules if not ready
        if rule_def.get("future_implementation") and not governance.get("enable_future_controls"):
            continue
        
        try:
            # Check if the required field exists and is compliant
            field_value = governance.get(rule_def["field"]) or ai_profile.get(rule_def["field"])
            
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
            enforcement_scope = _resolve_nist_ai_rmf_enforcement_scope(rule_def["article"], payload)
            
            # Determine impact on verdict
            if status == "VIOLATED" and rule_def["severity"] in {"HIGH", "CRITICAL"}:
                impact_on_verdict = "BLOCKING_FAILURE"
            elif status == "VIOLATED":
                impact_on_verdict = "NON_BLOCKING"
            else:
                impact_on_verdict = "COMPLIANT"
            
            # Determine severity based on context
            severity = rule_def["severity"]
            if status == "VIOLATED" and impact_level in {"CRITICAL", "HIGH"}:
                # Escalate severity for high-impact systems
                if severity == "MEDIUM":
                    severity = "HIGH"
                elif severity == "HIGH":
                    severity = "CRITICAL"
            
            # Check trustworthy AI characteristic score if applicable
            trustworthy_char = rule_def.get("trustworthy_characteristic")
            if trustworthy_char and trustworthy_scores.get(trustworthy_char, 0) < 50:
                # Low trustworthy AI score can escalate severity
                if severity == "MEDIUM":
                    severity = "HIGH"
            
            # Create policy
            policy = {
                "domain": NIST_AI_RMF_DOMAIN,
                "regime": "NIST_AI_RMF",
                "framework": NIST_AI_RMF_FRAMEWORK,
                "domain_id": "NIST_AI_RMF",
                "article": rule_def["article"],
                "category": rule_def["title"],
                "title": rule_def["title"],
                "status": status,
                "severity": severity if status == "VIOLATED" else "LOW",
                "enforcement_scope": enforcement_scope,
                "impact_on_verdict": impact_on_verdict,
                "trigger_type": "NIST_AI_RMF_CONTROL",
                "rule_ids": [rule_def["rule_id"]],
                "notes": rule_def["description"],
                "evidence": _collect_nist_ai_rmf_evidence(payload, rule_evidence),
                "remediation": (
                    f"Implement {rule_def['title']} controls per NIST AI RMF requirements. "
                    "Document procedures and re-run GNCE after remediation."
                    if status == "VIOLATED" else "No remediation required."
                ),
                "violation_detail": rule_def["description"] if status == "VIOLATED" else "",
                "control_severity": rule_def["severity"],
                # Future-proof metadata
                "metadata": {
                    "trustworthy_characteristic": trustworthy_char,
                    "trustworthy_score": trustworthy_scores.get(trustworthy_char) if trustworthy_char else None,
                    "compliance_level": rule_def.get("compliance_level", "REQUIRED"),
                    "impact_level": impact_level,
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
        "impact_level": impact_level,
        "ai_system_detected": True,
    }
    
    # Count by core function
    function_counts = {}
    for function in ["GOVERN", "MAP", "MEASURE", "MANAGE"]:
        function_counts[f"{function.lower()}_violations"] = sum(
            1 for p in policies 
            if p["status"] == "VIOLATED" and function in p["article"]
        )
    
    # Trustworthy AI characteristic scores
    trustworthy_summary = {}
    for char_id, score in trustworthy_scores.items():
        trustworthy_summary[f"{char_id.lower()}_score"] = score
    
    # Count by Trustworthy AI characteristic
    trustworthy_violations = {}
    for char_id in TRUSTWORTHY_AI_CHARACTERISTICS.keys():
        trustworthy_violations[f"{char_id.lower()}_violations"] = sum(
            1 for p in policies 
            if p["status"] == "VIOLATED" and 
            p.get("metadata", {}).get("trustworthy_characteristic") == char_id
        )
    
    summary = {
        "total_rules": len(policies),
        "passed": passed,
        "failed": failed,
        "blocking_failures": blocking,
        "regime": "NIST_AI_RMF",
        "context_gated": False,
        "evaluation_decision": evaluation_reason,
        # Context information
        "context": context_info,
        "context_evidence": context_evidence,
        # AI system characteristics
        "impact_level": impact_level,
        "impact_classification": impact_evidence,
        # Trustworthy AI assessment
        "trustworthy_scores": trustworthy_scores,
        "trustworthy_assessment": trustworthy_evidence,
        # Violation breakdown
        **function_counts,
        **trustworthy_violations,
        # Core function coverage
        "governance_controls": sum(1 for p in policies if "GOVERN" in p["article"]),
        "mapping_controls": sum(1 for p in policies if "MAP" in p["article"]),
        "measurement_controls": sum(1 for p in policies if "MEASURE" in p["article"]),
        "management_controls": sum(1 for p in policies if "MANAGE" in p["article"]),
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
        "technical_violations": sum(1 for p in policies 
                                  if p["status"] == "VIOLATED" and p.get("enforcement_scope") == "TECHNICAL"),
        "transaction_violations": sum(1 for p in policies 
                                    if p["status"] == "VIOLATED" and p.get("enforcement_scope") == "TRANSACTION"),
        # Rule statistics
        "core_rules_evaluated": len([r for r in NIST_AI_RMF_RULES if not r.get("future_implementation")]),
        "future_rules_available": len([r for r in NIST_AI_RMF_RULES if r.get("future_implementation")]),
        "future_rules_evaluated": len([r for r in NIST_AI_RMF_RULES if r.get("future_implementation") 
                                      and governance.get("enable_future_controls")]),
        # Error tracking
        "evaluation_errors": evaluation_errors if evaluation_errors else None,
    }
    
    return policies, summary