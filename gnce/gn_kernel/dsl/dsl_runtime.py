# gn_kernel/dsl_runtime.py
from __future__ import annotations

from typing import Any, Dict, List, Optional


# ============================================================
#  Core helpers
# ============================================================

def _get_nested(obj: Any, path: List[str]) -> Any:
    """
    Safely get a nested value: ["risk_indicators", "harmful_content_flag"]
    Returns None if any step is missing.
    """
    cur = obj
    for key in path:
        if not isinstance(cur, dict):
            return None
        if key not in cur:
            return None
        cur = cur[key]
    return cur


def _to_number(val: Any) -> Optional[float]:
    try:
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str) and val.strip():
            return float(val)
    except (TypeError, ValueError):
        return None
    return None


# ============================================================
#  Leaf condition evaluation
# ============================================================

def _eval_leaf_condition(
    cond: Dict[str, Any],
    payload: Dict[str, Any],
    policies_context: Optional[List[Dict[str, Any]]] = None,
    policy_row: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Evaluate a single leaf condition.

    Fields:
      - source: "input" | "policy" (default "input")
      - path:   ["risk_indicators", "harmful_content_flag"]
      - op:     "==", "!=", ">", ">=", "<", "<=", "in", "not_in", "missing", "empty"
      - value:  (optional, depends on op)

    For v0.5 we mostly use source="input".
    Meta-rules (scope: "policies") can use source="policy" later.
    """
    source = (cond.get("source") or "input").lower()
    path = cond.get("path") or []
    op = (cond.get("op") or "==").lower()
    value = cond.get("value", None)

    if source == "input":
        base = payload
    elif source == "policy":
        base = policy_row or {}
    else:
        base = payload  # fallback

    current = _get_nested(base, path) if path else base

    # --- null-ish ops: missing / empty ---
    if op == "missing":
        # If we couldn't resolve the path at all, treat as missing
        return current is None
    if op == "empty":
        if current is None:
            return True
        if isinstance(current, str) and current.strip() == "":
            return True
        if isinstance(current, (list, dict)) and len(current) == 0:
            return True
        return False

    # --- normal comparison ops ---
    if op in {"==", "!=", ">", ">=", "<", "<="}:
        # Try numeric comparison first, then fall back to raw
        n_current = _to_number(current)
        n_value = _to_number(value)

        if n_current is not None and n_value is not None:
            a, b = n_current, n_value
        else:
            a, b = current, value

        if op == "==":
            return a == b
        if op == "!=":
            return a != b
        if op == ">":
            return a > b
        if op == ">=":
            return a >= b
        if op == "<":
            return a < b
        if op == "<=":
            return a <= b

    # --- membership ops ---
    if op == "in":
        try:
            return current in value
        except TypeError:
            # value is not iterable
            return False

    if op == "not_in":
        try:
            return current not in value
        except TypeError:
            return True

    # Fallback: unknown op → False (safe)
    return False


# ============================================================
#  Composite condition evaluation (when {...})
# ============================================================

def _eval_condition_node(
    node: Dict[str, Any],
    payload: Dict[str, Any],
    policies_context: Optional[List[Dict[str, Any]]] = None,
) -> bool:
    """
    Evaluate a condition tree like:

      {
        "op": "all",
        "conditions": [ {...}, {...} ]
      }

    Supported:
      - op: "all" / "any"  with "conditions": [...]
      - leaf conditions: see _eval_leaf_condition
      - optional "scope": "policies" for meta-rules (v0.5 minimal support)
    """
    if not isinstance(node, dict):
        return False

    op = (node.get("op") or "all").lower()
    conditions = node.get("conditions") or []
    scope = (node.get("scope") or "input").lower()

    # No conditions → treat as True (neutral)
    if not conditions:
        return True

    # --------------------------------------------------------
    #  Normal path: scope = "input"
    # --------------------------------------------------------
    if scope != "policies":
        results: List[bool] = []
        for c in conditions:
            if "conditions" in (c or {}):
                # nested group
                results.append(_eval_condition_node(c, payload, policies_context))
            else:
                results.append(
                    _eval_leaf_condition(c, payload, policies_context, None)
                )

        if op == "all":
            return all(results)
        if op == "any":
            return any(results)
        # Unknown op → be safe: require all
        return all(results)

    # --------------------------------------------------------
    #  Meta rules: scope = "policies"
    #  iterate over policies_context and see if ANY policy-row
    #  satisfies the leaf conditions (with source="policy").
    # --------------------------------------------------------
    if not policies_context:
        return False

    # For meta-rules, we interpret as:
    #   "any policy row that makes (all/any) conditions true"
    for policy_row in policies_context:
        row_results: List[bool] = []
        for c in conditions:
            if "conditions" in (c or {}):
                # nested groups for policies are rare; keep simple:
                row_results.append(
                    _eval_condition_node(c, payload, policies_context)
                )
            else:
                row_results.append(
                    _eval_leaf_condition(c, payload, policies_context, policy_row)
                )

        if op == "all" and all(row_results):
            return True
        if op == "any" and any(row_results):
            return True

    return False


# ============================================================
#  Public API
# ============================================================

def rule_matches(
    rule: Dict[str, Any],
    payload: Dict[str, Any],
    policies_context: Optional[List[Dict[str, Any]]] = None,
) -> bool:
    """
    Return True if the rule's `when` condition holds for this payload.
    """
    when = rule.get("when")
    if not isinstance(when, dict):
        # no condition → applies unconditionally
        return True

    return _eval_condition_node(when, payload, policies_context)
