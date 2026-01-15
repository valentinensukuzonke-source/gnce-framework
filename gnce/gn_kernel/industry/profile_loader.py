"""gnce.gn_kernel.industry.profile_loader

Authoritative customer profile loading.

In GNCE v0.7.x, the industry registry (industry/registry.py) is imported as
Python code and historically contained *execution* fields like enabled_regimes.
Separately, regulator-grade profile JSON files live under gnce/profiles/*.json.

When these two sources drift, the kernel can execute the wrong scope while the
payload claims a different profile hash. This module makes JSON profiles the
authoritative source of truth for execution scope and provides an optional
fail-fast assertion when the registry includes an enabled_regimes list.
"""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional


class ProfileConfigError(RuntimeError):
    """Raised when registry and JSON profiles drift or a profile cannot load."""


@dataclass(frozen=True)
class LoadedProfile:
    """Normalized, authoritative profile data loaded from JSON."""

    profile_id: str
    jurisdiction: str
    enabled_regimes: List[str]
    raw: Dict[str, Any]
    sha256: str
    path: str


def _repo_root_from_this_file(this_file: str) -> Path:
    """Resolve the repository root and/or gnce package root from a module path.

    Callers may pass __file__ from different modules (e.g., kernel.py or this module).
    We therefore locate the nearest parent directory named 'gnce' and return it.
    If it cannot be found, we fall back to a conservative parent-based heuristic.
    """
    p = Path(this_file).resolve()
    for parent in [p.parent, *p.parents]:
        if parent.name == "gnce":
            return parent
    # Fallback: older layout assumption
    return p.parents[2]




def _sha256_bytes(b: bytes) -> str:
    return "sha256:" + hashlib.sha256(b).hexdigest()


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise ProfileConfigError(f"Profile JSON not found: {path}") from e
    except OSError as e:
        raise ProfileConfigError(f"Unable to read profile JSON: {path}") from e
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ProfileConfigError(f"Invalid JSON in profile file: {path}") from e


def _extract_enabled_regimes(obj: Dict[str, Any]) -> List[str]:
    """Support both the new JSON schema (scope.enabled_regimes) and legacy."""
    scope = obj.get("scope") or {}
    regimes = scope.get("enabled_regimes")
    if regimes is None:
        # legacy fallback
        regimes = obj.get("enabled_regimes")
    if regimes is None:
        return []
    if isinstance(regimes, str):
        return [regimes]
    if isinstance(regimes, list):
        return [str(x) for x in regimes if x]
    return []


@lru_cache(maxsize=256)
def load_profile_from_ref(customer_profile_ref: str, *, this_file: str) -> LoadedProfile:
    """Load a profile JSON file using the registry 'customer_profile_ref'.

    The ref is expected to look like: "profiles/fintech_fraud_global.json".
    We resolve it relative to the gnce/ package root.
    """

    if not customer_profile_ref:
        raise ProfileConfigError("Empty customer_profile_ref")

    gnce_root = _repo_root_from_this_file(this_file)
    path = (gnce_root / customer_profile_ref).resolve()
    raw = _read_json(path)
    b = path.read_bytes()
    sha = _sha256_bytes(b)

    profile_id = str(raw.get("profile_id") or "").strip() or "UNKNOWN_PROFILE"
    jurisdiction = str((raw.get("scope") or {}).get("jurisdiction") or raw.get("jurisdiction") or "").strip() or "UNKNOWN"
    enabled_regimes = _extract_enabled_regimes(raw)

    return LoadedProfile(
        profile_id=profile_id,
        jurisdiction=jurisdiction,
        enabled_regimes=enabled_regimes,
        raw=raw,
        sha256=sha,
        path=str(path),
    )


def merge_profile_spec_with_json(
    profile_spec: Dict[str, Any],
    *,
    fail_fast: bool = True,
    this_file: str,
) -> Dict[str, Any]:
    """Return a new profile_spec with JSON as the authority for enabled_regimes.

    Phase 1: fail-fast assertion if registry has enabled_regimes and differs.
    Phase 2: registry can omit enabled_regimes; JSON provides it.
    """

    if not isinstance(profile_spec, dict):
        return profile_spec

    ref = str(profile_spec.get("customer_profile_ref") or "").strip()
    if not ref:
        # Nothing to merge.
        return profile_spec

    loaded = load_profile_from_ref(ref, this_file=this_file)

    # Optional Phase-1 assertion
    registry_regimes = profile_spec.get("enabled_regimes")
    if fail_fast and registry_regimes is not None:
        reg_list: List[str]
        if isinstance(registry_regimes, str):
            reg_list = [registry_regimes]
        elif isinstance(registry_regimes, list):
            reg_list = [str(x) for x in registry_regimes if x]
        else:
            reg_list = []

        if [x.upper() for x in reg_list] != [x.upper() for x in loaded.enabled_regimes]:
            raise ProfileConfigError(
                "Registry/profile JSON drift for "
                f"{profile_spec.get('customer_profile_id') or profile_spec.get('customer_profile_ref')}: "
                f"registry enabled_regimes={reg_list} vs json enabled_regimes={loaded.enabled_regimes}. "
                f"JSON loaded from {loaded.path} ({loaded.sha256})."
            )

    # Merge: JSON is authoritative for execution
    merged = dict(profile_spec)
    merged["enabled_regimes"] = list(loaded.enabled_regimes)
    merged["_profile_json_sha256"] = loaded.sha256
    merged["_profile_json_path"] = loaded.path
    merged["jurisdiction"] = merged.get("jurisdiction") or loaded.jurisdiction
    return merged
