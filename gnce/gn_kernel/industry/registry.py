"""
GNCE industry registry.

This file defines supported industry_id values and their available customer profiles.
Profiles here are lightweight pointers used for UI + routing; full regulator-grade
profile JSON lives under gnce/profiles/*.json.

NOTE: Keep this registry additive/backwards-compatible.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Industry Registry
# ---------------------------------------------------------------------------

INDUSTRY_REGISTRY = {
    # -----------------------------------------------------------------------
    # SOCIAL MEDIA (existing)
    # -----------------------------------------------------------------------
    "SOCIAL_MEDIA": {
        "title": "Social Media / UGC Platform",
        "description": "User-generated content platform; DSA/DMA obligations may apply (EU).",
        "default_profile_id": "VLOP_SOCIAL_META",
        "profiles": {
            # Existing profile (keep keys unchanged; add optional fields safely)
            "VLOP_SOCIAL_META": {
                "title": "EU VLOP Social Platform (DSA/DMA baseline)",
                "jurisdiction": "EU",
                "customer_profile_id": "VLOP_SOCIAL_META",
                # Optional: relative reference used in request payloads (safe for sharing)
                "customer_profile_ref": "profiles/meta_vlop_eu.json",
                "enabled_regimes": ['DSA', 'DMA', 'GDPR', 'EU_AI_ACT'],
                # NOTE (v0.7.2+): Execution scope is loaded from the JSON profile at
                # customer_profile_ref. Keep registry routing-only to avoid drift.
            },
        },
    },

    # -----------------------------------------------------------------------
    # E-COMMERCE / MARKETPLACE
    # -----------------------------------------------------------------------
    "ECOMMERCE": {
        "title": "E-commerce / Marketplace",
        "description": "Online marketplace / retail platform (trust, safety, payments, ads).",
        "default_profile_id": "ECOMMERCE_MARKETPLACE_EU",
        "profiles": {
            "ECOMMERCE_MARKETPLACE_EU": {
                "title": "EU Marketplace (DSA baseline + AI governance)",
                "jurisdiction": "EU",
                "customer_profile_id": "ECOMMERCE_MARKETPLACE_EU",
                "customer_profile_ref": "profiles/ecommerce_marketplace_eu.json",
                "enabled_regimes": ['DSA', 'GDPR', 'EU_AI_ACT'],
                # Execution scope is loaded from JSON profile.
            },
            "ECOMMERCE_RETAIL_GLOBAL": {
                "title": "Global Retail (AI governance baseline)",
                "jurisdiction": "GLOBAL",
                "customer_profile_id": "ECOMMERCE_RETAIL_GLOBAL",
                "customer_profile_ref": "profiles/ecommerce_retail_global.json",
                "enabled_regimes": ['ISO_42001', 'NIST_AI_RMF'],
                # Execution scope is loaded from JSON profile.
            },
        },
    },

    # -----------------------------------------------------------------------
    # FINTECH / PAYMENTS
    # -----------------------------------------------------------------------
    "FINTECH": {
        "title": "FinTech / Payments",
        "description": "Payments, lending, fraud detection, and risk decisioning platforms.",
        "default_profile_id": "FINTECH_PAYMENTS_EU",
        "profiles": {
            "FINTECH_PAYMENTS_EU": {
                "title": "EU Payments (AI risk + governance baseline)",
                "jurisdiction": "EU",
                "customer_profile_id": "FINTECH_PAYMENTS_EU",
                "customer_profile_ref": "profiles/fintech_payments_eu.json",
                "enabled_regimes": ['EU_AI_ACT', 'GDPR', 'ISO_42001', 'NIST_AI_RMF'],
                # Execution scope is loaded from JSON profile.
            },
            "FINTECH_FRAUD_GLOBAL": {
                "title": "Fraud & Risk (Global baseline)",
                "jurisdiction": "GLOBAL",
                "customer_profile_id": "FINTECH_FRAUD_GLOBAL",
                "customer_profile_ref": "profiles/fintech_fraud_global.json",
                "enabled_regimes": ['ISO_42001', 'NIST_AI_RMF'],
                # Execution scope is loaded from JSON profile.
            },
        },
    },

    # -----------------------------------------------------------------------
    # HEALTHCARE
    # -----------------------------------------------------------------------
    "HEALTHCARE": {
        "title": "Healthcare / HealthTech",
        "description": "Clinical workflows, patient services, and medical decision support.",
        "default_profile_id": "HEALTHCARE_PROVIDER_US",
        "profiles": {
            "HEALTHCARE_PROVIDER_US": {
                "title": "US Healthcare Provider (AI governance baseline)",
                "jurisdiction": "US",
                "customer_profile_id": "HEALTHCARE_PROVIDER_US",
                "customer_profile_ref": "profiles/healthcare_provider_us.json",
                "enabled_regimes": ['ISO_42001', 'NIST_AI_RMF'],
                # Execution scope is loaded from JSON profile.
            },
            "HEALTHCARE_PROVIDER_EU": {
                "title": "EU Healthcare Provider (AI Act alignment baseline)",
                "jurisdiction": "EU",
                "customer_profile_id": "HEALTHCARE_PROVIDER_EU",
                "customer_profile_ref": "profiles/healthcare_provider_eu.json",
                "enabled_regimes": ['EU_AI_ACT', 'GDPR', 'ISO_42001', 'NIST_AI_RMF'],
                # Execution scope is loaded from JSON profile.
            },
        },
    },

    # -----------------------------------------------------------------------
    # B2B SAAS / ENTERPRISE SOFTWARE
    # -----------------------------------------------------------------------
    "SAAS_B2B": {
        "title": "B2B SaaS / Enterprise Software",
        "description": "Enterprise SaaS products with auditability, logging, and compliance needs.",
        "default_profile_id": "SAAS_ENTERPRISE_GLOBAL",
        "profiles": {
            "SAAS_ENTERPRISE_GLOBAL": {
                "title": "Enterprise SaaS (global baseline)",
                "jurisdiction": "GLOBAL",
                "customer_profile_id": "SAAS_ENTERPRISE_GLOBAL",
                "customer_profile_ref": "profiles/saas_enterprise_global.json",
                "enabled_regimes": ['ISO_42001', 'NIST_AI_RMF'],
                # Execution scope is loaded from JSON profile.
            },
            "SAAS_PUBLIC_SECTOR_EU": {
                "title": "Public Sector SaaS (EU baseline)",
                "jurisdiction": "EU",
                "customer_profile_id": "SAAS_PUBLIC_SECTOR_EU",
                "customer_profile_ref": "profiles/saas_public_sector_eu.json",
                "enabled_regimes": ['EU_AI_ACT', 'GDPR', 'ISO_42001', 'NIST_AI_RMF'],
                # Execution scope is loaded from JSON profile.
            },
        },
    },
}
