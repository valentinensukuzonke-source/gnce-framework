from __future__ import annotations
from typing import Any, Dict, List, Optional

def _status(flag: Optional[bool]) -> str:
    if flag is None:
        return "NOT_APPLICABLE"
    return "COMPLIANT" if flag else "NON_COMPLIANT"

def _emit(
    *,
    section: str,
    title: str,
    requirement: str,
    flag: Optional[bool],
    severity: str,
    evidence: Dict[str, Any],
    remediation: str,
) -> Dict[str, Any]:
    return {
        "regime": "SOX",
        "article": section,
        "title": title,
        "requirement": requirement,
        "status": _status(flag),
        "severity": severity,
        "evidence": evidence,
        "remediation": remediation,
    }

def resolve(payload: Dict[str, Any]) -> Dict[str, Any]:
    profile = payload.get("sox_profile") or {}

    if profile.get("public_company") is False:
        return {"policies_triggered": []}

    # Missing => NOT_APPLICABLE
    management_certification = profile.get("management_certification") if "management_certification" in profile else None
    disclosure_controls      = profile.get("disclosure_controls") if "disclosure_controls" in profile else None
    icfr_effective           = profile.get("icfr_effective") if "icfr_effective" in profile else None
    control_testing          = profile.get("control_testing") if "control_testing" in profile else None
    real_time_disclosure     = profile.get("real_time_disclosure") if "real_time_disclosure" in profile else None


    out: List[Dict[str, Any]] = []

    out.append(_emit(
        section="SOX 302",
        title="Management certification",
        requirement="Management must certify the accuracy of financial reports.",
        flag=management_certification,
        severity="CRITICAL",
        evidence={"sox_profile.management_certification": management_certification},
        remediation="Implement executive certification and sign-off for financial disclosures.",
    ))

    out.append(_emit(
        section="SOX 302",
        title="Disclosure controls",
        requirement="Disclosure controls and procedures must be designed and effective.",
        flag=disclosure_controls,
        severity="HIGH",
        evidence={"sox_profile.disclosure_controls": disclosure_controls},
        remediation="Establish and document disclosure controls with periodic evaluation.",
    ))

    out.append(_emit(
        section="SOX 404",
        title="ICFR effectiveness",
        requirement="Internal controls over financial reporting must be effective.",
        flag=icfr_effective,
        severity="CRITICAL",
        evidence={"sox_profile.icfr_effective": icfr_effective},
        remediation="Design, implement, and remediate ICFR deficiencies.",
    ))

    out.append(_emit(
        section="SOX 404",
        title="Control testing",
        requirement="Internal controls must be tested regularly.",
        flag=control_testing,
        severity="HIGH",
        evidence={"sox_profile.control_testing": control_testing},
        remediation="Perform periodic internal/external control testing with evidence.",
    ))

    out.append(_emit(
    section="SOX 409",
    title="Real-time disclosure",
    requirement="Material changes in financial condition or operations must be disclosed on a rapid and current basis.",
    flag=real_time_disclosure,
    severity="MEDIUM",
    evidence={"sox_profile.real_time_disclosure": real_time_disclosure},
    remediation="Implement a real-time disclosure process: define materiality triggers, ownership, escalation, and timelines for rapid public disclosure.",
))


    return {"policies_triggered": out}
