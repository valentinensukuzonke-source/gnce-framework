from __future__ import annotations

from typing import Any, Iterable


def _iter_strings(x: Any) -> Iterable[str]:
    """Yield lowercase strings from common container shapes."""
    if x is None:
        return
    if isinstance(x, str):
        yield x.lower()
        return
    if isinstance(x, dict):
        for v in x.values():
            yield from _iter_strings(v)
        return
    if isinstance(x, (list, tuple, set)):
        for v in x:
            yield from _iter_strings(v)
        return


def is_applicable(adra: Any = None, *args: Any, **kwargs: Any) -> bool:
    """
    Conservative PCI DSS applicability.

    Returns True only when the ADRA clearly indicates payment card data
    (PAN / card number / CVV / cardholder data / payment processing).

    Accepts flexible signature so engine changes won't break this.
    """
    if adra is None:
        adra = kwargs.get("adra") or kwargs.get("input") or kwargs.get("context")

    text = " ".join(_iter_strings(adra))

    strong_terms = [
        "pci dss",
        "payment card",
        "cardholder data",
        "pan",
        "primary account number",
        "cvv",
        "cvc",
        "track 1",
        "track 2",
        "card number",
        "credit card",
        "debit card",
        "payment processing",
        "chargeback",
        "merchant id",
        "acquirer",
        "issuer",
    ]

    return any(t in text for t in strong_terms)
