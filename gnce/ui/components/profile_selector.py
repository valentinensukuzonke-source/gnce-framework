# File: gnce/ui/components/profile_selector.py
"""
Profile selector component with auto-routing integration.
"""
from __future__ import annotations

import streamlit as st
from typing import List, Dict, Any, Optional, Tuple
import json
from pathlib import Path

# Try to import auto-router
try:
    from gnce.auto_routing import AutoRouter
    AUTO_ROUTING_AVAILABLE = True
except ImportError:
    AUTO_ROUTING_AVAILABLE = False


class ProfileSelector:
    """
    Handles industry and customer profile selection with auto-routing support.
    """
    
    def __init__(self, profiles_dir: Path = Path("gnce/profiles/")):
        self.profiles_dir = profiles_dir
        self.profiles = self._load_profiles()
        
        if AUTO_ROUTING_AVAILABLE:
            self.router = AutoRouter(str(profiles_dir))
        else:
            self.router = None
    
    def _load_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Load all profile JSON files from the profiles directory."""
        profiles = {}
        
        if not self.profiles_dir.exists():
            st.warning(f"Profiles directory not found: {self.profiles_dir}")
            return profiles
        
        for profile_file in self.profiles_dir.glob("*.json"):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                    profile_id = profile_data.get("profile_id", profile_file.stem)
                    profiles[profile_id] = profile_data
            except Exception as e:
                st.warning(f"Failed to load profile {profile_file}: {e}")
        
        return profiles
    
    def get_available_profiles(self) -> List[str]:
        """Get list of available profile IDs for dropdown."""
        return list(self.profiles.keys())
    
    def get_profile_display_names(self) -> Dict[str, str]:
        """Get mapping of profile_id -> display_name for UI."""
        return {
            profile_id: data.get("display_name", profile_id)
            for profile_id, data in self.profiles.items()
        }
    
    def render_profile_selection(
        self,
        payload: Optional[Dict[str, Any]] = None,
        default_profile: Optional[str] = None,
        key_prefix: str = ""
    ) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
        """
        Render profile selection UI with auto-routing suggestions.
        
        Returns:
            (selected_profile_id, selected_customer_profile, routing_info)
        """
        routing_info = {}
        
        # Get auto-routing suggestion if payload is provided
        auto_suggestion = None
        if payload and self.router:
            routing_info = self.router.route(payload)
            auto_suggestion = routing_info.get("routing_suggestion", {})
        
        # Check if auto-selection is enabled from input_editor
        auto_select_enabled = st.session_state.get("auto_select_enabled", False)
        
        # Get available profiles for dropdown
        available_profiles = self.get_available_profiles()
        display_names = self.get_profile_display_names()
        
        # Create display options for dropdown
        display_options = [display_names.get(pid, pid) for pid in available_profiles]
        profile_to_display = {display_names.get(pid, pid): pid for pid in available_profiles}
        
        # Determine default selection
        default_selection = default_profile
        
        if auto_suggestion and auto_select_enabled:
            suggested_profile = auto_suggestion.get("industry_profile")
            if suggested_profile in available_profiles:
                default_selection = suggested_profile
                # Auto-set in session state
                st.session_state[f"{key_prefix}_selected_profile"] = suggested_profile
        
        # If we have a session state value, use it
        session_key = f"{key_prefix}_selected_profile"
        if session_key in st.session_state:
            default_selection = st.session_state[session_key]
        
        # Render profile selection dropdown
        st.markdown("### 🏢 Industry Profile Selection")
        
        # Show auto-routing suggestion if available
        if auto_suggestion and auto_suggestion.get("industry"):
            confidence = routing_info.get("confidence", {}).get("level", "low")
            confidence_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(confidence, "⚪")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"**Auto-detected**: {auto_suggestion['industry'].title()} "
                       f"({confidence_emoji} {confidence.upper()} confidence)")
            with col2:
                if auto_select_enabled:
                    st.success("✅ Auto-selection enabled")
                else:
                    st.info("⏸️ Manual selection")
        
        # Create the profile selector
        if default_selection and default_selection in available_profiles:
            default_display = display_names.get(default_selection, default_selection)
            default_index = display_options.index(default_display)
        else:
            default_index = 0
        
        selected_display = st.selectbox(
            "Select Industry Profile",
            options=display_options,
            index=default_index,
            key=f"{key_prefix}_profile_dropdown",
            help="Choose the industry profile for this evaluation. "
                 "Auto-routing suggestions will be shown if detected."
        )
        
        # Convert display name back to profile ID
        selected_profile = profile_to_display.get(selected_display)
        
        # Store in session state
        st.session_state[session_key] = selected_profile
        
        # Customer profile selection (simplified - can be enhanced)
        customer_profile = self._render_customer_profile(
            selected_profile, auto_suggestion, key_prefix
        )
        
        return selected_profile, customer_profile, routing_info
    
    def _render_customer_profile(
        self,
        industry_profile: Optional[str],
        auto_suggestion: Optional[Dict[str, Any]],
        key_prefix: str
    ) -> Optional[str]:
        """Render customer profile selection."""
        # Simple customer profiles for now - can be expanded
        customer_profiles = {
            "default": "Default Customer",
            "hipaa_compliant_customer": "HIPAA Compliant Customer",
            "pci_audited_customer": "PCI Audited Customer", 
            "standard_consumer": "Standard Consumer",
            "enterprise_customer": "Enterprise Customer",
            "social_media_user": "Social Media User"
        }
        
        # Determine default customer profile
        default_customer = "default"
        
        if auto_suggestion and st.session_state.get("auto_select_enabled", False):
            suggested_customer = auto_suggestion.get("customer_profile")
            if suggested_customer in customer_profiles:
                default_customer = suggested_customer
                st.session_state[f"{key_prefix}_customer_profile"] = suggested_customer
        
        # Get customer profile from session state
        session_key = f"{key_prefix}_customer_profile"
        if session_key in st.session_state:
            default_customer = st.session_state[session_key]
        
        # Render customer profile selector
        st.markdown("#### 👥 Customer Profile")
        
        customer_options = list(customer_profiles.keys())
        display_options = [customer_profiles[c] for c in customer_options]
        display_to_key = {customer_profiles[c]: c for c in customer_options}
        
        if default_customer in customer_options:
            default_display = customer_profiles[default_customer]
            default_index = display_options.index(default_display)
        else:
            default_index = 0
        
        selected_display = st.selectbox(
            "Select Customer Profile",
            options=display_options,
            index=default_index,
            key=f"{key_prefix}_customer_dropdown",
            help="Select the customer profile for this evaluation"
        )
        
        selected_customer = display_to_key.get(selected_display)
        st.session_state[session_key] = selected_customer
        
        return selected_customer
    
    def get_profile_config(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get full configuration for a selected profile."""
        return self.profiles.get(profile_id)


def render_profile_selector_with_auto_routing(
    payload: Optional[Dict[str, Any]] = None,
    config_path: Optional[Path] = None
) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, Any]]]:
    """
    Main entry point for profile selection with auto-routing.
    
    This function should be called from your main app to render the
    profile selection UI with auto-routing capabilities.
    """
    # Initialize selector
    selector = ProfileSelector()
    
    # Get default profile from config if provided
    default_profile = None
    if config_path and config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                default_profile = config.get("profile_id")
        except:
            pass
    
    # Render the selection UI
    profile_id, customer_profile, routing_info = selector.render_profile_selection(
        payload=payload,
        default_profile=default_profile,
        key_prefix="main"
    )
    
    # Show selected profile details
    if profile_id:
        profile_config = selector.get_profile_config(profile_id)
        if profile_config:
            with st.expander("📋 Selected Profile Details", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Profile", profile_config.get("display_name", profile_id))
                    st.caption(f"ID: `{profile_id}`")
                with col2:
                    st.metric("Jurisdiction", profile_config.get("scope", {}).get("jurisdiction", "N/A"))
                    regimes = profile_config.get("scope", {}).get("enabled_regimes", [])
                    st.caption(f"Regimes: {', '.join(regimes[:3])}")
                
                # Show enabled domains
                if "enabled_domains" in profile_config.get("scope", {}):
                    st.markdown("**Enabled Domains:**")
                    domains = profile_config["scope"]["enabled_domains"]
                    for regime, regime_domains in domains.items():
                        st.caption(f"- {regime}: {', '.join(regime_domains[:2])}")
                        if len(regime_domains) > 2:
                            st.caption(f"  ...and {len(regime_domains) - 2} more")
    
    return profile_id, customer_profile, routing_info