#gnce/kernel/constitution/policy_normalizer.py
from __future__ import annotations

from typing import Any, Dict, List, Optional


SEVERITY_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
SEVERITY_FROM_SCORE = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}


def _as_int(x: Any, default: int = 1) -> int:
    try:
        return int(x)
    except Exception:
        return default


def _norm_status(raw: Any) -> str:
    s = str(raw or "").strip().upper()
    if s in {"VIOLATED", "SATISFIED", "NOT_APPLICABLE"}:
        return s
    if s in {"N/A", "NA"}:
        return "NOT_APPLICABLE"
    return "UNKNOWN"


def _norm_severity(score: Any = None, level: Any = None) -> Dict[str, Any]:
    """
    Returns:
      { "severity_score": int(1..4), "severity_level": str(LOW|MEDIUM|HIGH|CRITICAL) }
    Accepts:
      - score as int/float/"1"
      - level as textual (LOW/MEDIUM/HIGH/CRITICAL)
    """
    if level is not None:
        lv = str(level or "").strip().upper()
        if lv in SEVERITY_ORDER:
            return {"severity_score": SEVERITY_ORDER[lv], "severity_level": lv}

    if score is None:
        return {"severity_score": 1, "severity_level": "LOW"}

    if isinstance(score, (int, float)) or (isinstance(score, str) and score.strip().isdigit()):
        sc = min(max(_as_int(score, 1), 1), 4)
        return {"severity_score": sc, "severity_level": SEVERITY_FROM_SCORE.get(sc, "LOW")}

    # fallback
    return {"severity_score": 1, "severity_level": "LOW"}


def normalise_regime_result(
    *,
    regime_id: str,
    domain: str,
    framework: str,
    item: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Convert a single regime-native result item into the policy-like structure
    consumed by GNCE_CONSTITUTION.adjudicate().

    Expected native fields (best effort):
      - id / reference / article
      - verdict / status
      - severity (1..4) or severity_level
      - rationale / notes / reason
      - meta (optional dict)
    """
    if not isinstance(item, dict):
        item = {"raw": item}

    # identity/reference
    ref = item.get("id") or item.get("reference") or item.get("article") or item.get("clause")
    ref = str(ref) if ref is not None else None

    # verdict/status
    status = _norm_status(item.get("verdict") or item.get("status"))

    # severity
    sev = _norm_severity(
        score=item.get("severity")
        or item.get("severity_score")
        or item.get("severityLevel")  # tolerate camelCase
        or item.get("criticality"),
        level=item.get("severity_level") or item.get("severityLevelText"),
    )

    # rationale
    rationale = (
        item.get("rationale")
        or item.get("notes")
        or item.get("reason")
        or item.get("explanation")
        or ""
    )

    out: Dict[str, Any] = {
        "regime": str(regime_id or ""),
        "domain": str(domain or ""),
        "framework": str(framework or ""),
        "article": ref,  # keep "article" name for continuity
        "status": status,
        "severity_score": sev["severity_score"],
        "severity_level": sev["severity_level"],
        "notes": str(rationale or ""),
    }

    meta = item.get("meta")
    if isinstance(meta, dict) and meta:
        out["meta"] = meta

    return out


def normalise_regime_bundle_to_policies(regimes: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Input:
      regimes dict shaped like:
        {
          "DSA": {"domain": "...", "framework": "...", "results": [ {...}, ... ]},
          ...
        }

    Output:
      List[policy_like] for L1 adjudication.
    """
    policies: List[Dict[str, Any]] = []

    if not isinstance(regimes, dict):
        return policies

    for rid, bundle in regimes.items():
        if not isinstance(bundle, dict):
            continue
        domain = bundle.get("domain") or ""
        framework = bundle.get("framework") or ""
        results = bundle.get("results") or []
        if not isinstance(results, list):
            continue

        for item in results:
            policies.append(
                normalise_regime_result(
                    regime_id=str(rid),
                    domain=str(domain),
                    framework=str(framework),
                    item=item if isinstance(item, dict) else {"raw": item},
                )
            )

    return policies
