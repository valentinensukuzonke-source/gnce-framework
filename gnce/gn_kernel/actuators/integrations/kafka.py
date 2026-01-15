# gnce/gn_kernel/integrations/kafka.py
from __future__ import annotations

import json
from typing import Optional, Dict, Any


class KafkaPublisher:
    """
    Optional Kafka publisher.
    - If kafka-python isn't installed, this class fails gracefully.
    """
    def __init__(self, bootstrap_servers: str, topic: str, client_id: str = "gnce"):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.client_id = client_id
        self._producer = None

        try:
            from kafka import KafkaProducer  # type: ignore
            self._producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=self.client_id,
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
                key_serializer=lambda k: str(k).encode("utf-8") if k is not None else None,
                linger_ms=10,
            )
        except Exception:
            self._producer = None

    @property
    def enabled(self) -> bool:
        return self._producer is not None

    def publish(self, event: Dict[str, Any], key: Optional[str] = None) -> bool:
        if not self._producer:
            return False
        try:
            self._producer.send(self.topic, value=event, key=key)
            return True
        except Exception:
            return False

    def flush(self) -> None:
        if self._producer:
            try:
                self._producer.flush(timeout=2)
            except Exception:
                pass
