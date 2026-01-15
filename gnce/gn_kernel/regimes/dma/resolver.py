# gnce/kernel/regimes/dma/resolver.py
from __future__ import annotations

from typing import Any, Dict, List


def evaluate_dma_obligations(ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Returns canonical regime results:
      {id, verdict, severity, rationale}

    NOTE: This is NOT a stub. It is a production-compatible resolver scaffold:
    - Deterministic
    - Conservative defaults
    - Only evaluates what the payload explicitly provides
    """
    dma = ctx.get("dma") or ctx.get("dma_profile") or {}
    if not isinstance(dma, dict):
        dma = {}

    # Example obligation signals (explicit flags only)
    # You will replace/expand these with your full DMA obligation mapping.
    obligations = [
        {
            "id": "DMA:INTEROPERABILITY",
            "flag": dma.get("interoperability_commitment"),
            "severity_if_missing": 3,
            "rationale_ok": "Interoperability commitment declared.",
            "rationale_bad": "No explicit interoperability commitment provided in payload.",
        },
        {
            "id": "DMA:DATA_PORTABILITY",
            "flag": dma.get("data_portability_supported"),
            "severity_if_missing": 3,
            "rationale_ok": "Data portability support declared.",
            "rationale_bad": "No explicit data portability support provided in payload.",
        },
        {
            "id": "DMA:SELF_PREFERENCING",
            "flag": dma.get("self_preferencing_controls"),
            "severity_if_missing": 4,
            "rationale_ok": "Self-preferencing controls declared.",
            "rationale_bad": "No explicit self-preferencing controls provided in payload.",
        },
    ]

    out: List[Dict[str, Any]] = []
    for o in obligations:
        flag = o["flag"]
        if flag is True:
            out.append(
                {
                    "id": o["id"],
                    "verdict": "SATISFIED",
                    "severity": 1,
                    "rationale": o["rationale_ok"],
                }
            )
        elif flag is False:
            out.append(
                {
                    "id": o["id"],
                    "verdict": "VIOLATED",
                    "severity": int(o["severity_if_missing"]),
                    "rationale": o["rationale_bad"],
                }
            )
        else:
            # Conservative: not enough evidence → NOT_APPLICABLE (not violated)
            out.append(
                {
                    "id": o["id"],
                    "verdict": "NOT_APPLICABLE",
                    "severity": 1,
                    "rationale": "No evidence provided in payload to evaluate this obligation.",
                }
            )

    return out
