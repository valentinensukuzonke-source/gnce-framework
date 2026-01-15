# gnce/kernel/orchestrator/event_models.py
from pydantic import BaseModel
from typing import Any, Dict
from datetime import datetime

class GNEvent(BaseModel):
    event_id: str
    timestamp: datetime
    source: str
    event_type: str
    payload: Dict[str, Any]


class KernelExecutionEvent(GNEvent):
    input_data: Dict[str, Any]


class ADRAProducedEvent(GNEvent):
    adra: Dict[str, Any]
