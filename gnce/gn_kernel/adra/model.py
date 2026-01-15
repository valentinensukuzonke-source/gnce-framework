# gnce/gn_kernel/adra/model.py
from typing import Dict, Any, Optional

class ADRA(dict):
    """
    Canonical Audit-Decision-Record Artifact.
    This is the sovereign evidence envelope.
    """

    def get_layer(self, layer_id: str) -> Optional[Dict[str, Any]]:
        return self.get(layer_id)

    def set_layer(self, layer_id: str, payload: Dict[str, Any]) -> None:
        self[layer_id] = payload
