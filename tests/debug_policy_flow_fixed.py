# debug_policy_flow.py
import sys
import os
import json

print("=" * 80)
print("DEBUG POLICY FLOW - FIXED VERSION")
print("=" * 80)

# Get the absolute paths
gnce_root = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC"
gnce_dir = os.path.join(gnce_root, "gnce")
gn_kernel_dir = os.path.join(gnce_dir, "gn_kernel")

print(f"GNCE root: {gnce_root}")
print(f"GNCE dir: {gnce_dir}")
print(f"GN Kernel dir: {gn_kernel_dir}")

# Clear and set up paths properly
sys.path.clear()
sys.path.insert(0, gn_kernel_dir)  # First look in gn_kernel
sys.path.insert(0, gnce_dir)       # Then in gnce
sys.path.insert(0, gnce_root)      # Then in root
sys.path.insert(0, os.getcwd())    # Current directory

print(f"\nPython path:")
for i, p in enumerate(sys.path[:6]):
    print(f"{i+1}. {p}")

# Try to find and load kernel module
print("\nLooking for kernel module...")
kernel_module = None
kernel_path = os.path.join(gn_kernel_dir, "kernel.py")

if os.path.exists(kernel_path):
    print(f"✅ Found kernel.py at: {kernel_path}")
    
    # Load the module manually
    import importlib.util
    spec = importlib.util.spec_from_file_location("gn_kernel.kernel", kernel_path)
    kernel_module = importlib.util.module_from_spec(spec)
    
    # Execute the module to load it
    spec.loader.exec_module(kernel_module)
    print("✅ Successfully loaded kernel module")
    
    # Check what functions are available
    print(f"Functions in kernel module: {[x for x in dir(kernel_module) if not x.startswith('_')][:10]}")
else:
    print("❌ kernel.py not found!")
    sys.exit(1)

# Now monkey-patch the functions
print("\n" + "=" * 80)
print("MONKEY PATCHING FOR DEBUGGING")
print("=" * 80)

# Store original functions
original_evaluate_policies = kernel_module._evaluate_policies
original_is_allow_baseline = kernel_module._is_allow_baseline

def debug_evaluate_policies(payload, enabled_regimes=None):
    """Debug wrapper for _evaluate_policies"""
    print("\n" + ">" * 60)
    print("DEBUG _evaluate_policies CALLED")
    print(">" * 60)
    
    print(f"Payload keys: {list(payload.keys())}")
    print(f"Enabled regimes: {enabled_regimes}")
    
    # Check baseline
    baseline_result = original_is_allow_baseline(payload)
    print(f"Baseline mode would return: {baseline_result}")
    
    # Check risk indicators
    risk = payload.get("risk_indicators", {})
    print(f"Risk indicators: {risk}")
    
    # Check DSA signals
    print(f"DSA profile present: {'dsa' in payload}")
    print(f"Meta.is_vlop: {payload.get('meta', {}).get('is_vlop')}")
    
    # Call original
    print("\nCalling original _evaluate_policies...")
    policies, summary = original_evaluate_policies(payload, enabled_regimes)
    
    print(f"\nResults:")
    print(f"- Policies returned: {len(policies)}")
    print(f"- Summary: {summary}")
    
    if policies:
        print("\nFirst 3 policies:")
        for i, p in enumerate(policies[:3]):
            print(f"{i+1}. {p.get('regime')} - {p.get('article')} - {p.get('status')}")
    
    return policies, summary

def debug_is_allow_baseline(payload):
    """Debug wrapper for _is_allow_baseline"""
    result = original_is_allow_baseline(payload)
    
    print("\n" + "-" * 50)
    print("DEBUG _is_allow_baseline")
    print("-" * 50)
    
    # Check all the conditions
    print(f"1. Has risk_indicators: {'risk_indicators' in payload}")
    if 'risk_indicators' in payload:
        risk = payload.get("risk_indicators", {})
        print(f"   - harmful_content_flag: {risk.get('harmful_content_flag')}")
        print(f"   - violation_category: {risk.get('violation_category')}")
    
    print(f"2. Has dma_profile: {'dma_profile' in payload}")
    print(f"3. Has ai_profile: {'ai_profile' in payload}")
    print(f"4. Has dsa: {'dsa' in payload}")
    print(f"5. Action: {payload.get('action')}")
    print(f"6. Has content: {bool(payload.get('content'))}")
    
    print(f"\nFINAL RESULT: {result}")
    print("-" * 50)
    
    return result

# Apply patches
kernel_module._evaluate_policies = debug_evaluate_policies
kernel_module._is_allow_baseline = debug_is_allow_baseline

print("✅ Patches applied successfully")

# Test payload
print("\n" + "=" * 80)
print("TEST PAYLOAD")
print("=" * 80)

test_payload = {
    "action": "POST_CONTENT",
    "content": "How to do something harmful (test)",
    "user_id": "user-demo-001",
    "timestamp_utc": "2026-01-04T20:38:10+00:00",
    "risk_indicators": {
        "harmful_content_flag": True,
        "violation_category": "harmful_content",
        "previous_violations": 0
    },
    "meta": {
        "jurisdiction": "EU",
        "customer_profile_id": "VLOP_SOCIAL_META",
        "is_vlop": True
    },
    "industry_id": "SOCIAL_MEDIA",
    "profile_id": "VLOP_SOCIAL_META",
    "platform_behavior": {
        "self_preference": False,
        "ranking_bias": False
    },
    "dsa": {
        "systemic_risk_assessed": False,
        "mitigation_measures_in_place": True
    },
    "dma_profile": {
        "is_gatekeeper": True
    },
    "ai_profile": {
        "is_ai_system": True
    }
}

print(f"Payload prepared with {len(test_payload.keys())} keys")
print(f"Harmful content flag: {test_payload['risk_indicators']['harmful_content_flag']}")

# Import run_gn_kernel_safe from the patched module
run_gn_kernel_safe = kernel_module.run_gn_kernel_safe

print("\n" + "=" * 80)
print("RUNNING KERNEL WITH DEBUG PATCHES")
print("=" * 80)

try:
    result = run_gn_kernel_safe(test_payload)
    print("✅ Kernel execution completed")
    
    # Analyze result
    print("\n" + "=" * 80)
    print("FINAL ANALYSIS")
    print("=" * 80)
    
    l1 = result.get('L1_the_verdict_and_constitutional_outcome', {})
    decision = l1.get('decision_outcome', 'UNKNOWN')
    rationale = l1.get('rationale', 'No rationale')
    
    print(f"Decision: {decision}")
    print(f"Rationale: {rationale}")
    
    summary = l1.get('summary', {})
    print(f"\nSummary:")
    print(f"- Policies considered: {summary.get('policies_considered', 0)}")
    print(f"- Violations: {summary.get('violated', 0)}")
    print(f"- Blocking violations: {summary.get('blocking_violations', 0)}")
    
    policies = result.get('L4_policy_lineage_and_constitution', {}).get('policies_triggered', [])
    print(f"\nTotal policies in result: {len(policies)}")
    
    # Check if harmful content was blocked
    if decision == "ALLOW" and test_payload['risk_indicators']['harmful_content_flag']:
        print("\n❌❌❌ BUG CONFIRMED ❌❌❌")
        print("Harmful content was ALLOWED!")
        print("\nDebug info from patches should show above.")
        
    # Save result
    with open("debug_patch_result.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n✅ Result saved to: debug_patch_result.json")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("DEBUG COMPLETE")
print("=" * 80)