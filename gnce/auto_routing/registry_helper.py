# File: gnce/auto_routing/registry_helper.py
"""
Helper functions for loading profiles into the industry registry.
"""
import json
from pathlib import Path
from typing import Dict, Any

def load_profiles_to_registry(profiles_dir: str, industry_registry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load profile files and integrate them into the industry registry.
    
    Args:
        profiles_dir: Path to profiles directory
        industry_registry: Existing industry registry
        
    Returns:
        Updated industry registry
    """
    profiles_path = Path(profiles_dir)
    
    if not profiles_path.exists():
        print(f"Warning: Profiles directory not found: {profiles_dir}")
        return industry_registry
    
    for profile_file in profiles_path.glob("*.json"):
        try:
            with open(profile_file, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            # Extract profile metadata
            profile_id = profile_data.get("id") or profile_file.stem.upper()
            industry = profile_data.get("meta", {}).get("platform_classification", {}).get("industry")
            
            if industry and profile_id:
                # Ensure industry exists in registry
                if industry not in industry_registry:
                    industry_registry[industry] = {
                        "display_name": industry.replace("_", " ").title(),
                        "profiles": {}
                    }
                
                # Add profile to industry
                industry_registry[industry]["profiles"][profile_id] = {
                    "display_name": profile_data.get("name") or profile_id.replace("_", " ").title(),
                    "description": profile_data.get("description", ""),
                    "enabled_regimes": profile_data.get("scope", {}).get("enabled_regimes", []),
                    "profile_data": profile_data  # Keep full data for reference
                }
                
                print(f"Loaded profile: {profile_id} for industry: {industry}")
                
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading profile {profile_file}: {e}")
    
    return industry_registry