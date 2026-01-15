# gnce/gn_kernel/regimes/nydfs_500/applicability.py
def is_applicable(payload: dict) -> bool:
    meta = payload.get("meta") or {}
    juris = str(meta.get("jurisdiction", "")).upper()

    # NYDFS only applies in NY (or explicitly US if you choose)
    if not (juris == "US-NY" or juris == "US"):
        return False

    return bool(payload.get("nydfs_profile"))
