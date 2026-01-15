from __future__ import annotations

"""
GNCE Regime Registry (auto-discovery + backward-compatible register_regime)

Goals:
- Auto-discover all regime packages under `gnce.gn_kernel.regimes.*` and register them.
- Keep REGIME_REGISTRY as the single source of truth for kernel routing.
- Be backward-compatible with older regime register modules that call:
    - register() with no args
    - register(registry) with explicit registry
    - register_regime({"id": "...", ...})
    - register_regime("ID", {...})
    - register_regime(id="ID", ...)   (legacy)
    - register_regime(regime_id="ID", ...) (newer)
"""

from typing import Any, Callable, Dict, List, Optional, Tuple
import importlib
import pkgutil

# Public global registry used by kernel
REGIME_REGISTRY: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------
# Backward-compatible registration helper
# ---------------------------------------------------------------------

def _coalesce_regime_id(spec: Dict[str, Any], kwargs: Dict[str, Any]) -> Optional[str]:
    # Prefer explicit kwargs
    rid = kwargs.get("regime_id") or kwargs.get("id") or kwargs.get("regime")
    if rid:
        return str(rid)
    # Then spec dict
    for k in ("regime_id", "id", "regime"):
        if k in spec and spec[k]:
            return str(spec[k])
    return None

def register_regime(*args, **kwargs) -> None:
    """
    Backward-compatible regime registration helper.

    Supported call shapes:
      1) register_regime(spec_dict)
      2) register_regime(regime_id, spec_dict)
      3) register_regime(**spec_fields)              # regime_id OR id must be included
      4) register_regime(regime_id, **spec_fields)   # legacy style

    Notes:
      - Accepts 'id' as an alias for 'regime_id'.
      - If both args and kwargs provide the same field, kwargs wins.
    """
    spec: Dict[str, Any] = {}

    # --- parse positional forms ---
    if len(args) == 1 and isinstance(args[0], dict):
        spec = dict(args[0])
    elif len(args) == 2 and isinstance(args[1], dict):
        spec = dict(args[1])
        # allow first arg regime id
        spec.setdefault("regime_id", args[0])
    elif len(args) == 1 and isinstance(args[0], str):
        # allow register_regime("EU_AI_ACT", display_name=..., ...)
        spec = {"regime_id": args[0]}
    elif len(args) == 0:
        spec = {}
    else:
        raise TypeError(
            "register_regime() supports: (spec_dict) or (regime_id, spec_dict) or keyword args"
        )

    # --- merge kwargs (kwargs wins) ---
    if kwargs:
        spec.update(kwargs)

    # alias: id -> regime_id
    if "id" in spec and "regime_id" not in spec:
        spec["regime_id"] = spec.pop("id")

    regime_id = str(spec.get("regime_id") or "").strip()
    if not regime_id:
        raise ValueError("register_regime(): missing regime_id / id")

    # Normalize common alias to keep registry coherent
    if regime_id == "AI_ACT":
        regime_id = "EU_AI_ACT"
    spec["regime_id"] = regime_id

    # Required fields for kernel L4/L3
    required = [
        "display_name",
        "domain",
        "framework",
        "regime_type",
        "jurisdiction",
        "enforceable",
        "l4_executable",
        "authority",
        "applicability",
        "resolver",
    ]
    missing = [k for k in required if k not in spec]
    if missing:
        raise ValueError(f"register_regime({regime_id}): missing required fields: {missing}")

    REGIME_REGISTRY[regime_id] = {k: spec[k] for k in ["regime_id", *required]}

def _iter_regime_packages() -> List[str]:
    """
    Discover subpackages under gnce.gn_kernel.regimes
    We include folders that look like regime packages (have __init__.py in real filesystem),
    but we also tolerate namespace packages.
    """
    base_pkg = "gnce.gn_kernel.regimes"
    try:
        base = importlib.import_module(base_pkg)
    except Exception:
        return []

    packages: List[str] = []
    if not hasattr(base, "__path__"):
        return packages

    for mod in pkgutil.iter_modules(base.__path__, base_pkg + "."):
        name = mod.name
        tail = name.split(".")[-1]
        if tail.startswith("_"):
            continue
        if tail in {"tests", "test", "utils"}:
            continue
        # We only want packages (folders). pkgutil gives ispkg flag.
        if mod.ispkg:
            packages.append(name)
    return packages

def _call_register(pkg_name: str, verbose: bool) -> Tuple[bool, Optional[str]]:
    """
    Try to register a regime package.
    Returns (ok, error_message_if_any)
    """
    # Preferred: <pkg>.register.register
    register_fn: Optional[Callable[..., Any]] = None

    try:
        reg_mod = importlib.import_module(pkg_name + ".register")
        register_fn = getattr(reg_mod, "register", None)
    except Exception:
        # Fallback: package-level register
        try:
            pkg = importlib.import_module(pkg_name)
            register_fn = getattr(pkg, "register", None)
        except Exception as e:
            return False, f"import failed: {e!r}"

    if not callable(register_fn):
        return False, "no register() function found"

    # Call with registry if accepted; otherwise call with no args.
    try:
        try:
            register_fn(REGIME_REGISTRY)  # many regimes accept this
        except TypeError:
            register_fn()  # older regimes
        return True, None
    except Exception as e:
        return False, f"register() raised: {e!r}"

def init_registry(force: bool = False, verbose: bool = False) -> None:
    """
    Initialize REGIME_REGISTRY by auto-discovering regime packages.

    - If force=False and registry already populated, it's a no-op.
    - If force=True, clears and re-registers everything.

    Non-fatal behavior:
    - Individual regime registration failures are logged (if verbose) but do not crash init.
      This keeps GNCE boot resilient while you iteratively fix regimes.
    """
    if REGIME_REGISTRY and not force:
        return

    REGIME_REGISTRY.clear()

    pkgs = _iter_regime_packages()
    if verbose:
        print(f"GNCE: discovered regime packages: {pkgs}")

    failed: List[str] = []
    for pkg_name in pkgs:
        ok, err = _call_register(pkg_name, verbose=verbose)
        if not ok:
            failed.append(pkg_name)
            if verbose:
                print(f"GNCE: regime failed to register: {pkg_name} ({err})")

    if verbose and failed:
        print(f"GNCE: some regimes failed to register (non-fatal): {failed}")
