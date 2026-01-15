# gnce/kernel/orchestrator/ochestrator.py
from __future__ import annotations

"""
GNCE Orchestrator (Compatibility Shim)

This module exists for backward compatibility only.
The constitutional authority for execution is:
    gnce.gn_kernel.kernel.run_gn_kernel

IMPORTANT:
- This shim must never mutate ADRAs
- This shim must never compute adra_hash
- This shim must never export/federate
"""

from typing import Any, Dict


def run_gn_kernel(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compatibility wrapper. Prefer importing:
        from gnce.gn_kernel.kernel import run_gn_kernel
    """
    from gnce.gn_kernel.kernel import run_gn_kernel as _run

    return _run(payload)
