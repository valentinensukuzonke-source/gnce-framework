# trace_l3l4_error.py
import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Monkey-patch the logging to show full traceback
import logging

original_error = logging.Logger.error

def error_with_trace(self, msg, *args, **kwargs):
    if 'Error during L3/L4 evaluation' in str(msg):
        print("\n" + "="*80)
        print("CAPTURED L3/L4 ERROR WITH FULL TRACEBACK:")
        traceback.print_exc()
        print("="*80 + "\n")
    return original_error(self, msg, *args, **kwargs)

logging.Logger.error = error_with_trace

# Now run the kernel
from gnce.gn_kernel.kernel import run_gn_kernel_safe

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

print("Running kernel with traceback capture...")
result = run_gn_kernel_safe(payload)

# Also check if there's traceback in the result
if result.get('L3_deterministic_rule_engine', {}).get('evidence', {}).get('traceback'):
    print("\nFound traceback in L3 evidence:")
    print(result['L3_deterministic_rule_engine']['evidence']['traceback'])
elif result.get('L3_rule_level_trace', {}).get('evidence', {}).get('traceback'):
    print("\nFound traceback in L3 evidence:")
    print(result['L3_rule_level_trace']['evidence']['traceback'])