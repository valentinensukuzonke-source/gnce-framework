from __future__ import annotations

from typing import Any, Dict, List, Tuple


def dispatch(bundle: bytes, fed_cfg: Any) -> None:
    """
    Dispatch bundle bytes to all configured sinks.

    Non-blocking:
    - Sink errors are recorded and swallowed.
    - No sink failure may break GNCE execution.
    """
    sinks = getattr(fed_cfg, "sinks", None) or []
    if not isinstance(sinks, list) or not sinks:
        return

    mode = (getattr(fed_cfg, "mode", "OFF") or "OFF").upper()
    content_type = _content_type_for_mode(mode)

    for s in sinks:
        try:
            _send_to_sink(s, bundle, content_type)
        except Exception as exc:
            _record_sink_error(exc, s)


def _send_to_sink(sink_cfg: Dict[str, Any], body: bytes, content_type: str) -> None:
    if not isinstance(sink_cfg, dict):
        raise ValueError("Invalid sink config (expected dict)")

    sink_type = str(sink_cfg.get("type") or "").upper().strip()

    if sink_type == "HTTPS":
        from gnce.gn_kernel.federation.sinks.https_sink import build_https_sink
        sink = build_https_sink(sink_cfg)
        sink.send(body, content_type)
        return

    raise ValueError(f"Unsupported sink type: {sink_type}")


def _content_type_for_mode(mode: str) -> str:
    # HASH_ONLY -> JSON bytes
    # REDACTED/FULL -> ZIP bytes
    if mode == "HASH_ONLY":
        return "application/json"
    return "application/zip"


def _record_sink_error(exc: Exception, sink_cfg: Any) -> None:
    # Minimal non-blocking logging (v0.6.2)
    try:
        stype = (sink_cfg.get("type") if isinstance(sink_cfg, dict) else None) or "UNKNOWN"
        endpoint = (sink_cfg.get("endpoint") if isinstance(sink_cfg, dict) else None) or ""
    except Exception:
        stype, endpoint = "UNKNOWN", ""
    print(f"[GNCE:FEDERATION] Sink error type={stype} endpoint={endpoint}: {exc}")
