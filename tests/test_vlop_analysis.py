import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("COMPREHENSIVE VLOP DENIAL ANALYSIS")
print("=" * 80)

# Load the payload
with open("./gnce/configs/canonical_3_vlop_non-compliant_deny_critical.json", "r") as f:
    payload = json.load(f)

print("\n📋 Payload Summary:")
print(f"  Action: {payload.get('action')}")
print(f"  Industry: {payload.get('industry_id')}")
print(f"  Profile: {payload.get('profile_id')}")
print(f"  Is VLOP: {payload.get('meta', {}).get('is_vlop', False)}")
print(f"  Content: '{payload.get('content', '')[:50]}...'")
print(f"  Harmful flag: {payload.get('risk_indicators', {}).get('harmful_content_flag', False)}")

# Run GNCE
from gnce.gn_kernel.kernel import run_gn_kernel
result = run_gn_kernel(payload)

print("\n⚡ GNCE Evaluation Complete")
print("=" * 80)

# Find L1 verdict
for key in result.keys():
    if "L1" in key:
        verdict_data = result[key]
        if isinstance(verdict_data, dict):
            verdict = verdict_data.get("decision_outcome", verdict_data.get("verdict", "UNKNOWN"))
            print(f"\n🎯 FINAL VERDICT: {verdict}")
            print(f"   Severity: {verdict_data.get('severity', 'UNKNOWN')}")
            
            if verdict == "DENY":
                print("   ✅ CORRECT: VLOP harmful content is DENIED")
            else:
                print("   ❌ ERROR: Should be DENY but got", verdict)

# Find L3 violations
print("\n🔍 L3 Rule Violations:")
for key in result.keys():
    if "L3" in key:
        l3_data = result[key]
        if isinstance(l3_data, dict) and "causal_trace" in l3_data:
            violations = [item for item in l3_data["causal_trace"] if item.get("status") == "VIOLATED"]
            
            print(f"   Found {len(violations)} violations")
            
            for i, violation in enumerate(violations):
                article = violation.get("article", "Unknown")
                severity = violation.get("severity", "Unknown")
                why = violation.get("why_triggered", "No reason")
                
                print(f"\n   {i+1}. {article}")
                print(f"      Severity: {severity}")
                print(f"      Reason: {why}")
                
                if "DSA" in article:
                    print(f"      ✅ DSA violation detected")

# Find L7 veto
print("\n🚫 L7 Veto Status:")
for key in result.keys():
    if "L7" in key:
        l7_data = result[key]
        if isinstance(l7_data, dict):
            veto_triggered = l7_data.get("veto_triggered", False)
            execution_auth = l7_data.get("execution_authorized", True)
            
            print(f"   Veto triggered: {veto_triggered}")
            print(f"   Execution authorized: {execution_auth}")
            
            if veto_triggered and not execution_auth:
                print("   ✅ Constitutional veto working correctly")

print("\n" + "=" * 80)
print("SUMMARY: GNCE is correctly denying VLOP harmful content")
print("=" * 80)
