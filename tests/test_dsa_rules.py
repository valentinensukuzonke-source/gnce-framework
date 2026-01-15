import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test DSA rules directly
from gnce.gn_kernel.rules.dsa_rules import evaluate_dsa_rules

# Load payload
with open("./gnce/configs/canonical_3_vlop_non-compliant_deny_critical.json", "r") as f:
    payload = json.load(f)

print("Direct DSA Rules Evaluation:")
print("=" * 60)

results, summary = evaluate_dsa_rules(payload)

print(f"\n📊 DSA Summary:")
print(f"  Total rules: {summary.get('total_rules', 0)}")
print(f"  Passed: {summary.get('passed', 0)}")
print(f"  Failed: {summary.get('failed', 0)}")
print(f"  Blocking failures: {summary.get('blocking_failures', 0)}")

print(f"\n🔴 DSA Violations (Blocking):")
blocking_violations = [r for r in results if r.get("status") == "VIOLATED" and r.get("blocking") is True]

for i, violation in enumerate(blocking_violations):
    print(f"\n  {i+1}. {violation.get('article', 'Unknown')}")
    print(f"     Why: {violation.get('why_triggered', 'No reason')}")
    print(f"     Severity: {violation.get('severity', 'Unknown')}")
    print(f"     Remediation: {violation.get('remediation', 'None specified')}")

print(f"\n🟡 DSA Violations (Non-blocking):")
non_blocking = [r for r in results if r.get("status") == "VIOLATED" and r.get("blocking") is False]

for i, violation in enumerate(non_blocking):
    print(f"\n  {i+1}. {violation.get('article', 'Unknown')}")
    print(f"     Why: {violation.get('why_triggered', 'No reason')}")

print(f"\n✅ DSA Rules Analysis Complete")
