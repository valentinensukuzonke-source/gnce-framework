# gn_kernel/federation/config_loader.py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List
import json


@dataclass
class FederationConfig:
    enabled: bool = False
    mode: str = "OFF"  # OFF | HASH_ONLY | REDACTED | FULL
    sinks: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FederationConfig":
        if not isinstance(data, dict):
            data = {}
        return cls(
            enabled=bool(data.get("enabled", False)),
            mode=str(data.get("mode", "OFF")).upper(),
            sinks=list(data.get("sinks", []) or []),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "mode": self.mode,
            "sinks": self.sinks,
        }


def load_federation_config(path: Path | str) -> FederationConfig:
    """
    Load federation_config.json from disk.
    If missing or invalid, return a safe OFF config.
    """
    p = Path(path)
    if not p.exists():
        return FederationConfig()

    try:
        with p.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return FederationConfig()

    return FederationConfig.from_dict(raw)
