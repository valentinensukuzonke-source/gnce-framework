from __future__ import annotations

from gnce.gn_kernel.regimes.register import register_regime
from .applicability import is_applicable
from .resolver import resolve

def register():
    register_regime(
        regime_id="HIPAA",
        display_name="HIPAA Privacy Rule",
        domain="Healthcare Data Protection",
        framework="HIPAA",
        regime_type="POLICY",
        jurisdiction="US",
        enforceable=True,
        l4_executable=True,
        authority="U.S. Department of Health & Human Services",
        applicability=is_applicable,
        resolver=resolve,
    )
