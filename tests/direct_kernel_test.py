# direct_kernel_test.py
import sys
import os

# Setup paths - Go to GNCE root first
gnce_root = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC"
os.chdir(gnce_root)  # Change to GNCE root directory
sys.path.insert(0, '.')
sys.path.insert(0, './gnce')
sys.path.insert(0, './gnce/gn_kernel')

print(f"Working directory: {os.getcwd()}")
print(f"Python path: {sys.path[:3]}")

# Now try to import
try:
    from gnce.gn_kernel.kernel import run_gn_kernel_safe
    print("✅ Successfully imported run_gn_kernel_safe")
    
    # Simple test
    test_payload = {
        "action": "POST_CONTENT",
        "content": "harmful test",
        "risk_indicators": {"harmful_content_flag": True}
    }
    
    result = run_gn_kernel_safe(test_payload)
    decision = result.get('L1_the_verdict_and_constitutional_outcome', {}).get('decision_outcome')
    
    print(f"\nDecision: {decision}")
    print(f"Expected: DENY (because harmful_content_flag=True)")
    
    if decision == "ALLOW":
        print("❌ BUG: Harmful content was allowed!")
    else:
        print("✅ Good: Harmful content was blocked")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()