"""
Resolver for SAAS_TRANSACTION_INTEGRITY.

Note: The GNCE kernel executes SaaS TI via the rules evaluator
`evaluate_saas_transaction_integrity_rules`. This resolver exists to satisfy
the regime registry and to support any future dynamic regime execution.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from gnce.gn_kernel.rules.saas_transaction_integrity_rules import (
    evaluate_saas_transaction_integrity_rules,
)


def resolve(payload: Dict[str, Any]) -> Tuple[List[dict], dict]:
    return evaluate_saas_transaction_integrity_rules(payload)
