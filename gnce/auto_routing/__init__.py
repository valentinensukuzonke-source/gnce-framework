# File: gnce/auto_routing/__init__.py
"""
Auto-routing module for GNCE framework.
"""
from .router import AutoRouter
from .registry_helper import load_profiles_to_registry

__version__ = "1.0.0"
__all__ = ["AutoRouter", "load_profiles_to_registry"]