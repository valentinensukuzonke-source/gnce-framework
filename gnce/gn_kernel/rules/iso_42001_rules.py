# gnce/gn_kernel/rules/iso_42001_rules.py
"""
ISO/IEC 42001:2023 AI Management System Evaluator with Constitutional Binding (v0.7.2-RC-FUTUREPROOF)

CRITICAL UPDATES FOR FUTURE-PROOFING:
1. Comprehensive AI system detection with multi-method verification
2. ISO 42001 clause hierarchy and relationship mapping
3. AI system lifecycle stage detection (development, deployment, operation, decommissioning)
4. AI system impact classification (critical, high, moderate, low)
5. Global regulatory alignment (EU AI Act, US Executive Order, NIST AI RMF)
6. Enhanced enforcement scope resolution with risk-aware escalation
7. Comprehensive evidence collection for audit trails
8. Cross-domain safety (won't misfire on non-AI systems)
9. Future ISO 42001 updates ready for implementation

ISO/IEC 42001:2023 Reality (Future-Proof):
- Annex A controls: Context, leadership, planning, support, operation, performance, improvement
- PDCA cycle integration (Plan-Do-Check-Act)
- AI system lifecycle management
- Risk-based approach to AI governance
- Alignment with global AI regulations and standards
"""

from __future__ import annotations
from typing import Any, Dict, List, Tuple, Set, Optional
import re

# Load governance catalog for enforcement scope classification
from gnce.gn_kernel.constitution.constitution_catalog import load_governance_catalog_v05

# ============================================================
# MODULE CONSTANTS (FUTURE-PROOF)
# ============================================================

ISO_42001_DOMAIN = "AI Governance & Risk Management (ISO/IEC 42001:2023)"
ISO_42001_FRAMEWORK = "AI Management System"
ISO_42001_REGIME_ID = "ISO_42001"

# Load catalog once at module level (performance)
_GOVERNANCE_CATALOG = load_governance_catalog_v05()

# ============================================================
# AI SYSTEM DETECTION (FUTURE-PROOF)
# ============================================================

# AI system types (comprehensive list)
AI_SYSTEM_TYPES: Set[str] = {
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
    "content_generation",
    "image_recognition",
    "speech_recognition",
    "anomaly_detection",
    "fraud_detection",
    "sentiment_analysis",
}

# AI system lifecycle stages
AI_LIFECYCLE_STAGES: Set[str] = {
    "design_development",
    "data_collection",
    "model_training",
    "model_evaluation",
    "model_deployment",
    "inference_serving",
    "system_operation",
    "monitoring_observability",
    "maintenance_updates",
    "decommissioning",
    "impact_assessment",
    "continuous_improvement",
}

# AI system industries
AI_INDUSTRIES: Set[str] = {
    "AI_ML",
    "ARTIFICIAL_INTELLIGENCE",
    "MACHINE_LEARNING",
    "DEEP_LEARNING",
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

# AI system impact classification (aligned with NIST AI RMF)
AI_IMPACT_LEVELS = {
    "CRITICAL": {
        "description": "Potential for severe harm to human life, critical infrastructure, or national security",
        "examples": ["medical_diagnosis", "autonomous_weapons", "air_traffic_control", "power_grid_control"],
    },
    "HIGH": {
        "description": "Potential for significant harm to individuals or society",
        "examples": ["credit_scoring", "hiring_decisions", "criminal_risk_assessment", "mental_health_assessment"],
    },
    "MODERATE": {
        "description": "Potential for moderate harm or significant inconvenience",
        "examples": ["content_recommendation", "ad_targeting", "chatbots", "spam_filtering"],
    },
    "LOW": {
        "description": "Minimal risk of harm",
        "examples": ["spell_check", "photo_filters", "basic_automation", "simple_classification"],
    },
}

# ISO 42001 Annex A Control Objectives
ANNEX_A_CONTROLS = {
    "A.5": "Leadership",
    "A.6": "Planning",
    "A.7": "Support",
    "A.8": "Operation",
    "A.9": "Performance evaluation",
    "A.10": "Improvement",
}

# Regulatory alignment mapping
REGULATORY_ALIGNMENT = {
    # ISO 42001 Clause → EU AI Act Article
    "5": ["9"],   # Leadership → Risk management
    "6": ["10"],  # Planning → Data governance
    "7": ["11"],  # Support → Technical documentation
    "8": ["12"],  # Operation → Record-keeping
    "9": ["13"],  # Performance → Transparency
    "10": ["14"], # Improvement → Human oversight
    # Additional controls
    "4": ["5"],   # Context → Prohibited practices
    "8.2": ["15"], # Operation security → Cybersecurity
}

# Actions where ISO 42001 likely doesn't apply
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
    if "ai_" in action or "_ai" in action or "model_" in action or "_model" in action:
        detection_evidence["methods_used"].append("ACTION_PATTERN")
        detection_evidence["confidence"] = "MEDIUM"
        detection_evidence["indicators_found"].append(f"action:{action}")
        return True, detection_evidence
    
    # Method 4: Industry classification
    industry = str(payload.get("industry_id", "")).upper().strip()
    if industry in AI_INDUSTRIES:
        detection_evidence["methods_used"].append("INDUSTRY_CLASSIFICATION")
        detection_evidence["confidence"] = "MEDIUM"
        detection_evidence["indicators_found"].append(f"industry:{industry}")
        return True, detection_evidence
    
    # Method 5: System type detection
    system_type = str(payload.get("system_type", "")).lower()
    if any(ai_type in system_type for ai_type in AI_SYSTEM_TYPES):
        detection_evidence["methods_used"].append("SYSTEM_TYPE")
        detection_evidence["confidence"] = "HIGH"
        detection_evidence["indicators_found"].append(f"system_type:{system_type}")
        return True, detection_evidence
    
    # Method 6: Data fields indicating AI
    data_fields = payload.get("data_fields", [])
    if isinstance(data_fields, list):
        ai_fields = [field for field in data_fields 
                    if any(ai_term in str(field).lower() for ai_term in ["model", "inference", "training", "prediction"])]
        if ai_fields:
            detection_evidence["methods_used"].append("DATA_FIELD_ANALYSIS")
            detection_evidence["confidence"] = "MEDIUM"
            detection_evidence["indicators_found"].extend([f"field:{f}" for f in ai_fields[:3]])
            return True, detection_evidence
    
    return False, detection_evidence


def _classify_ai_impact(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Classify AI system impact level.
    
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
    
    # Factor 3: Industry context
    industry = str(payload.get("industry_id", "")).upper()
    classification_evidence["factors_considered"].append(f"INDUSTRY:{industry}")
    
    if industry in {"HEALTHCARE_AI", "DEFENSE_AI", "ENERGY_AI", "TRANSPORTATION_AI"}:
        classification_evidence["impact_level"] = "CRITICAL"
        classification_evidence["confidence"] = "MEDIUM"
        return "CRITICAL", classification_evidence
    
    if industry in {"FINTECH_AI", "GOVERNMENT_AI", "EDTECH_AI"}:
        classification_evidence["impact_level"] = "HIGH"
        classification_evidence["confidence"] = "MEDIUM"
        return "HIGH", classification_evidence
    
    # Factor 4: Risk indicators
    risk_indicators = payload.get("risk_indicators", {})
    if risk_indicators.get("high_risk_flag") or risk_indicators.get("critical_risk"):
        classification_evidence["factors_considered"].append("RISK_INDICATORS")
        classification_evidence["impact_level"] = "HIGH"
        classification_evidence["confidence"] = "LOW"
        return "HIGH", classification_evidence
    
    # Default: MODERATE (most common for deployed AI)
    classification_evidence["impact_level"] = "MODERATE"
    classification_evidence["confidence"] = "LOW"
    return "MODERATE", classification_evidence


def _determine_ai_lifecycle_stage(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Determine AI system lifecycle stage.
    
    Returns:
        (lifecycle_stage, determination_evidence)
        lifecycle_stage: One of AI_LIFECYCLE_STAGES or "UNKNOWN"
    """
    determination_evidence = {
        "factors_considered": [],
        "lifecycle_stage": "UNKNOWN",
        "confidence": "LOW",
    }
    
    action = str(payload.get("action", "")).lower()
    ai_profile = payload.get("ai_profile", {})
    
    # Factor 1: Action-based determination
    action_mapping = {
        "train": "model_training",
        "training": "model_training",
        "deploy": "model_deployment",
        "inference": "inference_serving",
        "predict": "inference_serving",
        "monitor": "monitoring_observability",
        "evaluate": "model_evaluation",
        "develop": "design_development",
        "collect": "data_collection",
    }
    
    for action_keyword, stage in action_mapping.items():
        if action_keyword in action:
            determination_evidence["factors_considered"].append(f"ACTION:{action}")
            determination_evidence["lifecycle_stage"] = stage
            determination_evidence["confidence"] = "MEDIUM"
            return stage, determination_evidence
    
    # Factor 2: AI profile indicators
    if ai_profile.get("is_training") or ai_profile.get("training_data"):
        determination_evidence["factors_considered"].append("TRAINING_INDICATOR")
        determination_evidence["lifecycle_stage"] = "model_training"
        determination_evidence["confidence"] = "MEDIUM"
        return "model_training", determination_evidence
    
    if ai_profile.get("is_deployed") or ai_profile.get("deployment_environment"):
        determination_evidence["factors_considered"].append("DEPLOYMENT_INDICATOR")
        determination_evidence["lifecycle_stage"] = "system_operation"
        determination_evidence["confidence"] = "MEDIUM"
        return "system_operation", determination_evidence
    
    # Factor 3: System characteristics
    if ai_profile.get("model_version") or ai_profile.get("model_architecture"):
        determination_evidence["factors_considered"].append("MODEL_CHARACTERISTICS")
        determination_evidence["lifecycle_stage"] = "design_development"
        determination_evidence["confidence"] = "LOW"
        return "design_development", determination_evidence
    
    # Default: Unknown
    return "UNKNOWN", determination_evidence


def _should_evaluate_iso_42001(payload: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Future-proof decision: Should ISO 42001 evaluation run for this payload?
    
    Returns:
        (should_evaluate, evaluation_reason, context_evidence)
    """
    context_evidence = {
        "ai_system_detection": {},
        "impact_classification": {},
        "lifecycle_stage_determination": {},
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
    
    # Check 4: Lifecycle stage
    lifecycle_stage, lifecycle_evidence = _determine_ai_lifecycle_stage(payload)
    context_evidence["lifecycle_stage_determination"] = lifecycle_evidence
    
    # All checks passed - evaluate ISO 42001
    return True, f"EVALUATE_ISO_42001_IMPACT:{impact_level}_STAGE:{lifecycle_stage}", context_evidence


# ============================================================
# ENFORCEMENT SCOPE RESOLUTION (FUTURE-PROOF)
# ============================================================

def _normalize_iso_42001_article(article: str) -> str:
    """
    Normalize ISO 42001 article identifier for consistent comparison.
    
    Future-proof examples:
        "ISO/IEC 42001 Cl. 5" → "5"
        "Annex A.6" → "6"
        "Clause 7.2" → "7.2"
        "EU AI Act Art. 9" → "9"
        "NIST AI RMF GOVERN 1.1" → "GOVERN_1.1"
    """
    if not article:
        return ""
    
    article = article.strip()
    
    # Remove common prefixes
    article = re.sub(r"(?i)^(iso\/iec\s*42001\s*)?(clause\s*|cl\.\s*)", "", article)
    article = re.sub(r"(?i)^(annex\s*a\.)", "", article)
    article = re.sub(r"(?i)^(eu\s*ai\s*act\s*)?(article\s*|art\.\s*)", "", article)
    article = re.sub(r"(?i)^(nist\s*ai\s*rmf\s*)", "", article)
    
    # Extract clause number with optional subclause
    match = re.match(r"(\d+(?:\.\d+)?)", article)
    if match:
        return match.group(1)
    
    # For NIST AI RMF references
    if "GOVERN" in article.upper():
        return "GOVERN_" + re.sub(r"\D", "", article)
    elif "MAP" in article.upper():
        return "MAP_" + re.sub(r"\D", "", article)
    elif "MEASURE" in article.upper():
        return "MEASURE_" + re.sub(r"\D", "", article)
    elif "MANAGE" in article.upper():
        return "MANAGE_" + re.sub(r"\D", "", article)
    
    return article.replace(" ", "_").upper()


def _get_iso_42001_base_enforcement_scope(article: str) -> str:
    """
    Get base enforcement scope from governance catalog.
    
    Future-proof ISO 42001 Classification:
    - Leadership (Cl. 5): GOVERNANCE (management system)
    - Planning (Cl. 6): PLATFORM_AUDIT (risk assessment, objectives)
    - Support (Cl. 7): POSTURE (resources, competence, awareness)
    - Operation (Cl. 8): TRANSACTION (operational controls)
    - Performance (Cl. 9): PLATFORM_AUDIT (monitoring, audit)
    - Improvement (Cl. 10): ADMINISTRATIVE (improvement actions)
    
    Returns: "TRANSACTION" | "PLATFORM_AUDIT" | "GOVERNANCE" | "POSTURE" | "ADMINISTRATIVE" | "TECHNICAL"
    Default: "PLATFORM_AUDIT" (safe - logs but doesn't block unknown articles)
    """
    article_normalized = _normalize_iso_42001_article(article)
    
    # First check catalog for ISO 42001 regime
    for regime in _GOVERNANCE_CATALOG.get("regimes", []):
        if regime.get("id") == ISO_42001_REGIME_ID:
            for domain in regime.get("domains", []):
                for art_def in domain.get("articles", []):
                    if art_def.get("article", "") == article_normalized:
                        return art_def.get("enforcement_scope", "PLATFORM_AUDIT")
    
    # Local mapping based on clause hierarchy
    iso_42001_scopes = {
        # Context (Cl. 4)
        "4": "GOVERNANCE",     # Understanding organization and context
        "4.1": "GOVERNANCE",   # Understanding organization
        "4.2": "GOVERNANCE",   # Understanding needs and expectations
        "4.3": "GOVERNANCE",   # Determining AIMS scope
        "4.4": "GOVERNANCE",   # AI management system
        
        # Leadership (Cl. 5)
        "5": "GOVERNANCE",
        "5.1": "GOVERNANCE",   # Leadership and commitment
        "5.2": "GOVERNANCE",   # Policy
        "5.3": "GOVERNANCE",   # Roles, responsibilities, authorities
        
        # Planning (Cl. 6)
        "6": "PLATFORM_AUDIT",
        "6.1": "PLATFORM_AUDIT", # Actions to address risks and opportunities
        "6.2": "PLATFORM_AUDIT", # AI objectives and planning
        
        # Support (Cl. 7)
        "7": "POSTURE",
        "7.1": "POSTURE",      # Resources
        "7.2": "POSTURE",      # Competence
        "7.3": "POSTURE",      # Awareness
        "7.4": "POSTURE",      # Communication
        "7.5": "POSTURE",      # Documented information
        
        # Operation (Cl. 8)
        "8": "TRANSACTION",
        "8.1": "TRANSACTION",  # Operational planning and control
        "8.2": "TRANSACTION",  # AI system development
        "8.3": "TRANSACTION",  # AI system deployment
        "8.4": "TRANSACTION",  # AI system operation
        "8.5": "TRANSACTION",  # AI system monitoring and maintenance
        
        # Performance evaluation (Cl. 9)
        "9": "PLATFORM_AUDIT",
        "9.1": "PLATFORM_AUDIT", # Monitoring, measurement, analysis
        "9.2": "PLATFORM_AUDIT", # Internal audit
        "9.3": "PLATFORM_AUDIT", # Management review
        
        # Improvement (Cl. 10)
        "10": "ADMINISTRATIVE",
        "10.1": "ADMINISTRATIVE", # Nonconformity and corrective action
        "10.2": "ADMINISTRATIVE", # Continual improvement
        
        # Regulatory alignment (EU AI Act)
        "9": "GOVERNANCE",     # Risk management (Art. 9)
        "10": "PLATFORM_AUDIT", # Data governance (Art. 10)
        "11": "POSTURE",       # Technical documentation (Art. 11)
        "12": "TRANSACTION",   # Record-keeping (Art. 12)
        "13": "PLATFORM_AUDIT", # Transparency (Art. 13)
        "14": "ADMINISTRATIVE", # Human oversight (Art. 14)
        "15": "TECHNICAL",     # Cybersecurity (Art. 15)
    }
    
    return iso_42001_scopes.get(article_normalized, "PLATFORM_AUDIT")


def _resolve_iso_42001_enforcement_scope(article: str, payload: Dict[str, Any]) -> str:
    """
    Resolve final enforcement scope with future-proof modifiers.
    
    ISO 42001 enforcement scope modifiers:
    1. AI system impact level escalation
    2. Lifecycle stage considerations
    3. Active incidents or nonconformities
    4. Regulatory alignment requirements
    
    Returns:
        Final enforcement scope after applying modifiers
    """
    base_scope = _get_iso_42001_base_enforcement_scope(article)
    article_normalized = _normalize_iso_42001_article(article)
    
    # Get context information
    impact_level, _ = _classify_ai_impact(payload)
    lifecycle_stage, _ = _determine_ai_lifecycle_stage(payload)
    ai_profile = payload.get("ai_profile", {})
    governance = payload.get("governance", {})
    
    # MODIFIER 1: High-impact AI system escalation
    if impact_level in {"CRITICAL", "HIGH"}:
        if base_scope in {"PLATFORM_AUDIT", "POSTURE", "ADMINISTRATIVE"}:
            # High-impact systems need stricter enforcement
            if article_normalized in {"8", "8.1", "8.2", "8.3", "8.4"}:
                return "TRANSACTION"  # Operational controls become transactional
    
    # MODIFIER 2: Deployment/operation stage escalation
    if lifecycle_stage in {"model_deployment", "inference_serving", "system_operation"}:
        if base_scope in {"PLATFORM_AUDIT", "POSTURE"} and article_normalized.startswith("8"):
            # Operational controls during deployment/operation
            return "TRANSACTION"
    
    # MODIFIER 3: Active incidents or nonconformities
    risk_indicators = payload.get("risk_indicators", {})
    if risk_indicators.get("ai_incident_active") or risk_indicators.get("nonconformity_detected"):
        if base_scope == "ADMINISTRATIVE" and article_normalized.startswith("10"):
            # Improvement actions during incidents
            return "TRANSACTION"
    
    # MODIFIER 4: Regulatory compliance requirements
    regulatory_context = str(payload.get("meta", {}).get("regulatory_context", "")).upper()
    if "EU_AI_ACT" in regulatory_context:
        # Map ISO 42001 to AI Act strict enforcement
        if article_normalized in {"9", "10", "14", "15"}:  # AI Act Articles
            if base_scope in {"PLATFORM_AUDIT", "POSTURE"}:
                return "TRANSACTION"
    
    # MODIFIER 5: Autonomous or high-autonomy AI
    if ai_profile.get("autonomous_decision_making") or ai_profile.get("high_autonomy"):
        if base_scope in {"PLATFORM_AUDIT", "POSTURE"}:
            # Higher autonomy requires stricter controls
            return "TRANSACTION"
    
    # No modifiers applied
    return base_scope


# ============================================================
# EVIDENCE COLLECTION (Enhanced for Future-Proofing)
# ============================================================

def _collect_iso_42001_evidence(payload: Dict[str, Any], rule_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect comprehensive ISO 42001 evidence for audit trails.
    
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
        # ISO 42001-specific information
        "iso_42001_info": {},
        # Metadata
        "metadata": {
            "evidence_collected_at": "NOW",  # Would be timestamp in real implementation
            "standard_version": "ISO/IEC 42001:2023",
        }
    }
    
    # Collect ISO 42001-specific information
    ai_profile = payload.get("ai_profile", {})
    governance = payload.get("governance", {})
    
    evidence["iso_42001_info"] = {
        "impact_level": ai_profile.get("impact_level"),
        "lifecycle_stage": ai_profile.get("lifecycle_stage"),
        "aime_scope_defined": governance.get("aime_scope_defined"),
        "management_review_date": governance.get("management_review_date"),
        "internal_audit_date": governance.get("internal_audit_date"),
    }
    
    return evidence


# ============================================================
# ISO 42001 RULE DEFINITIONS (Enhanced with Annex A Controls)
# ============================================================

# ISO 42001 rules with comprehensive metadata
ISO_42001_RULES = [
    # ============================================================
    # CONTEXT (Clause 4) - Understanding the organization
    # ============================================================
    {
        "article": "ISO/IEC 42001 Cl. 4.1",
        "title": "Understanding the Organization and Context",
        "description": "Determine external/internal issues relevant to AI management system.",
        "field": "context_analysis",
        "severity": "MEDIUM",
        "rule_id": "ISO_42001_CL4_1_CONTEXT",
        "enforcement_scope_default": "GOVERNANCE",
        "future_proof_notes": "Must consider legal, technological, competitive, cultural, social, economic environments.",
        "evidence_fields": ["governance.context_analysis", "governance.external_issues", "governance.internal_issues"],
        "annex_a_reference": "A.4",
        "regulatory_alignment": ["EU_AI_ACT_ART5"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "ISO/IEC 42001 Cl. 4.3",
        "title": "Determining AIMS Scope",
        "description": "Establish scope of AI management system considering organization context.",
        "field": "aime_scope_defined",
        "severity": "MEDIUM",
        "rule_id": "ISO_42001_CL4_3_SCOPE",
        "enforcement_scope_default": "GOVERNANCE",
        "future_proof_notes": "Scope must be documented and available to interested parties.",
        "evidence_fields": ["governance.aime_scope_defined", "governance.scope_documentation"],
        "annex_a_reference": "A.4",
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # LEADERSHIP (Clause 5)
    # ============================================================
    {
        "article": "ISO/IEC 42001 Cl. 5.1",
        "title": "Leadership and Commitment",
        "description": "Top management demonstrates leadership and commitment to AIMS.",
        "field": "top_management_commitment",
        "severity": "HIGH",
        "rule_id": "ISO_42001_CL5_1_LEADERSHIP",
        "enforcement_scope_default": "GOVERNANCE",
        "future_proof_notes": "Must integrate AIMS requirements into business processes.",
        "evidence_fields": ["governance.top_management_commitment", "governance.leadership_evidence"],
        "annex_a_reference": "A.5",
        "regulatory_alignment": ["EU_AI_ACT_ART9"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "ISO/IEC 42001 Cl. 5.2",
        "title": "AI Policy",
        "description": "Establish, implement, maintain AI policy appropriate to organization purpose.",
        "field": "ai_policy",
        "severity": "HIGH",
        "rule_id": "ISO_42001_CL5_2_POLICY",
        "enforcement_scope_default": "GOVERNANCE",
        "future_proof_notes": "Policy must include commitment to ethical AI, continuous improvement, compliance.",
        "evidence_fields": ["governance.ai_policy", "governance.policy_url", "governance.policy_version"],
        "annex_a_reference": "A.5",
        "regulatory_alignment": ["EU_AI_ACT_ART9"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "ISO/IEC 42001 Cl. 5.3",
        "title": "Roles, Responsibilities, Authorities",
        "description": "Assign roles, responsibilities, authorities for AIMS effectiveness.",
        "field": "roles_defined",
        "severity": "HIGH",
        "rule_id": "ISO_42001_CL5_3_ROLES",
        "enforcement_scope_default": "GOVERNANCE",
        "future_proof_notes": "Must include AI system owner, risk owner, compliance officer roles.",
        "evidence_fields": ["governance.roles_defined", "governance.owner", "governance.raci"],
        "annex_a_reference": "A.5",
        "regulatory_alignment": ["EU_AI_ACT_ART9"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # PLANNING (Clause 6)
    # ============================================================
    {
        "article": "ISO/IEC 42001 Cl. 6.1",
        "title": "Risk and Opportunity Management",
        "description": "Plan actions to address risks/opportunities affecting AIMS.",
        "field": "risk_assessment",
        "severity": "HIGH",
        "rule_id": "ISO_42001_CL6_1_RISK_MGMT",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Must consider AI-specific risks: bias, safety, security, transparency.",
        "evidence_fields": ["governance.risk_assessment", "governance.risk_register", "ai_profile.risk_assessment"],
        "annex_a_reference": "A.6",
        "regulatory_alignment": ["EU_AI_ACT_ART9", "EU_AI_ACT_ART10"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "ISO/IEC 42001 Cl. 6.2",
        "title": "AI Objectives and Planning",
        "description": "Establish AI objectives at relevant functions/levels.",
        "field": "ai_objectives",
        "severity": "MEDIUM",
        "rule_id": "ISO_42001_CL6_2_OBJECTIVES",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Objectives must be measurable, monitored, communicated, updated.",
        "evidence_fields": ["governance.ai_objectives", "governance.objectives_documented"],
        "annex_a_reference": "A.6",
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # SUPPORT (Clause 7)
    # ============================================================
    {
        "article": "ISO/IEC 42001 Cl. 7.2",
        "title": "Competence",
        "description": "Ensure persons doing work under AIMS control are competent.",
        "field": "competence_assurance",
        "severity": "MEDIUM",
        "rule_id": "ISO_42001_CL7_2_COMPETENCE",
        "enforcement_scope_default": "POSTURE",
        "future_proof_notes": "Based on education, training, experience for AI-specific roles.",
        "evidence_fields": ["governance.competence_assurance", "governance.training_records"],
        "annex_a_reference": "A.7",
        "regulatory_alignment": ["EU_AI_ACT_ART11"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "ISO/IEC 42001 Cl. 7.5",
        "title": "Documented Information",
        "description": "Control AIMS documented information per requirements.",
        "field": "technical_documentation",
        "severity": "MEDIUM",
        "rule_id": "ISO_42001_CL7_5_DOCUMENTATION",
        "enforcement_scope_default": "POSTURE",
        "future_proof_notes": "Includes creation, updating, control of documented information.",
        "evidence_fields": ["governance.technical_documentation", "governance.document_control"],
        "annex_a_reference": "A.7",
        "regulatory_alignment": ["EU_AI_ACT_ART11"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # OPERATION (Clause 8) - CRITICAL CONTROLS
    # ============================================================
    {
        "article": "ISO/IEC 42001 Cl. 8.1",
        "title": "Operational Planning and Control",
        "description": "Plan, implement, control processes needed for AIMS requirements.",
        "field": "operational_controls",
        "severity": "HIGH",
        "rule_id": "ISO_42001_CL8_1_OPERATIONAL",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Includes change management, configuration management, version control.",
        "evidence_fields": ["governance.operational_controls", "governance.change_management"],
        "annex_a_reference": "A.8",
        "regulatory_alignment": ["EU_AI_ACT_ART12"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "ISO/IEC 42001 Cl. 8.2",
        "title": "AI System Development",
        "description": "Establish, implement, maintain AI system development process.",
        "field": "development_process",
        "severity": "HIGH",
        "rule_id": "ISO_42001_CL8_2_DEVELOPMENT",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Includes requirements, design, implementation, testing, validation.",
        "evidence_fields": ["governance.development_process", "governance.model_inventory", "governance.testing_procedures"],
        "annex_a_reference": "A.8",
        "regulatory_alignment": ["EU_AI_ACT_ART15"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "ISO/IEC 42001 Cl. 8.4",
        "title": "AI System Operation",
        "description": "Ensure controlled conditions for AI system operation.",
        "field": "system_operation_controls",
        "severity": "HIGH",
        "rule_id": "ISO_42001_CL8_4_OPERATION",
        "enforcement_scope_default": "TRANSACTION",
        "future_proof_notes": "Includes monitoring, logging, access control, incident detection.",
        "evidence_fields": ["governance.system_operation_controls", "governance.monitoring_procedures"],
        "annex_a_reference": "A.8",
        "regulatory_alignment": ["EU_AI_ACT_ART13", "EU_AI_ACT_ART14"],
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # PERFORMANCE EVALUATION (Clause 9)
    # ============================================================
    {
        "article": "ISO/IEC 42001 Cl. 9.1",
        "title": "Monitoring, Measurement, Analysis",
        "description": "Monitor, measure, analyze AIMS performance and effectiveness.",
        "field": "performance_monitoring",
        "severity": "MEDIUM",
        "rule_id": "ISO_42001_CL9_1_MONITORING",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Includes KPIs, metrics, data collection methods, analysis techniques.",
        "evidence_fields": ["governance.performance_monitoring", "governance.kpis_defined"],
        "annex_a_reference": "A.9",
        "regulatory_alignment": ["EU_AI_ACT_ART13"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "ISO/IEC 42001 Cl. 9.2",
        "title": "Internal Audit",
        "description": "Conduct internal audits at planned intervals for AIMS.",
        "field": "internal_audit",
        "severity": "MEDIUM",
        "rule_id": "ISO_42001_CL9_2_AUDIT",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Audit program, criteria, scope, frequency, methods, responsibilities.",
        "evidence_fields": ["governance.internal_audit", "governance.audit_program"],
        "annex_a_reference": "A.9",
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # IMPROVEMENT (Clause 10)
    # ============================================================
    {
        "article": "ISO/IEC 42001 Cl. 10.1",
        "title": "Nonconformity and Corrective Action",
        "description": "React to nonconformities and take corrective actions.",
        "field": "incident_process",
        "severity": "HIGH",
        "rule_id": "ISO_42001_CL10_1_CORRECTIVE",
        "enforcement_scope_default": "ADMINISTRATIVE",
        "future_proof_notes": "Includes nonconformity identification, correction, root cause analysis, recurrence prevention.",
        "evidence_fields": ["governance.incident_process", "governance.incident_contact"],
        "annex_a_reference": "A.10",
        "regulatory_alignment": ["EU_AI_ACT_ART14"],
        "compliance_level": "REQUIRED",
    },
    {
        "article": "ISO/IEC 42001 Cl. 10.2",
        "title": "Continual Improvement",
        "description": "Continually improve suitability, adequacy, effectiveness of AIMS.",
        "field": "continuous_improvement",
        "severity": "MEDIUM",
        "rule_id": "ISO_42001_CL10_2_IMPROVEMENT",
        "enforcement_scope_default": "ADMINISTRATIVE",
        "future_proof_notes": "Based on audit results, analysis of data, management review.",
        "evidence_fields": ["governance.continuous_improvement", "governance.improvement_actions"],
        "annex_a_reference": "A.10",
        "compliance_level": "REQUIRED",
    },
    
    # ============================================================
    # ANNEX A CONTROLS (Additional Implementation Guidance)
    # ============================================================
    {
        "article": "ISO/IEC 42001 Annex A.8.4",
        "title": "AI System Impact Assessment",
        "description": "Assess potential impacts of AI system on individuals, groups, society.",
        "field": "impact_assessment",
        "severity": "HIGH",
        "rule_id": "ISO_42001_ANNEX_A8_4_IMPACT",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Consider fairness, transparency, accountability, human rights impacts.",
        "evidence_fields": ["governance.impact_assessment", "ai_profile.impact_level"],
        "annex_a_reference": "A.8",
        "regulatory_alignment": ["EU_AI_ACT_ART9", "EU_AI_ACT_ART13"],
        "compliance_level": "ADDRESSABLE",
        "future_implementation": True,
    },
    {
        "article": "ISO/IEC 42001 Annex A.8.5",
        "title": "AI System Transparency",
        "description": "Provide appropriate transparency about AI system capabilities/limitations.",
        "field": "transparency_measures",
        "severity": "MEDIUM",
        "rule_id": "ISO_42001_ANNEX_A8_5_TRANSPARENCY",
        "enforcement_scope_default": "PLATFORM_AUDIT",
        "future_proof_notes": "Includes explainability, interpretability, documentation, communication.",
        "evidence_fields": ["governance.transparency_measures", "ai_profile.explainability"],
        "annex_a_reference": "A.8",
        "regulatory_alignment": ["EU_AI_ACT_ART13"],
        "compliance_level": "ADDRESSABLE",
        "future_implementation": True,
    },
]


# ============================================================
# MAIN EVALUATION FUNCTION (Future-Proof Architecture)
# ============================================================

def evaluate_iso_42001_rules(payload: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Future-proof ISO/IEC 42001 evaluation with comprehensive context gating.
    
    Features:
    1. Multi-method AI system detection
    2. AI system impact classification
    3. Lifecycle stage determination
    4. Regulatory alignment mapping
    5. Enhanced enforcement scope resolution
    6. Comprehensive evidence collection
    7. Detailed context tracking
    8. Annex A controls support
    
    Returns:
        (policies, summary)
        - policies: List with enforcement_scope, evidence, and context
        - summary: Aggregate statistics with detailed context info
    """
    policies: List[Dict[str, Any]] = []
    
    # ============================================================
    # FUTURE-PROOF: CONTEXT GATING DECISION
    # ============================================================
    should_evaluate, evaluation_reason, context_evidence = _should_evaluate_iso_42001(payload)
    
    if not should_evaluate:
        # ISO 42001 doesn't apply - return with NOT_APPLICABLE
        policies.append({
            "domain": ISO_42001_DOMAIN,
            "regime": "ISO_42001",
            "framework": ISO_42001_FRAMEWORK,
            "domain_id": "ISO_42001",
            "article": "ISO/IEC 42001:APPLICABILITY",
            "category": "Applicability",
            "title": "Applicability",
            "status": "NOT_APPLICABLE",
            "severity": "LOW",
            "impact_on_verdict": "COMPLIANT",
            "trigger_type": "NOT_APPLICABLE",
            "rule_ids": ["ISO_42001_APPLICABILITY_NA"],
            "enforcement_scope": "SUPERVISORY",
            "notes": f"ISO 42001 evaluation skipped: {evaluation_reason}",
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
            "regime": "ISO_42001",
            "context_gated": True,
            "evaluation_decision": evaluation_reason,
            "context_evidence": context_evidence,
            "notes": f"ISO 42001 evaluation skipped: {evaluation_reason}"
        }
        return policies, summary
    
    # ============================================================
    # CONTEXT INFORMATION COLLECTION
    # ============================================================
    impact_level, impact_evidence = _classify_ai_impact(payload)
    lifecycle_stage, lifecycle_evidence = _determine_ai_lifecycle_stage(payload)
    ai_profile = payload.get("ai_profile", {}) or {}
    governance = payload.get("governance", {}) or {}
    risk_indicators = payload.get("risk_indicators", {}) or {}
    
    # ============================================================
    # RULE EVALUATION (Enhanced with Evidence Collection)
    # ============================================================
    
    evaluation_errors = []
    
    for rule_def in ISO_42001_RULES:
        # Skip future implementation rules if not ready
        if rule_def.get("future_implementation") and not governance.get("enable_future_controls"):
            continue
        
        try:
            # Check if the required field exists and is compliant
            field_value = governance.get(rule_def["field"])
            
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
            enforcement_scope = _resolve_iso_42001_enforcement_scope(rule_def["article"], payload)
            
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
            
            # Create policy
            policy = {
                "domain": ISO_42001_DOMAIN,
                "regime": "ISO_42001",
                "framework": ISO_42001_FRAMEWORK,
                "domain_id": "ISO_42001",
                "article": rule_def["article"],
                "category": rule_def["title"],
                "title": rule_def["title"],
                "status": status,
                "severity": severity if status == "VIOLATED" else "LOW",
                "enforcement_scope": enforcement_scope,
                "impact_on_verdict": impact_on_verdict,
                "trigger_type": "ISO_42001_CONTROL",
                "rule_ids": [rule_def["rule_id"]],
                "notes": rule_def["description"],
                "evidence": _collect_iso_42001_evidence(payload, rule_evidence),
                "remediation": (
                    f"Implement {rule_def['title']} controls per ISO 42001 requirements. "
                    "Document procedures and re-run GNCE after remediation."
                    if status == "VIOLATED" else "No remediation required."
                ),
                "violation_detail": rule_def["description"] if status == "VIOLATED" else "",
                "control_severity": rule_def["severity"],
                # Future-proof metadata
                "metadata": {
                    "annex_a_reference": rule_def.get("annex_a_reference"),
                    "regulatory_alignment": rule_def.get("regulatory_alignment", []),
                    "compliance_level": rule_def.get("compliance_level", "REQUIRED"),
                    "impact_level": impact_level,
                    "lifecycle_stage": lifecycle_stage,
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
        "lifecycle_stage": lifecycle_stage,
        "ai_system_detected": True,
    }
    
    # Count by clause type
    clause_counts = {}
    for clause in ["4", "5", "6", "7", "8", "9", "10"]:
        clause_counts[f"clause_{clause}_violations"] = sum(
            1 for p in policies 
            if p["status"] == "VIOLATED" and f"Cl. {clause}" in p["article"]
        )
    
    # Count by Annex A reference
    annex_counts = {}
    for annex_ref in ["A.4", "A.5", "A.6", "A.7", "A.8", "A.9", "A.10"]:
        annex_counts[f"annex_{annex_ref.replace('.', '_')}_violations"] = sum(
            1 for p in policies 
            if p["status"] == "VIOLATED" and 
            p.get("metadata", {}).get("annex_a_reference") == annex_ref
        )
    
    summary = {
        "total_rules": len(policies),
        "passed": passed,
        "failed": failed,
        "blocking_failures": blocking,
        "regime": "ISO_42001",
        "context_gated": False,
        "evaluation_decision": evaluation_reason,
        # Context information
        "context": context_info,
        "context_evidence": context_evidence,
        # AI system characteristics
        "impact_level": impact_level,
        "impact_classification": impact_evidence,
        "lifecycle_stage": lifecycle_stage,
        "lifecycle_determination": lifecycle_evidence,
        # Violation breakdown
        **clause_counts,
        **annex_counts,
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
        "posture_violations": sum(1 for p in policies 
                                if p["status"] == "VIOLATED" and p.get("enforcement_scope") == "POSTURE"),
        "transaction_violations": sum(1 for p in policies 
                                    if p["status"] == "VIOLATED" and p.get("enforcement_scope") == "TRANSACTION"),
        "administrative_violations": sum(1 for p in policies 
                                       if p["status"] == "VIOLATED" and p.get("enforcement_scope") == "ADMINISTRATIVE"),
        # Regulatory alignment
        "eu_ai_act_aligned_violations": sum(1 for p in policies 
                                          if p["status"] == "VIOLATED" and 
                                          "EU_AI_ACT" in str(p.get("metadata", {}).get("regulatory_alignment", []))),
        # Rule statistics
        "core_rules_evaluated": len([r for r in ISO_42001_RULES if not r.get("future_implementation")]),
        "future_rules_available": len([r for r in ISO_42001_RULES if r.get("future_implementation")]),
        "future_rules_evaluated": len([r for r in ISO_42001_RULES if r.get("future_implementation") 
                                      and governance.get("enable_future_controls")]),
        # Error tracking
        "evaluation_errors": evaluation_errors if evaluation_errors else None,
    }
    
    return policies, summary