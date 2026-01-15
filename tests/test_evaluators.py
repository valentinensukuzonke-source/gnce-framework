# test_evaluators.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test payload
test_payload = {
    "action": "POST_CONTENT",
    "content": "test harmful content",
    "risk_indicators": {"harmful_content_flag": True},
    "industry_id": "SOCIAL_MEDIA",
    "profile_id": "VLOP_SOCIAL_META"
}

print("Testing each evaluator...")

# Test DSA rules
try:
    from gnce.gn_kernel.rules.dsa_rules import evaluate_dsa_rules
    print("\n1. Testing DSA rules...")
    policies, summary = evaluate_dsa_rules(test_payload)
    print(f"   ✓ DSA: {len(policies)} policies, summary: {summary}")
except Exception as e:
    print(f"   ✗ DSA ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test DMA rules  
try:
    from gnce.gn_kernel.rules.dma_rules import evaluate_dma_rules
    print("\n2. Testing DMA rules...")
    policies, summary = evaluate_dma_rules(test_payload)
    print(f"   ✓ DMA: {len(policies)} policies, summary: {summary}")
except Exception as e:
    print(f"   ✗ DMA ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test GDPR rules (defined in kernel.py)
try:
    from gnce.gn_kernel.kernel import evaluate_gdpr_rules
    print("\n3. Testing GDPR rules...")
    policies, summary = evaluate_gdpr_rules(test_payload)
    print(f"   ✓ GDPR: {len(policies)} policies, summary: {summary}")
except Exception as e:
    print(f"   ✗ GDPR ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test EU AI Act rules
try:
    from gnce.gn_kernel.rules.eu_ai_act_rules import evaluate_eu_ai_act_rules
    print("\n4. Testing EU AI Act rules...")
    policies, summary = evaluate_eu_ai_act_rules(test_payload)
    print(f"   ✓ EU AI Act: {len(policies)} policies, summary: {summary}")
except Exception as e:
    print(f"   ✗ EU AI Act ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50)
print("Testing _apply_dsa_vlop_gating directly...")
try:
    from gnce.gn_kernel.kernel import _apply_dsa_vlop_gating
    test_policies = [{"regime": "DSA", "article": "DSA Art. 34", "status": "VIOLATED"}]
    result = _apply_dsa_vlop_gating(test_policies, test_payload)
    print(f"✓ _apply_dsa_vlop_gating: {len(result)} policies returned")
except Exception as e:
    print(f"✗ _apply_dsa_vlop_gating ERROR: {e}")
    import traceback
    traceback.print_exc()