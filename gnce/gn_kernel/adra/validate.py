# gnce/gn_kernel/adra/validate.py
from typing import Dict, Any

def validate_adra(adra: Dict[str, Any]) -> None:
    if "L7_veto_and_execution_feedback" not in adra:
        raise ValueError("ADRA missing L7 veto layer")
