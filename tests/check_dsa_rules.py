# check_dsa_rules.py
import sys
import os

# Setup paths
gnce_root = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC"
sys.path.insert(0, os.path.join(gnce_root, "gnce"))
sys.path.insert(0, os.path.join(gnce_root, "gnce", "gn_kernel"))

print("Testing DSA rules evaluator...")
print("=" * 80)

try:
    # Try to import DSA rules
    from gnce.gn_kernel.rules.dsa_rules import evaluate_dsa_rules
    print("✅ Successfully imported evaluate_dsa_rules")
    
    # Test with harmful content
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
    
    print("\nRunning evaluate_dsa_rules...")
    policies, summary = evaluate_dsa_rules(test_payload)
    
    print(f"Results: {len(policies)} policies")
    print(f"Summary: {summary}")
    
    if policies:
        print("\nDSA Policies found:")
        for i, p in enumerate(policies[:5]):
            print(f"{i+1}. {p.get('regime')} - {p.get('article')} - {p.get('status')}")
            if p.get('status') == 'VIOLATED':
                print(f"   Violation: {p.get('violation_detail', 'No details')[:100]}...")
    else:
        print("❌ No DSA policies returned!")
        
except ImportError as e:
    print(f"❌ Failed to import DSA rules: {e}")
    
    # Try to find the file
    dsa_rules_path = os.path.join(gnce_root, "gnce", "gn_kernel", "rules", "dsa_rules.py")
    if os.path.exists(dsa_rules_path):
        print(f"✅ Found dsa_rules.py at: {dsa_rules_path}")
        
        # Try to load it directly
        import importlib.util
        spec = importlib.util.spec_from_file_location("dsa_rules", dsa_rules_path)
        dsa_rules = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dsa_rules)
        
        if hasattr(dsa_rules, 'evaluate_dsa_rules'):
            evaluate_dsa_rules = dsa_rules.evaluate_dsa_rules
            print("✅ Loaded evaluate_dsa_rules directly")
        else:
            print(f"❌ dsa_rules module doesn't have evaluate_dsa_rules")
    else:
        print(f"❌ dsa_rules.py not found at: {dsa_rules_path}")
        
except Exception as e:
    print(f"❌ Error running DSA rules: {e}")
    import traceback
    traceback.print_exc()