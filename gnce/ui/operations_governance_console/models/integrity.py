# gnce/ui/operations_governance_console/models/integrity.py
from __future__ import annotations

from typing import Any, Dict, List
from collections import Counter


def sovereign_integrity(entries: List[Dict[str, Any]], session_fingerprint: str, constitution_hash: str | None) -> Dict[str, Any]:
    """
    Produces a sovereign-readout: integrity, determinism confidence, and trust-chain hints.
    This is READ-ONLY: we only summarize what is provable from entries.
    """
    if not entries:
        return {
            "integrity": "UNKNOWN",
            "determinism_confidence": 0.0,
            "constitution_hash": constitution_hash,
            "session_fingerprint": session_fingerprint,
            "notes": ["No entries loaded. Integrity cannot be assessed."],
        }

    verdicts = [e.get("_verdict") for e in entries]
    c = Counter(verdicts)
    total = sum(c.values()) or 1
    allow_rate = (c.get("ALLOW", 0) / total) * 100.0

    # Determinism confidence (v0.6.1 pragmatic):
    # If we can compute a stable fingerprint and entries contain timestamps/verdicts consistently,
    # we treat it as high confidence; else moderate.
    has_ts = sum(1 for e in entries if e.get("_dt") is not None)
    has_const = sum(1 for e in entries if e.get("_constitution_hash"))
    denom = len(entries) or 1
    ts_ratio = has_ts / denom
    const_ratio = has_const / denom

    confidence = 60.0
    if ts_ratio >= 0.8:
        confidence += 15.0
    if const_ratio >= 0.6:
        confidence += 15.0
    if constitution_hash:
        confidence += 5.0
    confidence = min(confidence, 99.0)

    integrity = "GREEN"
    notes: List[str] = []
    if constitution_hash is None:
        integrity = "AMBER"
        notes.append("No constitution hash found in ledger entries (add constitution_hash to ADRA metadata).")
    if const_ratio < 0.3:
        integrity = "AMBER"
        notes.append("Low constitution_hash coverage across entries; sovereign traceability is weakened.")
    if ts_ratio < 0.5:
        integrity = "AMBER"
        notes.append("Low timestamp coverage across entries; timeline evidence is weak.")
    if allow_rate < 20.0 and c.get("DENY", 0) > 0:
        integrity = "AMBER"
        notes.append("Very low ALLOW rate; system may be under policy constraint pressure.")
    if allow_rate < 10.0 and c.get("DENY", 0) >= 10:
        integrity = "RED"
        notes.append("Extreme constraint pressure observed (near-total denial).")

    return {
        "integrity": integrity,
        "determinism_confidence": round(confidence, 1),
        "constitution_hash": constitution_hash,
        "session_fingerprint": session_fingerprint,
        "verdict_counts": dict(c),
        "notes": notes or ["Sovereign integrity signals look stable from available evidence."],
    }
