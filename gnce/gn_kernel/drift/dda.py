# gnce/gn_kernel/drift/dda.py
from __future__ import annotations

from typing import Any, Dict, Optional
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path


def _fingerprint(obj: Any) -> str:
    """
    Stable fingerprint for drift comparisons.
    Uses JSON canonicalization where possible.
    """
    try:
        blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    except Exception:
        blob = str(obj).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


# ===================================================================
# PERSISTENT BASELINE STORAGE (file-based, survives app restarts)
# ===================================================================
BASELINE_FILE = Path("data/drift_baselines.json")


def _load_baselines() -> Dict[str, Dict[str, Any]]:
    """Load baselines from disk."""
    if not BASELINE_FILE.exists():
        return {}
    try:
        with BASELINE_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_baselines(baselines: Dict[str, Dict[str, Any]]) -> None:
    """Save baselines to disk."""
    BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with BASELINE_FILE.open("w", encoding="utf-8") as f:
        json.dump(baselines, f, indent=2, default=str)


def evaluate_drift(
    payload: Dict[str, Any],
    policies: Optional[list] = None,
    l1: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    L6 Drift Detection Agent (DDA)

    Detects behavioral drift by comparing current request
    against established baseline for this user/action pattern.

    Returns drift outcome, score, and fingerprints.
    """
    policies = policies or []
    l1 = l1 or {}

    # Generate fingerprints
    payload_fp = _fingerprint(payload)
    policies_fp = _fingerprint(policies)
    l1_fp = _fingerprint({
        "decision_outcome": l1.get("decision_outcome"),
        "severity": l1.get("severity"),
    })

    # Extract user/action for baseline key
    user_id = payload.get("user_id", "unknown")
    action = payload.get("action", "unknown")
    baseline_key = f"{user_id}:{action}"

    # Calculate current behavioral fingerprint
    current_fingerprint = _calculate_behavioral_fingerprint(payload, l1, policies)

    # Load baselines from disk
    baselines = _load_baselines()
    baseline = baselines.get(baseline_key)

    if not baseline:
        # First time seeing this user/action - establish baseline
        baselines[baseline_key] = {
            "fingerprint": current_fingerprint,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "sample_count": 1,
        }
        _save_baselines(baselines)
        
        return {
            "drift_status": "NO_DRIFT",
            "drift_outcome": "NO_DRIFT",
            "drift_score": 0.0,
            "reason": f"Baseline established for {user_id}:{action}.",
            "signals": {
                "payload_fingerprint": payload_fp,
                "policies_fingerprint": policies_fp,
                "l1_fingerprint": l1_fp,
            },
        }
    
    # Compare against baseline
    drift_score = _calculate_drift_score(baseline["fingerprint"], current_fingerprint)

    # Update baseline (exponential moving average: 90% old, 10% new)
    baseline["fingerprint"] = _update_baseline(
        baseline["fingerprint"],
        current_fingerprint,
        alpha=0.1
    )
    baseline["sample_count"] = baseline.get("sample_count", 1) + 1
    baselines[baseline_key] = baseline
    _save_baselines(baselines)

    # Determine outcome
    if drift_score >= 0.6:
        outcome = "DRIFT_ALERT"
        reason = _explain_drift(baseline["fingerprint"], current_fingerprint, drift_score)
    else:
        outcome = "NO_DRIFT"
        reason = f"Behavior within expected baseline (drift score: {drift_score:.2f})."

    return {
        "drift_status": outcome,
        "drift_outcome": outcome,
        "drift_score": round(drift_score, 2),
        "reason": reason,
        "human_rationale": reason if outcome == "DRIFT_ALERT" else None,
        "signals": {
            "payload_fingerprint": payload_fp,
            "policies_fingerprint": policies_fp,
            "l1_fingerprint": l1_fp,
        },
    }


def _calculate_behavioral_fingerprint(
    payload: Dict[str, Any],
    l1: Dict[str, Any],
    policies: list
) -> Dict[str, float]:
    """
    Calculate behavioral fingerprint for this ADRA.
    Returns normalized feature vector (all values 0.0-1.0).
    """
    risk_indicators = payload.get("risk_indicators", {})

    return {
        "harmful_content_flag": 1.0 if risk_indicators.get("harmful_content_flag") else 0.0,
        "bot_probability": float(risk_indicators.get("bot_probability", 0.0)),
        "previous_violations": min(float(risk_indicators.get("previous_violations", 0)) / 10.0, 1.0),
        "severity_score": _severity_to_score(l1.get("severity", "LOW")),
        "violation_count": min(sum(1 for p in policies if p.get("status") == "VIOLATED") / 5.0, 1.0),
    }


def _severity_to_score(severity: str) -> float:
    """Convert severity string to numeric score."""
    mapping = {
        "LOW": 0.1,
        "MEDIUM": 0.4,
        "HIGH": 0.7,
        "CRITICAL": 1.0,
    }
    return mapping.get(str(severity).upper(), 0.0)


def _calculate_drift_score(
    baseline: Dict[str, float],
    current: Dict[str, float]
) -> float:
    """
    Calculate drift score (0.0 to 1.0) using weighted Euclidean distance.
    Higher weights = more important signals.
    """
    weights = {
        "harmful_content_flag": 2.5,  # Critical - highest weight
        "severity_score": 2.0,
        "bot_probability": 1.5,
        "previous_violations": 1.5,
        "violation_count": 1.0,
    }

    total_distance = 0.0
    total_weight = 0.0

    for key in baseline:
        if key in current:
            distance = abs(baseline[key] - current[key])
            weight = weights.get(key, 1.0)
            total_distance += distance * weight
            total_weight += weight

    if total_weight == 0:
        return 0.0

    # Normalize to 0-1 range
    return min(total_distance / total_weight, 1.0)


def _update_baseline(
    baseline: Dict[str, float],
    current: Dict[str, float],
    alpha: float = 0.1
) -> Dict[str, float]:
    """
    Update baseline using exponential moving average.
    alpha: weight for new observation (0.1 = 10% new, 90% old)
    """
    updated = {}
    for key in baseline:
        if key in current:
            updated[key] = (1 - alpha) * baseline[key] + alpha * current[key]
        else:
            updated[key] = baseline[key]
    return updated


def _explain_drift(
    baseline: Dict[str, float],
    current: Dict[str, float],
    score: float
) -> str:
    """
    Generate human-readable explanation of what changed.
    """
    drifts = []

    for key, baseline_val in baseline.items():
        current_val = current.get(key, 0.0)
        diff = abs(current_val - baseline_val)

        if diff > 0.3:  # Significant change threshold
            direction = "increased" if current_val > baseline_val else "decreased"
            readable_key = key.replace("_", " ")
            drifts.append(f"{readable_key} {direction} significantly")

    if drifts:
        return (
            f"DRIFT_ALERT (score: {score:.2f}): {', '.join(drifts)}. "
            "Pattern deviates from established baseline. "
            "Forced recalibration recommended."
        )
    else:
        return (
            f"DRIFT_ALERT (score: {score:.2f}): "
            "Cumulative behavioral deviation from baseline detected. "
            "Review user activity patterns."
        )