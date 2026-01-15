# ui/components/cet.py
from __future__ import annotations

from typing import Any, Dict, Optional
import streamlit as st


def _as_dict(x: Any) -> Optional[Dict[str, Any]]:
    return x if isinstance(x, dict) else None


def _first(adra: Dict[str, Any], *keys: str):
    for k in keys:
        v = adra.get(k)
        if v not in (None, {}, [], ""):
            return v
    return None


def extract_cet(adra: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Regulator-safe: never invent CET.
    Prefer explicit CET blocks, but fall back to known envelope locations
    that Decision Summary already uses (e.g. evidence_chain / integrity blocks).
    """
    # Common explicit keys
    cet = _first(adra, "CET", "cet", "cryptographic_evidence_token", "cryptographicEvidenceToken")
    cet = _as_dict(cet)
    if cet:
        return cet

    # Known envelope-level evidence container (you have this top-level key)
    ev = _as_dict(adra.get("evidence_chain"))
    if ev:
        # Some schemas store CET under evidence_chain["cet"] or similar
        inner = _as_dict(_first(ev, "cet", "CET", "cryptographic_evidence_token"))
        return inner or ev

    # L5 often holds integrity/tokenization artifacts
    l5 = _as_dict(_first(adra, "L5_integrity_and_tokenization", "L5"))
    if l5:
        inner = _as_dict(_first(l5, "cet", "CET", "cryptographic_evidence_token"))
        return inner or l5

    return None


def render_cet(adra: Dict[str, Any]) -> None:
    st.subheader("🔐 Cryptographic Evidence Token (CET)")

    cet = extract_cet(adra)
    if not cet:
        st.warning("No CET object found on this ADRA (and no evidence container present).")
        # regulator-safe debug
        with st.expander("Debug: top-level keys", expanded=False):
            st.json({"top_level_keys": sorted(list(adra.keys()))})
        return

    # Pull common fields if present (don’t assume names)
    signing_strategy = (
        cet.get("signing_strategy")
        or cet.get("strategy")
        or cet.get("signing")
        or cet.get("signer")
        or "—"
    )
    content_hash = (
    cet.get("content_hash")
    or cet.get("content_hash_sha256")
    or cet.get("hash")
    or cet.get("contentHash")
    or "—"
    )

    nonce = (
        cet.get("nonce")
        or cet.get("replay_guard")
        or cet.get("replayGuard")
        or "—"
    )


    signature = (
        cet.get("pseudo_signature")
        or cet.get("pseudo_signature_sha256")
        or cet.get("signature")
        or cet.get("sig")
        or "—"
    )

    # Nice summary like your Decision Summary panel
    st.markdown(
        f"**Signing strategy:** `{signing_strategy}`\n\n"
        f"- **Content hash:** `{content_hash}`\n"
        f"- **Nonce (replay guard):** `{nonce}`\n"
        f"- **Signature:** `{signature}`"
    )

    # Full regulator-grade JSON
    with st.expander("Full CET payload (regulator-grade JSON)", expanded=True):
        st.json(cet)
