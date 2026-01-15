# gnce/kernel/gn_dsl_compiler.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import json

# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]
CONSTITUTION_DIR = BASE_DIR / "constitution"
GN_DSL_PATH = CONSTITUTION_DIR / "gn_constitution.gn.py"
COMPILED_JSON_PATH = CONSTITUTION_DIR / "compiled_constitution.json"


# -------------------------------------------------------------------
# Public helpers exposed to the GN-DSL file
# -------------------------------------------------------------------

def load_constitution() -> Dict[str, Any]:
    """
    Helper for gn_constitution.gn.py to bootstrap from an existing
    compiled constitution (if any).

    Safe to call inside the DSL file:

        from .gn_dsl_compiler import load_constitution, build_domain_catalog
        prev = load_constitution()  # {} if nothing yet

    Returns an empty dict if no compiled JSON exists or it cannot be read.
    """
    if COMPILED_JSON_PATH.exists():
        try:
            text = COMPILED_JSON_PATH.read_text(encoding="utf-8")
            return json.loads(text)
        except Exception:
            return {}
    return {}


def build_domain_catalog(regimes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convenience helper for the GN-DSL file to normalise the
    constitutional catalog into the canonical JSON shape.

    Typical GN-DSL usage:

        from .gn_dsl_compiler import load_constitution, build_domain_catalog

        prev = load_constitution()  # optional

        CONSTITUTION = build_domain_catalog(
            regimes=[
                {
                    "id": "DSA",
                    "label": "EU Digital Services Act (DSA)",
                    "articles": [
                        {
                            "id": "DSA_34",
                            "article": "Art. 34",
                            "title": "Risk assessment",
                            "severity_default": "HIGH",
                            "tags": ["systemic_risk"],
                            "status": "ENABLED",
                        },
                        # ...
                    ],
                },
                # ...
            ]
        )
    """
    return {
        "version": "0.5",
        "regimes": regimes,
    }


# -------------------------------------------------------------------
# Internal loader
# -------------------------------------------------------------------

def _load_gn_dsl_source() -> str:
    if not GN_DSL_PATH.exists():
        raise FileNotFoundError(f"GN-DSL file not found: {GN_DSL_PATH}")
    return GN_DSL_PATH.read_text(encoding="utf-8")


# -------------------------------------------------------------------
# Main entry: compile GN-DSL → JSON constitution
# -------------------------------------------------------------------

def compile_constitution() -> Dict[str, Any]:
    """
    Execute `constitution/gn_constitution.gn.py` in an isolated namespace
    and return the resulting `CONSTITUTION` object (dict).

    The DSL file can rely on:
      - load_constitution()
      - build_domain_catalog()

    and MUST define a top-level variable:

      CONSTITUTION: dict
    """
    code = _load_gn_dsl_source()

    # Namespace given to the GN-DSL file
    ns: Dict[str, Any] = {}

    # Run GN-DSL file. It can import load_constitution/build_domain_catalog
    # from gnce.gn_kernel.gn_dsl_compiler (this module), which are already defined.
    exec(compile(code, str(GN_DSL_PATH), "exec"), ns)  # type: ignore[arg-type]

    constitution = ns.get("CONSTITUTION")
    if not isinstance(constitution, dict):
        raise ValueError(
            "GN-DSL file must define a top-level dict named CONSTITUTION."
        )

    # Persist to JSON for the catalog loader
    try:
        COMPILED_JSON_PATH.write_text(
            json.dumps(constitution, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    except Exception:
        # Non-fatal if disk write fails in lab mode
        pass

    return constitution
