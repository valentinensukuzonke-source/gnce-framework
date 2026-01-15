# gnce/gn_kernel/regimes/nydfs_500/resolver.py
from gnce.gn_kernel.rules.nydfs_500_rules import evaluate_nydfs_500_rules

def resolve(payload: dict) -> dict:
    policies, _ = evaluate_nydfs_500_rules(payload)
    return {"policies_triggered": policies}
