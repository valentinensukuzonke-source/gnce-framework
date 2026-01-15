# test_kernel_with_trace.py
import sys
import os
import json

# Setup paths
gnce_root = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC"
sys.path.insert(0, os.path.join(gnce_root, "gnce"))
sys.path.insert(0, os.path.join(gnce_root, "gnce", "gn_kernel"))

print("Testing kernel with trace...")
print("=" * 80)

try:
    from gnce.gn_kernel.kernel import run_gn_kernel_safe
    print("✅ Imported run_gn_kernel_safe")
    
    # Simple test payload
    simple_payload = {
        "action": "POST_CONTENT",
        "content": "harmful test",
        "risk_indicators": {
            "harmful_content_flag": True
        },
        "meta": {
            "jurisdiction": "EU"
        },
        "industry_id": "SOCIAL_MEDIA"
    }
    
    print(f"\nRunning kernel with simple payload...")
    result = run_gn_kernel_safe(simple_payload)
    
    # Check result
    l1 = result.get('L1_the_verdict_and_constitutional_outcome', {})
    decision = l1.get('decision_outcome', 'UNKNOWN')
    
    print(f"\nSimple test result:")
    print(f"Decision: {decision}")
    print(f"Rationale: {l1.get('rationale', 'No rationale')}")
    
    policies = result.get('L4_policy_lineage_and_constitution', {}).get('policies_triggered', [])
    print(f"Policies triggered: {len(policies)}")
    
    if decision == "ALLOW":
        print("\n❌ Simple harmful content was ALLOWED!")
        print("\nChecking what regimes were enabled...")
        enabled_regimes = result.get('governance_context', {}).get('scope_enabled_regimes', [])
        print(f"Enabled regimes: {enabled_regimes}")
        
        # Save for analysis
        with open("simple_test_result.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n✅ Result saved to: simple_test_result.json")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()