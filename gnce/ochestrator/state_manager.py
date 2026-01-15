# gnce/kernel/orchestrator/state_manager.py
from typing import Dict, Any

class StateManager:
    def __init__(self):
        self.total_runs = 0
        self.last_adra = None
        self.last_decision = None
        self.metrics = {
            "LOW": 0,
            "MEDIUM": 0,
            "HIGH": 0,
            "CRITICAL": 0,
        }

    def update_from_adra(self, adra: Dict[str, Any]):
        self.total_runs += 1
        self.last_adra = adra

        sev = str(adra.get("L1_the_verdict_and_constitutional_outcome", {}).get("severity", "")).upper()
        if sev in self.metrics:
            self.metrics[sev] += 1

        self.last_decision = adra.get("L1_the_verdict_and_constitutional_outcome", {}).get("decision_outcome")
