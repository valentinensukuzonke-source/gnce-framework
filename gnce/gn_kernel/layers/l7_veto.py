# gnce/gn_kernel/execution/layers/l7_veto.py

def build_veto_basis(l4_results):
    return [
        {
            "article": r["article"],
            "severity": r["severity"],
            "status": r["status"],
            "constitutional_clause": "GNCE Sec. 1.1 — No HIGH/CRITICAL violation may yield ALLOW.",
            "explanation": f"Article {r['article']} violated with severity {r['severity']}."
        }
        for r in l4_results
        if r["status"] == "VIOLATED" and r["severity"] in ("HIGH", "CRITICAL")
    ]


def apply_l7_veto(veto_basis, constitution):
    veto_triggered = len(veto_basis) > 0

    return {
        "layer": "L7",
        "execution_authorized": not veto_triggered,
        "veto_path_triggered": veto_triggered,
        "veto_category": "CONSTITUTIONAL_BLOCK" if veto_triggered else None,
        "veto_basis": veto_basis,
        "escalation_required": "HUMAN_REVIEWER" if veto_triggered else None,
        "decision_gate": {
            "allow_downstream": not veto_triggered,
            "block_reason": "L7 veto: CONSTITUTIONAL_BLOCK" if veto_triggered else None,
        },
    }
