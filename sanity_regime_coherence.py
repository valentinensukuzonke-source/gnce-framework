"""
Run:  python sanity_regime_coherence.py

This is a no-pytest regression check:
- If any regime has veto_triggered=True (blocking failures), L1 must be DENY
- execution_authorized must be False
""" 
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gnce.gn_kernel.kernel import run_gn_kernel # adjust import if your entrypoint differs


def main() -> None:
    # Use a payload that you know triggers deny_critical_violation.json in your environment.
    payload = {
    "action": "execute",
    "content": "sanity check — force evaluation",
    "user_id": "sanity",
    "risk_indicators": {
        "harmful_content_flag": True,
        "violation_category": "critical_violation",
    }
}


    adras = run_gn_kernel(payload)
    print("ADRAs type:", type(adras), "keys:", list(adras.keys()) if isinstance(adras, dict) else None)

    assert isinstance(adras, dict) and adras, "No ADRAs returned"

    bad = []
    for regime, adra in adras.items():
        l1 = adra.get("L1_the_verdict_and_constitutional_outcome", {}) or {}
        l7 = adra.get("L7_veto_and_execution_feedback", {}) or {}

        decision = str(l1.get("decision_outcome", "")).upper()
        veto = bool(l7.get("veto_triggered", False))
        exec_auth = l7.get("execution_authorized", None)

        if veto:
            if decision != "DENY" or exec_auth is not False:
                bad.append((regime, decision, exec_auth))

    if bad:
        raise SystemExit(f"FAILED coherence: {bad}")

    print("OK: L1↔L7 coherence holds for all vetoed regimes.")


if __name__ == "__main__":
    main()
