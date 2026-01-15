# gnce/gn_kernel/regimes/finra/applicability.py

def is_applicable(payload: dict) -> bool:
    profile = payload.get("finra_profile") or {}
    return bool(profile.get("broker_dealer"))
