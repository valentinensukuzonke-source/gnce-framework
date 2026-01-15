# clean_diagnostic.py
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("="*80)
print("CLEAN DIAGNOSTIC - Why is harmful content being ALLOWED?")
print("="*80)

# 1. First, test if we can import the kernel at all
try:
    from gnce.gn_kernel.kernel import run_gn_kernel_safe
    print("✅ Kernel imports successfully")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# 2. Create a simple test case
test_payload = {
    "action": "POST_CONTENT",
    "content": "Test harmful content about violence",
    "risk_indicators": {
        "harmful_content_flag": True,
        "violation_category": "extremism"
    },
    "industry_id": "SOCIAL_MEDIA",
    "profile_id": "VLOP_SOCIAL_META"
}

print(f"\nTest payload created:")
print(f"  - Action: {test_payload['action']}")
print(f"  - Harmful flag: {test_payload['risk_indicators']['harmful_content_flag']}")
print(f"  - Industry: {test_payload['industry_id']}")
print(f"  - Profile: {test_payload['profile_id']}")

# 3. Run kernel in SAFE mode (catches errors)
print("\n" + "-"*80)
print("Running kernel (safe mode)...")
result = run_gn_kernel_safe(test_payload)

# 4. Analyze result
print("\n" + "="*80)
print("RESULT ANALYSIS:")
print("="*80)

if result.get("error"):
    print(f"❌ Kernel returned error: {result.get('error_message')}")
    print(f"   Issues: {result.get('validation_issues', [])}")
else:
    # Get decision
    l1 = result.get("L1_the_verdict_and_constitutional_outcome", {})
    decision = l1.get("decision_outcome", "UNKNOWN")
    
    # Get policy count
    l4 = result.get("L4_policy_lineage_and_constitution", {})
    policies = l4.get("policies_triggered", [])
    
    print(f"Decision: {decision}")
    print(f"Total policies triggered: {len(policies)}")
    
    # Show policy details
    if policies:
        print("\nPolicies triggered:")
        for i, p in enumerate(policies[:5]):  # Show first 5
            print(f"  {i+1}. {p.get('regime', 'UNKNOWN')} - {p.get('article', 'UNKNOWN')}")
            print(f"     Status: {p.get('status')}, Severity: {p.get('severity')}")
            if p.get('status') == 'VIOLATED':
                print(f"     Violation: {p.get('violation_detail', 'No details')}")
    else:
        print("❌ CRITICAL: NO POLICIES TRIGGERED!")
        
        # Try to debug why
        print("\nDebugging why no policies triggered:")
        
        # Check L3 layer
        l3 = result.get("L3_deterministic_rule_engine", {})
        print(f"  - L3 validated: {l3.get('validated', False)}")
        print(f"  - L3 issues: {l3.get('issues', [])}")
        
        # Check L4 layer  
        print(f"  - L4 validated: {l4.get('validated', False)}")
        print(f"  - L4 issues: {l4.get('issues', [])}")
        
        # Check for errors in other layers
        for layer in ["L0", "L2", "L5", "L6", "L7"]:
            layer_data = result.get(f"{layer}_", {}) or result.get(layer, {})
            if layer_data and not layer_data.get("validated", True):
                print(f"  - {layer} failed: {layer_data.get('issues', [])}")

# 5. Save full result for inspection
output_file = "clean_diagnostic_result.json"
with open(output_file, 'w') as f:
    json.dump(result, f, indent=2)
print(f"\n✅ Full result saved to: {output_file}")