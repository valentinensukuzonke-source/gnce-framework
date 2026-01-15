"""
Profile resolver that maps detected industry to complete profile chain.
"""
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

class ProfileResolver:
    """
    Resolves the complete chain from industry to specific profile configuration.
    Integrates with existing profile JSON files.
    """
    
    def __init__(self, profiles_dir: str = "gnce/profiles/"):
        self.profiles_dir = Path(profiles_dir)
        self._profile_cache = {}
    
    def load_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Load a profile from the profiles directory."""
        if profile_id in self._profile_cache:
            return self._profile_cache[profile_id]
        
        profile_file = self.profiles_dir / f"{profile_id.lower()}.json"
        
        if not profile_file.exists():
            # Try alternative naming
            alt_file = self.profiles_dir / f"{profile_id}.json"
            if alt_file.exists():
                profile_file = alt_file
            else:
                return None
        
        try:
            with open(profile_file, 'r', encoding='utf-8') as f:
                profile = json.load(f)
                self._profile_cache[profile_id] = profile
                return profile
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading profile {profile_id}: {e}")
            return None
    
    def resolve_chain(self, industry: str, jurisdiction_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Resolve the complete profile chain for a detected industry.
        Returns a chain configuration that can be used by the UI.
        """
        # Default chain configuration
        chain = {
            "industry": industry,
            "industry_profile": None,
            "customer_profile": self._get_default_customer_profile(industry),
            "regimes": [],
            "confidence": "high" if industry else "low"
        }
        
        # Map industry to likely profile IDs
        profile_map = {
            "healthcare": {
                "EU": "HEALTHCARE_PROVIDER_EU",
                "US": "HEALTHCARE_PROVIDER_US",
                "default": "HEALTHCARE_PROVIDER_EU"
            },
            "fintech_payments": {
                "EU": "FINTECH_PAYMENTS_EU", 
                "default": "FINTECH_FRAUD_GLOBAL"
            },
            "ecommerce": {
                "EU": "ECOMMERCE_MARKETPLACE_EU",
                "default": "ECOMMERCE_RETAIL_GLOBAL"
            },
            "saas_b2b": {
                "EU": "SAAS_PUBLIC_SECTOR_EU",
                "default": "SAAS_ENTERPRISE_GLOBAL"
            },
            "vlop_social": {
                "default": "VLOP_SOCIAL_META"
            }
        }
        
        # Select appropriate profile
        if industry in profile_map:
            industry_config = profile_map[industry]
            
            if jurisdiction_hint and jurisdiction_hint in industry_config:
                profile_id = industry_config[jurisdiction_hint]
            else:
                profile_id = industry_config.get("default")
            
            # Load the profile to get enabled regimes
            profile = self.load_profile(profile_id)
            if profile:
                chain["industry_profile"] = profile_id
                chain["regimes"] = profile.get("scope", {}).get("enabled_regimes", [])
        
        return chain
    
    def _get_default_customer_profile(self, industry: str) -> str:
        """Get default customer profile based on industry."""
        customer_profile_map = {
            "healthcare": "hipaa_compliant_customer",
            "fintech_payments": "pci_audited_customer", 
            "ecommerce": "standard_consumer",
            "saas_b2b": "enterprise_customer",
            "vlop_social": "social_media_user"
        }
        return customer_profile_map.get(industry, "default_customer")