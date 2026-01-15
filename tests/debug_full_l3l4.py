# debug_full_l3l4.py
import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from gnce.gn_kernel.kernel import (
        _evaluate_policies, 
        _apply_dsa_vlop_gating,
        _run_executable_regimes,
        _filter_policies_by_enabled_regimes
    )
    
    test_payload = {
        "action": "POST_CONTENT",
        "content": "test harmful content",
        "risk_indicators": {"harmful_content_flag": True},
        "industry_id": "SOCIAL_MEDIA", 
        "profile_id": "VLOP_SOCIAL_META",
        "meta": {"is_vlop": True}
    }
    
    enabled_regimes = ['DSA', 'DMA', 'GDPR', 'EU_AI_ACT', 'ISO_42001', 'NIST_AI_RMF']
    
    print("Step 1: _evaluate_policies...")
    policies, rule_summary = _evaluate_policies(test_payload, enabled_regimes=enabled_regimes)
    print(f"  ✓ {len(policies)} policies, summary: {rule_summary}")
    
    print("\nStep 2: _apply_dsa_vlop_gating...")
    policies = _apply_dsa_vlop_gating(policies, test_payload)
    print(f"  ✓ {len(policies)} policies after gating")
    
    print("\nStep 3: _run_executable_regimes...")
    _run_executable_regimes(test_payload, policies, enabled_regimes)
    print(f"  ✓ {len(policies)} policies after registry regimes")
    
    print("\nStep 4: _filter_policies_by_enabled_regimes...")
    policies = _filter_policies_by_enabled_regimes(policies, enabled_regimes)
    print(f"  ✓ {len(policies)} policies after final filter")
    
    print("\n✓ All L3/L4 steps completed successfully!")
    
except Exception as e:
    print(f"ERROR at step: {e}")
    print("\nFull traceback:")
    traceback.print_exc()