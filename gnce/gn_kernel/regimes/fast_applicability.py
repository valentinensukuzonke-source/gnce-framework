def get_applicable_regimes_fast(payload: dict) -> list[str]:
    """Fast applicability checking based on simple payload inspection."""
    applicable = []
    
    loc = payload.get("user_location", "").upper()
    
    # EU regimes
    if loc in ["EU", "EEA"] or any(k.startswith("eu_") for k in payload):
        applicable.extend(["DSA", "GDPR", "DMA"])
    
    # US healthcare
    if payload.get("contains_phi") or payload.get("hipaa_entity"):
        applicable.append("HIPAA")
    
    # Financial
    if payload.get("financial_transaction"):
        applicable.extend(["SEC_17A4", "FINRA"])
        if payload.get("sox_entity"):
            applicable.append("SOX")
    
    # Payment
    if payload.get("payment_card_data"):
        applicable.append("PCI_DSS")
    
    # AI-related
    if payload.get("ai_decision"):
        if loc in ["EU", "EEA"]:
            applicable.append("EU_AI_ACT")
        applicable.append("NIST_AI_RMF")
    
    # Banking/AML
    if payload.get("aml_screening"):
        applicable.append("BSA_AML")
    
    # ISO (always check if org uses it)
    if payload.get("iso_42001_entity"):
        applicable.append("ISO_42001")
    
    return applicable