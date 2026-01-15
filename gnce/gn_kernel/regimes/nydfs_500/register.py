# gnce/gn_kernel/regimes/nydfs_500/register.py
from __future__ import annotations
from gnce.gn_kernel.regimes.register import register_regime
from gnce.gn_kernel.regimes.nydfs_500.applicability import is_applicable
from gnce.gn_kernel.regimes.nydfs_500.resolver import resolve

def register() -> None:
    register_regime(
        regime_id="NYDFS_500",
        display_name="NYDFS 23 NYCRR 500 (Cybersecurity Regulation)",
        domain="Cybersecurity Governance",
        framework="Security & Compliance",
        regime_type="REGULATION",
        jurisdiction="US-NY",
        authority="NYDFS",
        enforceable=True,
        l4_executable=True,
        applicability=is_applicable,
        resolver=resolve,
    )
