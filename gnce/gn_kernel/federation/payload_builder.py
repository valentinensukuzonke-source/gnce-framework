from __future__ import annotations

from typing import Any, Dict

from gnce.gn_kernel.redaction import redact_adra_for_regulator


def build_payload(adra: Dict[str, Any], mode: str) -> Dict[str, Any]:
    """
    Build the export payload for a given federation mode.

    Modes:
    - HASH_ONLY: minimal identity & integrity anchors
    - REDACTED: regulator-safe ADRA
    - FULL: full ADRA
    """
    mode = (mode or "OFF").upper().strip()

    if mode == "HASH_ONLY":
        l5 = adra.get("L5_integrity_and_tokenization") or {}
        return {
            "adra_id": adra.get("adra_id"),
            "adra_hash": adra.get("adra_hash"),
            "gnce_contract_version": adra.get("gnce_contract_version"),
            "adra_version": adra.get("adra_version"),
            "GNCE_version": adra.get("GNCE_version"),
            "created_at_utc": adra.get("created_at_utc"),
            "integrity": l5,
        }

    if mode == "REDACTED":
        return redact_adra_for_regulator(adra)

    if mode == "FULL":
        return adra

    return {}
