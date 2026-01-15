# test_baseline_fix.py
import sys
import os

# Setup paths
gnce_root = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC"
gn_kernel_dir = os.path.join(gnce_root, "gnce", "gn_kernel")

sys.path.insert(0, gn_kernel_dir)
sys.path.insert(0, os.path.join(gnce_root, "gnce"))

# Load kernel module
import importlib.util
kernel_path = os.path.join(gn_kernel_dir, "kernel.py")
spec = importlib.util.spec_from_file_location("kernel", kernel_path)
kernel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kernel)

print("Testing _is_allow_baseline function directly...")

# Test cases
test_cases = [
    {
        "name": "Harmful content",
        "payload": {
            "risk_indicators": {"harmful_content_flag": True},
            "action": "POST_CONTENT"
        },
        "expected": False  # Should force evaluation
    },
    {
        "name": "DMA profile",
        "payload": {
            "dma_profile": {"is_gatekeeper": True},
            "action": "POST_CONTENT"
        },
        "expected": False
    },
    {
        "name": "Empty payload",
        "payload": {},
        "expected": True  # Should allow baseline
    },
    {
        "name": "VLOP with harmful content",
        "payload": {
            "risk_indicators": {"harmful_content_flag": True},
            "dsa": {"systemic_risk_assessed": False},
            "meta": {"is_vlop": True},
            "action": "POST_CONTENT"
        },
        "expected": False
    }
]

print("\n" + "=" * 80)
for test in test_cases:
    result = kernel._is_allow_baseline(test["payload"])
    status = "✅" if result == test["expected"] else "❌"
    print(f"{status} {test['name']}: Got {result}, Expected {test['expected']}")
    
print("\n" + "=" * 80)
print("If any ❌ appear, the _is_allow_baseline function needs fixing.")