from __future__ import annotations
from typing import Dict, Any

# Import the actual engine you already have
from .dda import evaluate_drift as _evaluate_drift

def evaluate_drift(adra: Dict[str, Any]) -> Dict[str, Any]:
    return _evaluate_drift(adra)
