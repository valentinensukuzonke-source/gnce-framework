# gnce/gn_kernel/constitution/gnce_jurisdiction_router.py
"""
GNCE jurisdiction + industry regime router (future-proof, additive).

What this router does:
- Normalizes common jurisdiction/industry inputs (case/spacing/aliases).
- Adds regimes ONLY from the GNCE regime registry (avoid "UNSUPPORTED" surfaces).
- Uses *jurisdiction* to select legal frameworks (e.g., EU -> DSA/DMA/GDPR/EU_AI_ACT).
- Uses *industry* to select integrity regimes (e.g., FINTECH -> FINTECH_TRANSACTION_INTEGRITY).
- Uses payload feature flags to optionally add regimes (PCI/HIPAA/FINRA/SEC_17A4/SOX).

Important:
- This router is optional if you already route via INDUSTRY_REGISTRY profiles.
- If you do use it, prefer using it to *suggest* scope, then intersect with profile scope.
"""

from __future__ import annotations

from typing import Any, Dict, List, Set


# ------------------------------------------------------------
# Canonical helpers
# ------------------------------------------------------------

def _canon(x: Any) -> str:
    return str(x or "").strip().upper().replace(" ", "_").replace("-", "_")


# Aliases -> canonical IDs used in kernel / regime registry.
# Keep this mapping additive.
REGIME_ALIASES: Dict[str, str] = {
    "EU_DSA": "DSA",
    "EU_DMA": "DMA",
    "EU_GDPR": "GDPR",
    "AI_ACT": "EU_AI_ACT",
    "EU_AI_ACT": "EU_AI_ACT",
    "ISO_IEC_42001": "ISO_42001",
    "ISO/IEC_42001": "ISO_42001",
    "NIST_AI_RMF": "NIST_AI_RMF",
    "SEC_17A4": "SEC_17A4",
    "SEC_17A-4": "SEC_17A4",
}

# Jurisdiction aliases -> canonical buckets
JURIS_ALIASES: Dict[str, str] = {
    "EUROPEAN_UNION": "EU",
    "EUROPE": "EU",
    "UNITED_STATES": "US",
    "USA": "US",
    "UNITED_KINGDOM": "UK",
    "GREAT_BRITAIN": "UK",
    "BRITAIN": "UK",
    "WORLDWIDE": "GLOBAL",
    "INTL": "GLOBAL",
    "INTERNATIONAL": "GLOBAL",
    "ALL": "GLOBAL",
}


# These are the regimes we know are registered in your repo (see regimes/register.py).
# Keeping this list local makes the router safe: it won't emit unknown regime IDs.
KNOWN_REGIMES: Set[str] = {
    "DSA",
    "DMA",
    "GDPR",
    "EU_AI_ACT",
    "ISO_42001",
    "NIST_AI_RMF",
    "HIPAA",
    "GLBA",
    "BSA_AML",
    "PCI_DSS",
    "SOX",
    "SEC_17A4",
    "FINRA",
    "NYDFS_500",
    "ECOMMERCE_TRANSACTION_INTEGRITY",
    "FINTECH_TRANSACTION_INTEGRITY",
    "SAAS_TRANSACTION_INTEGRITY",
}


def _canon_regime(r: Any) -> str:
    c = _canon(r)
    return REGIME_ALIASES.get(c, c)


def _canon_jurisdiction(j: Any) -> str:
    c = _canon(j)
    return JURIS_ALIASES.get(c, c)


def _add(regimes: List[str], seen: Set[str], *items: str) -> None:
    for it in items:
        rid = _canon_regime(it)
        if rid and rid in KNOWN_REGIMES and rid not in seen:
            seen.add(rid)
            regimes.append(rid)


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

def route_regimes(payload: dict) -> List[str]:
    """
    Return an ordered list of regime IDs for this payload.

    Ordering principle:
      (1) Jurisdiction "hard law" first (DSA/DMA/GDPR/EU_AI_ACT, HIPAA)
      (2) Cross-jurisdiction governance baselines (ISO_42001, NIST_AI_RMF)
      (3) Industry transaction-integrity regimes (FINTECH/ECOMMERCE)
      (4) Feature-flag add-ons (PCI/SOX/SEC_17A4/FINRA/NYDFS_500/etc.)

    The list is de-duped and stable.
    """
    payload = payload or {}
    meta = payload.get("meta") or {}

    jurisdiction = _canon_jurisdiction(meta.get("jurisdiction"))
    industry = _canon(payload.get("industry_id"))

    regimes: List[str] = []
    seen: Set[str] = set()

    # -----------------------
    # Jurisdiction frameworks
    # -----------------------
    # EU: platform + privacy + AI Act alignment
    if jurisdiction == "EU":
        _add(regimes, seen, "DSA", "DMA", "GDPR", "EU_AI_ACT")

    # UK: we don't have UK-specific regimes in this repo; GDPR is the closest surface.
    # (If you later add "UK_GDPR" etc., update KNOWN_REGIMES + this mapping.)
    elif jurisdiction == "UK":
        _add(regimes, seen, "GDPR", "EU_AI_ACT")

    # US: HIPAA is the most common sector regime we actually have registered
    elif jurisdiction == "US":
        _add(regimes, seen, "HIPAA")

    # GLOBAL/other: keep jurisdiction-specific adds minimal to avoid wrong-law claims.
    # (Governance baselines handled below.)

    # -------------------------------------------
    # Cross-jurisdiction governance baselines
    # -------------------------------------------
    # These are standards/frameworks and can be used as "baseline surfaces".
    _add(regimes, seen, "ISO_42001", "NIST_AI_RMF")

    # -----------------------
    # Industry integrity regs
    # -----------------------
    # Social / UGC platforms: only EU has DSA/DMA in this repo; ISO/NIST already added.
    if industry in {"SOCIAL_MEDIA", "UGC", "PLATFORM"}:
        # No extra beyond jurisdiction + baselines for now.
        pass

    # FinTech / payments / lending / fraud
    if industry in {"FINTECH", "PAYMENTS", "BANKING", "LENDING"}:
        _add(regimes, seen, "FINTECH_TRANSACTION_INTEGRITY", "BSA_AML", "GLBA")
        if jurisdiction == "US":
            # NYDFS applies to NY; we keep it as a surface when US jurisdiction is requested.
            _add(regimes, seen, "NYDFS_500", "FINRA", "SEC_17A4")

    # E-commerce / marketplace / retail
    if industry in {"ECOMMERCE", "MARKETPLACE", "RETAIL"}:
        _add(regimes, seen, "ECOMMERCE_TRANSACTION_INTEGRITY")
        # EU marketplaces already get DSA/GDPR above via jurisdiction.

    # Healthcare / healthtech
    if industry in {"HEALTHCARE", "HEALTHTECH", "MEDICAL"}:
        if jurisdiction == "US":
            _add(regimes, seen, "HIPAA")
        if jurisdiction in {"EU", "UK"}:
            _add(regimes, seen, "GDPR")
        # NOTE: If you introduce a dedicated HEALTHCARE_TRANSACTION_INTEGRITY regime,
        # add it to KNOWN_REGIMES and wire it here.

    # B2B SaaS / enterprise software
    if industry in {"SAAS_B2B", "SAAS", "B2B_SAAS", "ENTERPRISE_SOFTWARE"}:
        _add(regimes, seen, "SAAS_TRANSACTION_INTEGRITY")

    # -----------------------
    # Payload feature flags
    # -----------------------
    # These flags let callers request additional regimes without changing industry/profile.

    # PCI surface: if the payload indicates payment card data or PCI profile, surface PCI DSS
    if payload.get("pci_profile") or payload.get("data_types"):
        _add(regimes, seen, "PCI_DSS")

    # HIPAA surface: explicit hipaa profile hint
    if payload.get("hipaa_profile"):
        _add(regimes, seen, "HIPAA")

    # FINRA surface
    if payload.get("finra_profile"):
        _add(regimes, seen, "FINRA")

    # SEC 17a-4 surface
    if payload.get("sec_17a4_profile"):
        _add(regimes, seen, "SEC_17A4")

    # SOX surface
    if payload.get("sox_profile"):
        _add(regimes, seen, "SOX")

    # If the payload explicitly indicates financial crime controls (common in fintech)
    if payload.get("aml_profile") or payload.get("bsa_aml_profile"):
        _add(regimes, seen, "BSA_AML")

    # If the payload explicitly indicates consumer finance privacy (GLBA)
    if payload.get("glba_profile"):
        _add(regimes, seen, "GLBA")

    return regimes
