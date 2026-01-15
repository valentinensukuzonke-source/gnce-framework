def fraud_band(payload: dict) -> str:
    score = payload.get("risk_indicators", {}).get("fraud_risk_score", 0)

    if score >= 0.9:
        return "HIGH"
    if score >= 0.6:
        return "MEDIUM"
    return "LOW"

def fraud_band(payload: dict) -> str:
    score = payload.get("risk_indicators", {}).get("fraud_risk_score", 0)

    if score >= 0.9:
        return "HIGH"
    if score >= 0.6:
        return "MEDIUM"
    return "LOW"
