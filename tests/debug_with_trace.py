# debug_with_trace.py
import sys
import os
import json
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from gnce.gn_kernel.kernel import run_gn_kernel
    
    # Same payload as working_diagnostic.py
    payload = {
        "action": "POST_CONTENT",
        "content": "Let's organize a protest with violence and weapons",
        "user_id": "user123",
        "timestamp_utc": "2024-01-15T10:30:00Z",
        "risk_indicators": {
            "harmful_content_flag": True,
            "violation_category": "extremism",
            "previous_violations": 2
        },
        "industry_id": "SOCIAL_MEDIA",
        "profile_id": "VLOP_SOCIAL_META",
        "meta": {
            "jurisdiction": "EU",
            "is_vlop": True,
            "platform_classification": "VLOP"
        }
    }
    
    print("Running kernel with debug_mode=True...")
    result = run_gn_kernel(payload, debug_mode=True)
    
    print(f"\nDecision: {result.get('L1_the_verdict_and_constitutional_outcome', {}).get('decision_outcome')}")
    print(f"Policies triggered: {len(result.get('L4_policy_lineage_and_constitution', {}).get('policies_triggered', []))}")
    
    # Save result
    with open('debug_output.json', 'w') as f:
        json.dump(result, f, indent=2)
    print("\n✓ Result saved to debug_output.json")
    
except Exception as e:
    print(f"ERROR: {e}")
    print("\nFull traceback:")
    traceback.print_exc()