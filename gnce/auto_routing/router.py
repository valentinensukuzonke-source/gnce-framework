# File: gnce/auto_routing/router.py
"""
Main auto-router orchestrator.
"""
import os
import sys
from typing import Dict, Any
import datetime

# Safer path handling - only add if needed
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Robust imports with fallbacks
try:
    from gnce.auto_routing.payload_analyzer import PayloadAnalyzer, DetectionResult
    from gnce.auto_routing.profile_resolver import ProfileResolver
    MODULES_LOADED = True
except ImportError:
    try:
        from .payload_analyzer import PayloadAnalyzer, DetectionResult
        from .profile_resolver import ProfileResolver
        MODULES_LOADED = True
    except ImportError as e:
        print(f"Warning: Could not import auto-routing modules: {e}", file=sys.stderr)
        MODULES_LOADED = False
        
        # Fallback classes if imports fail
        class DetectionResult:
            def __init__(self):
                self.industry = None
                self.confidence = 'low'
                self.matched_fields = []
                self.suggested_profile_id = None
                self.jurisdiction_hint = None
        
        class PayloadAnalyzer:
            def __init__(self, *args, **kwargs):
                pass
            
            def detect_industry(self, payload):
                result = DetectionResult()
                return result
            
            def extract_fields(self, payload):
                return set()
        
        class ProfileResolver:
            def __init__(self, *args, **kwargs):
                pass
            
            def resolve_chain(self, industry, jurisdiction_hint=None):
                return {
                    "industry": industry,
                    "industry_profile": None,
                    "customer_profile": "default_customer",
                    "regimes": [],
                    "confidence": "low"
                }


class AutoRouter:
    """
    Main orchestrator for auto-routing payloads to industry profiles.
    Designed to integrate with existing UI/API flows.
    """
    
    def __init__(self, profiles_dir: str = "gnce/profiles/", configs_dir: str = "gnce/configs/"):
        self.profiles_dir = profiles_dir
        self.configs_dir = configs_dir
        self.routing_history = []  # For audit trail
        self.modules_available = MODULES_LOADED
        
        # Initialize components with error handling
        try:
            self.analyzer = PayloadAnalyzer(profiles_dir)
            self.resolver = ProfileResolver(profiles_dir)
        except Exception as e:
            print(f"Warning: AutoRouter initialization error: {e}", file=sys.stderr)
            self.analyzer = PayloadAnalyzer()
            self.resolver = ProfileResolver()
    
    def route(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main routing method. Analyzes payload and returns complete routing suggestion.
        
        Args:
            input_payload: The incoming payload to analyze
            
        Returns:
            Dictionary with routing suggestions and confidence levels
        """
        # Step 1: Analyze payload for industry detection
        try:
            detection = self.analyzer.detect_industry(input_payload)
        except Exception as e:
            print(f"Warning: Payload analysis failed: {e}", file=sys.stderr)
            detection = DetectionResult()
        
        # Step 2: Resolve complete profile chain
        try:
            if detection.industry:
                chain = self.resolver.resolve_chain(
                    detection.industry, 
                    detection.jurisdiction_hint
                )
                
                # Override with detected profile if analyzer found one
                if detection.suggested_profile_id:
                    chain["industry_profile"] = detection.suggested_profile_id
            else:
                chain = self.resolver.resolve_chain(None)
        except Exception as e:
            print(f"Warning: Profile resolution failed: {e}", file=sys.stderr)
            chain = {
                "industry": None,
                "industry_profile": None,
                "customer_profile": "default_customer",
                "regimes": [],
                "confidence": "low"
            }
        
        # Step 3: Prepare result for UI integration
        try:
            result = {
                "routing_suggestion": {
                    "industry": detection.industry,
                    "industry_profile": chain.get("industry_profile"),
                    "customer_profile": chain.get("customer_profile", "default_customer"),
                    "regimes": chain.get("regimes", []),
                    "auto_selected": detection.confidence == "high"
                },
                "confidence": {
                    "level": detection.confidence,
                    "matched_fields": detection.matched_fields,
                    "jurisdiction_hint": detection.jurisdiction_hint
                },
                "payload_metadata": {
                    "field_count": len(self.analyzer.extract_fields(input_payload)),
                    "has_user_context": "user" in input_payload or "user_id" in input_payload
                },
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "routing_version": "phase1_rule_based",
                "modules_available": self.modules_available
            }
            
            # Store for audit trail
            self.routing_history.append({
                "timestamp": result["timestamp"],
                "industry": detection.industry,
                "profile": chain.get("industry_profile"),
                "confidence": detection.confidence
            })
            
            return result
        except Exception as e:
            print(f"Warning: Result preparation failed: {e}", file=sys.stderr)
            return {
                "routing_suggestion": {
                    "industry": None,
                    "industry_profile": None,
                    "customer_profile": "default_customer",
                    "regimes": [],
                    "auto_selected": False
                },
                "confidence": {
                    "level": "low",
                    "matched_fields": [],
                    "jurisdiction_hint": None
                },
                "payload_metadata": {
                    "field_count": 0,
                    "has_user_context": False
                },
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "routing_version": "fallback",
                "modules_available": False,
                "error": str(e)
            }
    
    def suggest_override(self, user_selection: Dict[str, Any], auto_suggestion: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare user selection with auto-suggestion and provide feedback.
        Useful for learning and improving rules over time.
        """
        differences = []
        
        for key in ["industry", "industry_profile", "customer_profile"]:
            if (user_selection.get(key) != auto_suggestion.get("routing_suggestion", {}).get(key)):
                differences.append({
                    "field": key,
                    "auto_value": auto_suggestion.get("routing_suggestion", {}).get(key),
                    "user_value": user_selection.get(key)
                })
        
        return {
            "has_differences": len(differences) > 0,
            "differences": differences,
            "recommendation": "Review auto-routing rules" if len(differences) > 1 else None
        }
    
    def simple_detect_from_filename(self, filename: str) -> Dict[str, str]:
        """
        Simple filename-based detection as fallback.
        This matches what your gn_app.py sidebar is using.
        """
        filename_lower = filename.lower()
        
        if "vlop" in filename_lower or "social" in filename_lower or "vlog" in filename_lower:
            return {
                "industry": "SOCIAL_MEDIA",
                "profile": "VLOP_SOCIAL_META",
                "method": "filename_pattern"
            }
        elif "ecom" in filename_lower or "purchase" in filename_lower or "shop" in filename_lower:
            return {
                "industry": "ECOMMERCE",
                "profile": "ECOMMERCE_MARKETPLACE_EU",
                "method": "filename_pattern"
            }
        elif "health" in filename_lower or "phi" in filename_lower or "patient" in filename_lower:
            return {
                "industry": "HEALTHCARE",
                "profile": "HEALTHCARE_PROVIDER_US",
                "method": "filename_pattern"
            }
        elif "fin" in filename_lower or "payment" in filename_lower or "transaction" in filename_lower:
            return {
                "industry": "FINTECH",
                "profile": "FINTECH_PAYMENTS_EU",
                "method": "filename_pattern"
            }
        elif "saas" in filename_lower:
            return {
                "industry": "SAAS",
                "profile": "SAAS_ENTERPRISE_GLOBAL",
                "method": "filename_pattern"
            }
        
        return {
            "industry": None,
            "profile": None,
            "method": "filename_pattern_no_match"
        }
