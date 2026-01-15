# gnce/ui/streaming/kafka_kpi_consumer.py
from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

try:
    from kafka import KafkaConsumer  # kafka-python
except Exception:
    KafkaConsumer = None


@dataclass
class KpiState:
    total_runs: int = 0
    allow_count: int = 0
    deny_count: int = 0
    # optional extras
    violations_total: int = 0
    last_event_ts_utc: Optional[str] = None
    by_regime: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def update_from_event(self, evt: Dict[str, Any]) -> None:
        if not isinstance(evt, dict):
            return

        decision = str(evt.get("decision") or "").upper()
        regime = str(evt.get("regime") or "UNKNOWN")

        self.total_runs += 1

        if decision == "ALLOW":
            self.allow_count += 1
        elif decision == "DENY":
            self.deny_count += 1

        v = evt.get("violations_count")
        if isinstance(v, int):
            self.violations_total += v

        ts = evt.get("ts_utc")
        if isinstance(ts, str) and ts.strip():
            self.last_event_ts_utc = ts.strip()

        # regime slicing
        bucket = self.by_regime.setdefault(regime, {"total": 0, "allow": 0, "deny": 0})
        bucket["total"] += 1
        if decision == "ALLOW":
            bucket["allow"] += 1
        elif decision == "DENY":
            bucket["deny"] += 1


class KafkaKpiConsumer:
    """
    Threaded Kafka consumer that maintains an in-memory KPI state.
    Safe for Streamlit: UI thread only *reads* the snapshot; background thread only *writes* under a lock.
    """

    def __init__(
        self,
        *,
        bootstrap_servers: str,
        topic: str,
        group_id: str,
        enabled: bool = True,
        poll_timeout_ms: int = 500,
        max_records: int = 200,
        auto_offset_reset: str = "latest",
    ) -> None:
        self.enabled = bool(enabled)
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self.poll_timeout_ms = int(poll_timeout_ms)
        self.max_records = int(max_records)
        self.auto_offset_reset = auto_offset_reset

        self._lock = threading.Lock()
        self._state = KpiState()
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

        self._consumer = None

    def start(self) -> None:
        if not self.enabled:
            return
        if KafkaConsumer is None:
            # kafka-python not installed
            self.enabled = False
            return
        if self._thread and self._thread.is_alive():
            return

        self._stop.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        try:
            if self._consumer is not None:
                self._consumer.close()
        except Exception:
            pass

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            s = self._state
            # return a plain dict so Streamlit can store/serialize
            return {
                "total_runs": s.total_runs,
                "allow_count": s.allow_count,
                "deny_count": s.deny_count,
                "violations_total": s.violations_total,
                "last_event_ts_utc": s.last_event_ts_utc,
                "by_regime": dict(s.by_regime),
            }

    def _ensure_consumer(self) -> None:
        if self._consumer is not None:
            return
        self._consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            enable_auto_commit=True,
            auto_offset_reset=self.auto_offset_reset,
            value_deserializer=lambda v: v.decode("utf-8") if isinstance(v, (bytes, bytearray)) else v,
        )

    def _run_loop(self) -> None:
        try:
            self._ensure_consumer()
        except Exception:
            self.enabled = False
            return

        while not self._stop.is_set():
            try:
                records = self._consumer.poll(timeout_ms=self.poll_timeout_ms, max_records=self.max_records)
                if not records:
                    time.sleep(0.05)
                    continue

                for _tp, msgs in records.items():
                    for m in msgs:
                        try:
                            payload = m.value
                            if isinstance(payload, str):
                                evt = json.loads(payload)
                            elif isinstance(payload, dict):
                                evt = payload
                            else:
                                continue
                        except Exception:
                            continue

                        with self._lock:
                            self._state.update_from_event(evt)

            except Exception:
                # don't crash thread; backoff
                time.sleep(0.25)
                continue
