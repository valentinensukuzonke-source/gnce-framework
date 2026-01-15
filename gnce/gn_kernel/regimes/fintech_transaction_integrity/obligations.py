"""gnce.gn_kernel.regimes.fintech_transaction_integrity.obligations

Fintech Transaction Integrity (FTI) obligation catalog.

GNCE v0.7.x expectations:
- Each obligation MUST include at least: domain, regime, article, severity.
- 'regime' must match the profile's enabled_regimes entry: "FINTECH_TRANSACTION_INTEGRITY"
- Resolver may override status / severity at evaluation time, but the catalog should be truthful by default.
"""

from __future__ import annotations

from typing import Dict, List


def obligations() -> List[Dict]:
    """Return the obligation catalog for the FINTECH_TRANSACTION_INTEGRITY regime."""
    return [
        {
            "domain": "Fintech Transaction Integrity",
            "regime": "FINTECH_TRANSACTION_INTEGRITY",
            "framework": "Financial Crime Controls",
            "domain_id": "FINTECH_TRANSACTION_INTEGRITY",
            "article": "FTI:HIGH_RISK_WIRE_TRANSFER",
            "category": "Fraud Prevention",
            "title": "Block high-risk wire transfers",
            "severity": "HIGH",
            "enforcement_scope": "TRANSACTION",
            "remediation": "Block execution; require enhanced due diligence and analyst approval.",
        },
        {
            "domain": "Fintech Transaction Integrity",
            "regime": "FINTECH_TRANSACTION_INTEGRITY",
            "framework": "Financial Crime Controls",
            "domain_id": "FINTECH_TRANSACTION_INTEGRITY",
            "article": "FTI:HIGH_RISK_AML_TRANSFER",
            "category": "AML / KYC",
            "title": "Block AML/KYC high-risk transfers",
            "severity": "HIGH",
            "enforcement_scope": "TRANSACTION",
            "remediation": "Block execution; escalate for AML/KYC review and verification.",
        },
        {
            "domain": "Fintech Transaction Integrity",
            "regime": "FINTECH_TRANSACTION_INTEGRITY",
            "framework": "Financial Crime Controls",
            "domain_id": "FINTECH_TRANSACTION_INTEGRITY",
            "article": "FTI:MEDIUM_RISK_TRANSACTION",
            "category": "Fraud Monitoring",
            "title": "Review medium-risk transactions",
            "severity": "MEDIUM",
            "enforcement_scope": "TRANSACTION",
            "remediation": "Allow with review; queue for analyst triage and monitoring.",
        },
    ]
