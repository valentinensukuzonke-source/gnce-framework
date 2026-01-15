# gnce/kernel/orchestrator/event_bus.py
from typing import Callable, Dict, List
from .event_models import GNEvent

class EventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable):
        self.subscribers.setdefault(event_type, []).append(handler)

    def publish(self, event: GNEvent):
        for handler in self.subscribers.get(event.event_type, []):
            handler(event)
