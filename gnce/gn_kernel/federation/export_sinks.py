# gn_kernel/federation/export_sinks.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import json
import hashlib
import datetime as dt

from .config_loader import FederationConfig
from ..redaction import redact_adra_for_regulator

# ------------------------------------------------------
# Payload builder (shared by exporter + UI preview)
# ------------------------------------------------------

def build_federation_payload(
    adra: Dict[str, Any],
    cfg: FederationConfig,
) -> Optional[Dict[str, Any]]:
    """
    Construct the federated payload according to federation mode.

    OFF or disabled  -> returns None (no export)
    HASH_ONLY        -> minimal hash-only payload
    REDACTED         -> regulator-safe ADRA
    FULL             -> full ADRA
    """
    if not isinstance(adra, dict):
        return None

    if not cfg.enabled:
        return None

    mode = (cfg.mode or "OFF").upper()
    if mode == "OFF":
        return None

    adra_id = adra.get("adra_id", "unknown")
    adra_hash = adra.get("adra_hash")

    # Ensure we have a hash even if kernel omitted it
    if not adra_hash:
        try:
            canonical = json.dumps(
                adra, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
            adra_hash = "sha256:" + hashlib.sha256(canonical).hexdigest()
        except Exception:
            adra_hash = ""

    meta = {
        "adra_id": adra_id,
        "adra_hash": adra_hash,
        "GNCE_version": adra.get("GNCE_version"),
        "federated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "mode": mode,
    }

    if mode == "HASH_ONLY":
        return {
            "kind": "GNCE_ADRA_HASH_ONLY",
            "meta": meta,
        }

    if mode == "REDACTED":
        try:
            redacted = redact_adra_for_regulator(adra)
        except Exception:
            redacted = {}
        return {
            "kind": "GNCE_ADRA_REDACTED",
            "meta": meta,
            "adra": redacted,
        }

    # FULL (or anything else) defaults to full ADRA
    return {
        "kind": "GNCE_ADRA_FULL",
        "meta": meta,
        "adra": adra,
    }


# ------------------------------------------------------
# Sink implementations (best-effort, non-fatal)
# ------------------------------------------------------

def _export_to_filesystem(payload: Dict[str, Any], sink_cfg: Dict[str, Any]) -> None:
    directory = Path(sink_cfg.get("directory", "federated_adras"))
    prefix = sink_cfg.get("file_prefix", "federated_adra_")

    directory.mkdir(parents=True, exist_ok=True)

    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    adra_id = (payload.get("meta") or {}).get("adra_id", "unknown")

    filename = f"{prefix}{ts}_{adra_id}.json"
    path = directory / filename

    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def _export_to_s3(payload: Dict[str, Any], sink_cfg: Dict[str, Any]) -> None:
    """
    Optional S3 sink. Requires boto3 and AWS credentials configured.

    If boto3 is not available, this becomes a no-op.
    """
    try:
        import boto3  # type: ignore
    except Exception:
        # Soft failure – operator can install boto3 if needed.
        print("[GNCE federation] boto3 not available; skipping S3 export.")
        return

    bucket = sink_cfg.get("bucket")
    prefix = sink_cfg.get("prefix", "adras/")
    region = sink_cfg.get("region")

    if not bucket:
        return

    s3 = boto3.client("s3", region_name=region) if region else boto3.client("s3")

    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    adra_id = (payload.get("meta") or {}).get("adra_id", "unknown")
    key = f"{prefix}{ts}_{adra_id}.json"

    body = json.dumps(payload).encode("utf-8")
    s3.put_object(Bucket=bucket, Key=key, Body=body, ContentType="application/json")


def _export_to_http_api(payload: Dict[str, Any], sink_cfg: Dict[str, Any]) -> None:
    """
    Optional HTTP API sink. Requires 'requests' library.
    """
    try:
        import requests  # type: ignore
    except Exception:
        print("[GNCE federation] requests not available; skipping HTTP export.")
        return

    url = sink_cfg.get("url")
    if not url:
        return

    method = (sink_cfg.get("method") or "POST").upper()
    headers = sink_cfg.get("headers") or {}
    timeout = sink_cfg.get("timeout_seconds", 5)

    if method == "POST":
        requests.post(url, json=payload, headers=headers, timeout=timeout)
    elif method == "PUT":
        requests.put(url, json=payload, headers=headers, timeout=timeout)
    else:
        # Fallback: still POST if unknown
        requests.post(url, json=payload, headers=headers, timeout=timeout)


# ------------------------------------------------------
# Public entry point
# ------------------------------------------------------

def export_federated_adra(adra: Dict[str, Any], cfg: FederationConfig) -> None:
    """
    Best-effort federated export.

    - No effect if cfg.disabled or mode=OFF
    - Never raises out of this function (safe for UI / kernel callers)
    """
    try:
        payload = build_federation_payload(adra, cfg)
        if payload is None:
            return

        for sink in cfg.sinks:
            if not isinstance(sink, dict):
                continue
            if not sink.get("enabled", False):
                continue

            typ = (sink.get("type") or "").lower()
            try:
                if typ == "filesystem":
                    _export_to_filesystem(payload, sink)
                elif typ == "s3":
                    _export_to_s3(payload, sink)
                elif typ == "api":
                    _export_to_http_api(payload, sink)
                else:
                    print(f"[GNCE federation] Unknown sink type: {typ}")
            except Exception as e:
                print(f"[GNCE federation] Export to sink {sink.get('name')} failed: {e}")

    except Exception as e:
        # Absolute last resort: never break GNCE due to federation.
        print(f"[GNCE federation] Unexpected error in export_federated_adra: {e}")
