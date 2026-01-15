# gnce/gn_kernel/federation/federation_gateway.py
from __future__ import annotations

from typing import Any
from .mode_resolver import resolve_mode

from gnce.gn_kernel.guards.immutability import assert_mutable

def emit_adra_if_enabled(adra: dict, fed_cfg: Any, ui_enabled: bool) -> None:
    """
    Sovereign federation gateway (non-blocking).

    A1 requirement:
    - This module MUST be importable even before payload/bundle/sinks exist.
    """
    try:
        cfg_enabled = bool(getattr(fed_cfg, "enabled", False))
        cfg_mode = getattr(fed_cfg, "mode", None)

        effective_enabled = cfg_enabled and bool(ui_enabled)
        mode = resolve_mode(effective_enabled, cfg_mode)

        if mode == "OFF":
            return

        # Lazy imports so A1 can land before A2/A3
        try:
            from .payload_builder import build_payload
            from .bundle_builder import build_bundle
            from .sink_dispatcher import dispatch
        except Exception as exc:
            _record_federation_error(
                RuntimeError(f"Federation modules not yet installed for mode={mode}: {exc}")
            )
            return

        payload = build_payload(adra, mode)
        bundle = build_bundle(payload, adra, mode)
        dispatch(bundle, fed_cfg)

    except Exception as exc:
        _record_federation_error(exc)


def _record_federation_error(exc: Exception) -> None:
    # Minimal non-blocking logging (will be upgraded later)
    print(f"[GNCE:FEDERATION] Non-blocking error: {exc}")
