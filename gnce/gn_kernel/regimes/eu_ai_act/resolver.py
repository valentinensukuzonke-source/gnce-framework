# gnce/regimes/eu_ai_act/resolver.py
from __future__ import annotations

from typing import Any, Dict, List


def evaluate_eu_ai_act_controls(ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Canonical results:
      {id, verdict, severity, rationale}

    Production-compatible scaffold:
    - Evaluates only explicit controls/flags in payload
    - Emits NOT_APPLICABLE where evidence is missing (conservative)
    """
    ai = ctx.get("ai") or ctx.get("ai_profile") or {}
    if not isinstance(ai, dict):
        ai = {}

    # Minimal “control surface” you can expand (risk mgmt, data gov, logs, oversight, etc.)
    controls = [
        {
            "id": "EU_AI_ACT:RISK_MANAGEMENT",
            "flag": ai.get("risk_management_process"),
            "severity_if_missing": 4,
            "ok": "Risk management process declared.",
            "bad": "No explicit risk management process provided for AI system.",
        },
        {
            "id": "EU_AI_ACT:DATA_GOVERNANCE",
            "flag": ai.get("data_governance_controls"),
            "severity_if_missing": 3,
            "ok": "Data governance controls declared.",
            "bad": "No explicit data governance controls provided.",
        },
        {
            "id": "EU_AI_ACT:LOGGING_TRACEABILITY",
            "flag": ai.get("logging_and_traceability"),
            "severity_if_missing": 3,
            "ok": "Logging/traceability controls declared.",
            "bad": "No explicit logging/traceability controls provided.",
        },
        {
            "id": "EU_AI_ACT:HUMAN_OVERSIGHT",
            "flag": ai.get("human_oversight_mechanisms"),
            "severity_if_missing": 4,
            "ok": "Human oversight mechanisms declared.",
            "bad": "No explicit human oversight mechanisms provided.",
        },
    ]

    out: List[Dict[str, Any]] = []
    for c in controls:
        flag = c["flag"]
        if flag is True:
            out.append({"id": c["id"], "verdict": "SATISFIED", "severity": 1, "rationale": c["ok"]})
        elif flag is False:
            out.append({"id": c["id"], "verdict": "VIOLATED", "severity": int(c["severity_if_missing"]), "rationale": c["bad"]})
        else:
            out.append(
                {
                    "id": c["id"],
                    "verdict": "NOT_APPLICABLE",
                    "severity": 1,
                    "rationale": "No evidence provided in payload to evaluate this control.",
                }
            )

    return out
