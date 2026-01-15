from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import requests


@dataclass(frozen=True)
class HTTPSSink:
    """
    Minimal HTTPS sink.

    Expects sink config keys:
      - type: "HTTPS"
      - endpoint: URL
      - headers: optional dict
      - timeout_seconds: optional int (default 10)
    """
    endpoint: str
    headers: Dict[str, str]
    timeout_seconds: int = 10

    def send(self, body: bytes, content_type: str) -> None:
        resp = requests.post(
            self.endpoint,
            data=body,
            headers={**self.headers, "Content-Type": content_type},
            timeout=self.timeout_seconds,
        )
        # Hard fail at sink level (caught by dispatcher)
        if resp.status_code >= 400:
            raise RuntimeError(
                f"HTTPS sink failed: {resp.status_code} {resp.text[:200]}"
            )


def build_https_sink(sink_cfg: Dict[str, Any]) -> HTTPSSink:
    endpoint = str(sink_cfg.get("endpoint") or "").strip()
    if not endpoint:
        raise ValueError("HTTPS sink missing required field: endpoint")

    headers = sink_cfg.get("headers") or {}
    if not isinstance(headers, dict):
        headers = {}

    timeout = sink_cfg.get("timeout_seconds", 10)
    try:
        timeout = int(timeout)
    except Exception:
        timeout = 10

    return HTTPSSink(endpoint=endpoint, headers=headers, timeout_seconds=timeout)
