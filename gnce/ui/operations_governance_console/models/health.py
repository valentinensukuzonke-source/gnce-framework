from __future__ import annotations

from typing import Any, Dict, List

# =========================================================
# Sovereign Compliance Thresholds (Regulator-grade)
# =========================================================

# Minimum evidence coverage required for regulator-grade claims
MIN_CONSTITUTION_HASH_COVERAGE = 0.60   # 60%
MIN_TIMESTAMP_COVERAGE = 0.95           # 95%


def _coverage(entries: List[Dict[str, Any]], field: str) -> float:
    """Return fraction of entries with a truthy `field`."""
    if not entries:
        return 0.0
    present = sum(1 for e in entries if e.get(field))
    return present / len(entries)


def governance_health_statement(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Regulator-grade health statement for Block M.

    IMPORTANT:
    - This is read-only evidence summarization. No mutation.
    - DENY rate is computed on adjudicated outcomes only: DENY / (ALLOW + DENY).
      UNKNOWN is treated as evidence incompleteness and excluded from the denominator.
    """
    total = len(entries)

    verdicts = [str(e.get("verdict") or e.get("decision") or "").upper().strip() for e in entries]
    denies = sum(1 for v in verdicts if v == "DENY")
    allows = sum(1 for v in verdicts if v == "ALLOW")
    unknowns = total - (denies + allows)

    adjudicated = denies + allows
    deny_rate = (denies / adjudicated * 100.0) if adjudicated else 0.0

    # Evidence completeness (fractions)
    ts_cov_f = _coverage(entries, "time")  # `time` is the canonical normalized key in Block M
    const_cov_f = _coverage(entries, "constitution_hash")

    ts_cov = ts_cov_f * 100.0
    const_cov = const_cov_f * 100.0

    # Compliance gate (explicit sovereign requirement)
    compliance_pass = (
        const_cov_f >= MIN_CONSTITUTION_HASH_COVERAGE
        and ts_cov_f >= MIN_TIMESTAMP_COVERAGE
    )

    # Simple risk grading (tune later). Compliance gate can only worsen risk.
    risk = "LOW"
    if deny_rate >= 15 or const_cov < 60 or ts_cov < 90:
        risk = "MEDIUM"
    if deny_rate >= 30 or const_cov < 40 or ts_cov < 75:
        risk = "HIGH"

    if not compliance_pass:
        # Missing constitutional evidence is always high risk in a sovereign observatory.
        risk = "HIGH"

    notes: List[str] = []

    if total == 0:
        notes.append("No session evidence observed yet. Run GNCE to populate SARS ledger.")
    else:
        # Gate findings (hard requirements)
        if const_cov_f < MIN_CONSTITUTION_HASH_COVERAGE:
            notes.append(
                f"Constitution hash coverage {const_cov:.1f}% is below required threshold ({int(MIN_CONSTITUTION_HASH_COVERAGE*100)}%)."
            )
        if ts_cov_f < MIN_TIMESTAMP_COVERAGE:
            notes.append(
                f"Timestamp coverage {ts_cov:.1f}% is below required threshold ({int(MIN_TIMESTAMP_COVERAGE*100)}%)."
            )

        # Soft findings (advisory)
        if unknowns > 0:
            notes.append(
                f"{unknowns} entries are UNKNOWN (missing ALLOW/DENY verdict evidence); exclude UNKNOWN from DENY rate denominator."
            )
        if deny_rate >= 15:
            notes.append("Elevated DENY rate detected; review veto and drift loops for root cause.")

    attestation = (
        "This statement is generated from read-only SARS session evidence. "
        "No execution or mutation occurs within Block M.\n\n"
    )
    if compliance_pass:
        attestation += (
            "Compliance status: PASS — constitutional evidence meets minimum coverage thresholds."
        )
    else:
        attestation += (
            "Compliance status: FAIL — constitutional evidence coverage is below minimum sovereign requirements. "
            "Accountability findings are provisional."
        )

    return {
        "risk_band": risk,
        # NOTE: In Block M, `entries` are ADRA-level evidence rows (session ledger).
        # If you want run telemetry, compute that separately from run_events.jsonl and pass it in at the console level.
        "runs_observed": total,
        "allow_count": allows,
        "deny_count": denies,
        "unknown_count": unknowns,
        "deny_rate_pct": round(deny_rate, 1),
        "timestamp_coverage_pct": round(ts_cov, 1),
        "constitution_hash_coverage_pct": round(const_cov, 1),
        "compliance_pass": compliance_pass,
        "attestation": attestation,
        "notes": notes,
    }
