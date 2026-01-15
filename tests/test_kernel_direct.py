# test_kernel_direct.py
import sys
import os

# Change to GNCE root
gnce_root = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC"
os.chdir(gnce_root)
sys.path.insert(0, '.')

print(f"Working directory: {os.getcwd()}")

# Import the kernel module directly
try:
    import importlib.util
    kernel_path = os.path.join(gnce_root, "gnce", "gn_kernel", "kernel.py")
    spec = importlib.util.spec_from_file_location("gn_kernel.kernel", kernel_path)
    kernel = importlib.util.module_from_spec(spec)
    
    # Patch sys.modules to avoid import errors
    sys.modules['gnce.gn_kernel.kernel'] = kernel
    
    # Execute the module
    spec.loader.exec_module(kernel)
    print("✅ Loaded kernel module")
    
    # Test the _evaluate_policies function directly
    print("\nTesting _evaluate_policies directly...")
    
    test_payload = {
        "action": "POST_CONTENT",
        "content": "How to do something harmful",
        "risk_indicators": {
            "harmful_content_flag": True,
            "violation_category": "harmful_content"
        },
        "meta": {
            "jurisdiction": "EU",
            "is_vlop": True
        },
        "industry_id": "SOCIAL_MEDIA",
        "dsa": {
            "systemic_risk_assessed": False
        }
    }
    
    # Call _evaluate_policies directly
    policies, summary = kernel._evaluate_policies(test_payload, enabled_regimes=["DSA"])
    
    print(f"Direct evaluation result:")
    print(f"- Policies: {len(policies)}")
    print(f"- Summary: {summary}")
    
    if policies:
        print("\nPolicies found:")
        for i, p in enumerate(policies[:5]):
            print(f"{i+1}. {p.get('regime')} - {p.get('article')} - {p.get('status')}")
    else:
        print("\n❌ No policies returned!")
        
        # Test with all regimes enabled
        print("\nTesting with all regimes enabled...")
        policies2, summary2 = kernel._evaluate_policies(test_payload, enabled_regimes=None)
        print(f"All regimes: {len(policies2)} policies")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()