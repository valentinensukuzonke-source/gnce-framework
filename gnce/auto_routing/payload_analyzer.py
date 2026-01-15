"""
Payload analyzer for auto-routing industry detection.
"""
import json
from typing import Dict, Any, Set, Optional, List
from dataclasses import dataclass


@dataclass
class DetectionResult:
    """Structured result of industry detection."""
    industry: Optional[str]
    confidence: str  # 'high' | 'medium' | 'low'
    matched_fields: List[str]
    suggested_profile_id: Optional[str]
    jurisdiction_hint: Optional[str]


class PayloadAnalyzer:
    """
    Analyzes payload structure and content to detect industry patterns.
    Integrates with existing profile system.
    """
    
    # Industry detection rules based on your profile meta.platform_classification
    INDUSTRY_RULES = {
        "healthcare": {
            "required_fields": [{"patient_id"}, {"diagnosis_code"}, {"medical_record"}],
            "profile_candidates": ["HEALTHCARE_PROVIDER_EU", "HEALTHCARE_PROVIDER_US"],
            "jurisdiction_field": "patient_address.country"  # Could determine EU vs US
        },
        "fintech_payments": {
            "required_fields": [
                {"transaction_id", "amount", "currency"},
                {"iban", "swift_code"},
                {"payment_method", "transaction_type"}
            ],
            "profile_candidates": ["FINTECH_PAYMENTS_EU", "FINTECH_FRAUD_GLOBAL"],
            "jurisdiction_field": "billing_address.country"
        },
        "ecommerce": {
            "required_fields": [
                {"order_id", "sku", "quantity"},
                {"cart", "shipping_address"},
                {"product_price", "tax_amount"}
            ],
            "profile_candidates": ["ECOMMERCE_RETAIL_GLOBAL", "ECOMMERCE_MARKETPLACE_EU"],
            "jurisdiction_field": "shipping_address.country"
        },
        "saas_b2b": {
            "required_fields": [
                {"tenant_id", "subscription_tier"},
                {"user_id", "organization_id"},
                {"feature_flags", "api_key"}
            ],
            "profile_candidates": ["SAAS_ENTERPRISE_GLOBAL", "SAAS_PUBLIC_SECTOR_EU"],
            "jurisdiction_field": "tenant_region"
        },
        "vlop_social": {
            "required_fields": [
                {"user_generated_content", "post_id"},
                {"recommender_system", "ad_targeting"},
                {"content_moderation", "user_engagement"}
            ],
            "profile_candidates": ["VLOP_SOCIAL_META"],
            "jurisdiction_field": "user_region"
        }
    }
    
    def __init__(self, profile_registry_path: str = "gnce/profiles/"):
        self.profile_registry_path = profile_registry_path
    
    def extract_fields(self, payload: Dict[str, Any]) -> Set[str]:
        """Recursively extract all field paths from a nested payload."""
        fields = set()
        
        def _extract(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    fields.add(new_path)
                    _extract(value, new_path)
            elif isinstance(obj, list) and obj:
                # Check first element if list is not empty
                _extract(obj[0], f"{path}[]")
        
        _extract(payload)
        return fields
    
    def detect_industry(self, payload: Dict[str, Any]) -> DetectionResult:
        """
        Main detection method that analyzes payload against industry rules.
        Returns structured detection result.
        """
        fields = self.extract_fields(payload)
        matched_fields = []
        
        # Check each industry rule
        for industry, rules in self.INDUSTRY_RULES.items():
            for field_set in rules["required_fields"]:
                if field_set.issubset(fields):
                    matched_fields.extend(list(field_set))
                    
                    # Determine jurisdiction if possible
                    jurisdiction = self._detect_jurisdiction(payload, rules.get("jurisdiction_field"))
                    
                    # Select appropriate profile based on jurisdiction
                    profile_id = self._select_profile(
                        rules["profile_candidates"], 
                        jurisdiction
                    )
                    
                    return DetectionResult(
                        industry=industry,
                        confidence="high",
                        matched_fields=matched_fields,
                        suggested_profile_id=profile_id,
                        jurisdiction_hint=jurisdiction
                    )
        
        # Fallback for no clear match
        return DetectionResult(
            industry=None,
            confidence="low",
            matched_fields=[],
            suggested_profile_id=None,
            jurisdiction_hint=None
        )
    
    def _detect_jurisdiction(self, payload: Dict[str, Any], jurisdiction_field: Optional[str]) -> Optional[str]:
        """Extract jurisdiction hint from payload if field path exists."""
        if not jurisdiction_field:
            return None
        
        # Simple field path traversal
        parts = jurisdiction_field.split('.')
        current = payload
        
        try:
            for part in parts:
                if part.endswith('[]') and isinstance(current, list):
                    current = current[0] if current else {}
                    part = part[:-2]
                current = current.get(part, {})
            
            # If we get a string value, check if it's a country code
            if isinstance(current, str) and current.upper() in ['US', 'EU', 'GB', 'DE', 'FR']:
                return 'US' if current.upper() == 'US' else 'EU'
        except (AttributeError, KeyError, IndexError, TypeError):
            pass
        
        return None
    
    def _select_profile(self, candidates: List[str], jurisdiction: Optional[str]) -> Optional[str]:
        """Select the most appropriate profile from candidates based on jurisdiction."""
        if not candidates:
            return None
        
        if len(candidates) == 1:
            return candidates[0]
        
        # Prefer EU profiles for EU jurisdiction, otherwise first candidate
        if jurisdiction == 'EU':
            eu_profiles = [p for p in candidates if '_EU' in p]
            if eu_profiles:
                return eu_profiles[0]
        
        return candidates[0]