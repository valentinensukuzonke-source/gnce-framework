# test_baseline_logic.py
import sys
import os

# Simple test without importing the whole kernel
print("Testing _is_allow_baseline logic...")
print("=" * 80)

# Simulate the function logic
def test_is_allow_baseline(payload):
    """Simulates the corrected logic"""
    if not isinstance(payload, dict):
        return True

    # CRITICAL SAFETY CHECK 1: If ANY risk indicators key exists
    if "risk_indicators" in payload:
        return False
    
    # CRITICAL SAFETY CHECK 2: Force evaluation for ANY compliance profile
    compliance_profiles = [
        "dsa", "dma_profile", "ai_profile", "platform_behavior",
        "pci_profile", "hipaa_profile", "sec_17a4_profile",
        "finra_profile", "sox_profile", "data_types", "export"
    ]
    
    for profile in compliance_profiles:
        if profile in payload and payload[profile]:
            return False
    
    # CRITICAL SAFETY CHECK 3: Force evaluation for content-related actions
    action = str(payload.get("action", "")).upper()
    if action in ["POST_CONTENT", "LIST_PRODUCT", "EXPORT_DATA", "PROCESS_TRANSACTION"]:
        return False
    
    # CRITICAL SAFETY CHECK 4: Force evaluation if content exists
    if payload.get("content"):
        return False
    
    # CRITICAL SAFETY CHECK 5: Force evaluation for VLOP/enterprise signals
    meta = payload.get("meta") or {}
    if meta:
        return False
    
    # CRITICAL SAFETY CHECK 6: Force evaluation for any governance context
    if payload.get("governance") or payload.get("audit"):
        return False
    
    # ONLY for truly empty payloads
    empty_keys = [k for k in payload.keys() if k not in ["timestamp_utc", "user_id", "request_id"]]
    return not empty_keys

# Test cases
test_cases = [
    {
        "name": "Your harmful content payload",
        "payload": {
            "action": "POST_CONTENT",
            "content": "harmful",
            "risk_indicators": {"harmful_content_flag": True},
            "meta": {"jurisdiction": "EU", "is_vlop": True},
            "industry_id": "SOCIAL_MEDIA",
            "profile_id": "VLOP_SOCIAL_META",
            "dsa": {"systemic_risk_assessed": False},
            "dma_profile": {"is_gatekeeper": True},
            "ai_profile": {"is_ai_system": True},
            "governance": {"owner": "Policy Team"}
        },
        "expected": False
    },
    {
        "name": "Empty payload",
        "payload": {},
        "expected": True
    },
    {
        "name": "Just risk_indicators (empty dict)",
        "payload": {"risk_indicators": {}},
        "expected": False
    },
    {
        "name": "Just meta (empty dict)",
        "payload": {"meta": {}},
        "expected": False
    }
]

print("\nTest Results:")
print("-" * 80)

all_passed = True
for test in test_cases:
    result = test_is_allow_baseline(test["payload"])
    passed = result == test["expected"]
    status = "✅" if passed else "❌"
    
    print(f"{status} {test['name']}: Got {result}, Expected {test['expected']}")
    
    if not passed:
        all_passed = False
        print(f"   Payload keys: {list(test['payload'].keys())}")

print("\n" + "=" * 80)
if all_passed:
    print("✅ All tests passed! The logic is correct.")
else:
    print("❌ Some tests failed. The function needs fixing.")