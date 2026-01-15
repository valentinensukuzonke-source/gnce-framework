# gnce/kernel/regimes/dsa/resolver.py
from __future__ import annotations

from typing import Any, Dict, List, Optional


Verdict = str  # "SATISFIED" | "VIOLATED" | "NOT_APPLICABLE"


def _dsa_profile(ctx: Dict[str, Any]) -> Dict[str, Any]:
    dsa = ctx.get("dsa") or ctx.get("dsa_profile") or {}
    return dsa if isinstance(dsa, dict) else {}


def _service_type(ctx: Dict[str, Any]) -> str:
    return str(ctx.get("service_type") or ctx.get("platform_type") or "").strip().upper()


def _truthy(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    s = str(v).strip().lower()
    return s in {"1", "true", "yes", "y", "on"}


def _result(
    article_id: str,
    verdict: Verdict,
    severity: int,
    rationale: str,
    evidence: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    sev = int(severity)
    if sev < 1:
        sev = 1
    if sev > 4:
        sev = 4

    out = {
        "id": article_id,
        "verdict": verdict,
        "severity": sev,
        "rationale": rationale,
    }
    if evidence:
        out["evidence"] = evidence
    return out


def evaluate_dsa_articles(ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Produce DSA article outcomes in canonical GNCE regime-result form:
      { id, verdict, severity(1-4), rationale, evidence? }

    Inputs are expected to be explicit signals in ctx['dsa'] / ctx['dsa_profile'].
    Conservative behavior:
      - If the service/article is not applicable → NOT_APPLICABLE
      - If applicable but evidence missing/false → VIOLATED
      - If applicable and evidence true → SATISFIED
    """
    if not isinstance(ctx, dict):
        return []

    market = str(ctx.get("market") or "").strip().upper()
    if market != "EU":
        return []  # DSA resolver should only run when applicability is already EU; keep safe.

    svc = _service_type(ctx)
    dsa = _dsa_profile(ctx)

    is_platform = svc in {"ONLINE_PLATFORM", "SOCIAL_PLATFORM", "MARKETPLACE", "VLOP", "VLOSE"}
    is_hosting_like = svc in {"HOSTING_SERVICE", "INTERMEDIARY_SERVICE"} or is_platform
    is_marketplace = svc == "MARKETPLACE"
    is_vlop = svc in {"VLOP", "VLOSE"}

    results: List[Dict[str, Any]] = []

    # -------------------------------
    # Art. 14 — Terms & conditions transparency (platform/hosting-facing)
    # -------------------------------
    if is_hosting_like:
        ok = _truthy(dsa.get("terms_published"))
        results.append(
            _result(
                "DSA:Art14",
                "SATISFIED" if ok else "VIOLATED",
                2 if ok else 2,
                "Terms & conditions are published and accessible." if ok else
                "Missing explicit signal that terms & conditions are published/accessed in the EU context.",
                {"terms_published": bool(ok)},
            )
        )
    else:
        results.append(_result("DSA:Art14", "NOT_APPLICABLE", 1, "Service type does not indicate hosting/platform context."))

    # -------------------------------
    # Art. 16 — Notice & action mechanism (hosting/platform)
    # -------------------------------
    if is_hosting_like:
        ok = _truthy(dsa.get("notice_and_action"))
        results.append(
            _result(
                "DSA:Art16",
                "SATISFIED" if ok else "VIOLATED",
                3 if not ok else 2,
                "Notice & action mechanism is implemented." if ok else
                "Missing explicit signal that a notice & action mechanism is implemented for EU users.",
                {"notice_and_action": bool(ok)},
            )
        )
    else:
        results.append(_result("DSA:Art16", "NOT_APPLICABLE", 1, "Service type does not indicate hosting/platform context."))

    # -------------------------------
    # Art. 17 — Statement of reasons (platform actions)
    # -------------------------------
    if is_platform:
        ok = _truthy(dsa.get("statement_of_reasons"))
        results.append(
            _result(
                "DSA:Art17",
                "SATISFIED" if ok else "VIOLATED",
                3 if not ok else 2,
                "Statement-of-reasons capability exists for moderation/enforcement actions." if ok else
                "Missing explicit signal that statement-of-reasons is produced for moderation/enforcement actions.",
                {"statement_of_reasons": bool(ok)},
            )
        )
    else:
        results.append(_result("DSA:Art17", "NOT_APPLICABLE", 1, "Service type does not indicate an online platform context."))

    # -------------------------------
    # Art. 20 — Internal complaint-handling system (online platforms)
    # -------------------------------
    if is_platform:
        ok = _truthy(dsa.get("complaint_handling"))
        results.append(
            _result(
                "DSA:Art20",
                "SATISFIED" if ok else "VIOLATED",
                3 if not ok else 2,
                "Internal complaint-handling system exists." if ok else
                "Missing explicit signal that internal complaint-handling is implemented for EU users.",
                {"complaint_handling": bool(ok)},
            )
        )
    else:
        results.append(_result("DSA:Art20", "NOT_APPLICABLE", 1, "Service type does not indicate an online platform context."))

    # -------------------------------
    # Art. 22 — Traceability of traders (marketplaces)
    # -------------------------------
    if is_marketplace:
        ok = _truthy(dsa.get("trader_traceability"))
        results.append(
            _result(
                "DSA:Art22",
                "SATISFIED" if ok else "VIOLATED",
                3 if not ok else 2,
                "Trader traceability controls are implemented." if ok else
                "Missing explicit signal that trader traceability controls are implemented.",
                {"trader_traceability": bool(ok)},
            )
        )
    else:
        results.append(_result("DSA:Art22", "NOT_APPLICABLE", 1, "Service type is not a marketplace."))

    # -------------------------------
    # Art. 24 — Transparency reporting (platform/hosting)
    # -------------------------------
    if is_hosting_like:
        ok = _truthy(dsa.get("transparency_reports"))
        results.append(
            _result(
                "DSA:Art24",
                "SATISFIED" if ok else "VIOLATED",
                2 if ok else 2,
                "Transparency reporting is enabled." if ok else
                "Missing explicit signal that transparency reports are produced for EU operations.",
                {"transparency_reports": bool(ok)},
            )
        )
    else:
        results.append(_result("DSA:Art24", "NOT_APPLICABLE", 1, "Service type does not indicate hosting/platform context."))

    # -------------------------------
    # Art. 27 — Recommender transparency (if recommenders used)
    # -------------------------------
    uses_recommenders = _truthy(dsa.get("uses_recommenders"))
    if uses_recommenders:
        ok = _truthy(dsa.get("recommender_disclosure"))
        results.append(
            _result(
                "DSA:Art27",
                "SATISFIED" if ok else "VIOLATED",
                3 if not ok else 2,
                "Recommender system parameters are disclosed." if ok else
                "Missing explicit signal that recommender parameters/disclosure is provided to EU users.",
                {"uses_recommenders": True, "recommender_disclosure": bool(ok)},
            )
        )
    else:
        results.append(
            _result(
                "DSA:Art27",
                "NOT_APPLICABLE",
                1,
                "No recommender usage signal present (or explicitly disabled).",
                {"uses_recommenders": False},
            )
        )

    # -------------------------------
    # VLOP/VLOSE systemic obligations cluster (risk + mitigation + researcher access)
    # -------------------------------
    if is_vlop:
        # Art. 34 — Systemic risk assessment
        ok34 = _truthy(dsa.get("systemic_risk_assessment"))
        results.append(
            _result(
                "DSA:Art34",
                "SATISFIED" if ok34 else "VIOLATED",
                4 if not ok34 else 2,
                "Systemic risk assessment exists." if ok34 else
                "Missing explicit signal that systemic risk assessment is performed and recorded.",
                {"systemic_risk_assessment": bool(ok34)},
            )
        )

        # Art. 35 — Mitigation measures
        ok35 = _truthy(dsa.get("risk_mitigation_measures"))
        results.append(
            _result(
                "DSA:Art35",
                "SATISFIED" if ok35 else "VIOLATED",
                4 if not ok35 else 2,
                "Risk mitigation measures exist and are operationalized." if ok35 else
                "Missing explicit signal that risk mitigation measures are operationalized for systemic risks.",
                {"risk_mitigation_measures": bool(ok35)},
            )
        )

        # Art. 38 — Recommender option not based on profiling (if recommenders used)
        if uses_recommenders:
            ok38 = _truthy(dsa.get("non_profiling_recommender_option"))
            results.append(
                _result(
                    "DSA:Art38",
                    "SATISFIED" if ok38 else "VIOLATED",
                    4 if not ok38 else 2,
                    "Non-profiling recommender option is available." if ok38 else
                    "Missing explicit signal that a non-profiling recommender option is available to users.",
                    {"non_profiling_recommender_option": bool(ok38)},
                )
            )
        else:
            results.append(_result("DSA:Art38", "NOT_APPLICABLE", 1, "No recommender usage signal present."))

        # Art. 39 — Researcher data access (VLOP/VLOSE)
        ok39 = _truthy(dsa.get("researcher_data_access"))
        results.append(
            _result(
                "DSA:Art39",
                "SATISFIED" if ok39 else "VIOLATED",
                4 if not ok39 else 2,
                "Researcher data access capability is enabled." if ok39 else
                "Missing explicit signal that a researcher data-access pathway exists for vetted requests.",
                {"researcher_data_access": bool(ok39)},
            )
        )
    else:
        results.append(_result("DSA:Art34", "NOT_APPLICABLE", 1, "Service is not VLOP/VLOSE."))
        results.append(_result("DSA:Art35", "NOT_APPLICABLE", 1, "Service is not VLOP/VLOSE."))
        results.append(_result("DSA:Art38", "NOT_APPLICABLE", 1, "Service is not VLOP/VLOSE."))
        results.append(_result("DSA:Art39", "NOT_APPLICABLE", 1, "Service is not VLOP/VLOSE."))

    return results
