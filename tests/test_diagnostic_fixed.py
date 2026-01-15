# test_diagnostic_fixed.py
import sys
import os
import json

# Clear any existing paths and add the correct ones
sys.path.clear()

# Add the GNCE root directory
gnce_root = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC"
sys.path.insert(0, gnce_root)

# Also add the parent directory in case of nested structure
parent_dir = os.path.dirname(gnce_root)
sys.path.insert(0, parent_dir)

print(f"Python path after setup:")
for p in sys.path:
    print(f"  - {p}")

print(f"\nCurrent directory: {os.getcwd()}")
print(f"GNCE root: {gnce_root}")

# First, let's see what's actually in the gnce directory
print("\n=== Checking GNCE structure ===")
gnce_path = os.path.join(gnce_root, "gnce")
if os.path.exists(gnce_path):
    print(f"✓ Found gnce directory at: {gnce_path}")
    print("Contents of gnce directory:")
    for item in os.listdir(gnce_path)[:10]:  # Show first 10 items
        print(f"  - {item}")
else:
    print(f"✗ gnce directory not found at: {gnce_path}")
    print("Looking for alternative structure...")
    
    # Search for kernel.py
    for root, dirs, files in os.walk(gnce_root):
        if "kernel.py" in files:
            print(f"✓ Found kernel.py at: {root}")
            # Add the directory containing kernel.py to path
            sys.path.insert(0, os.path.dirname(root))
            break

# Now try to import
print("\n=== Attempting imports ===")
try:
    # Try direct import first
    from gnce.gn_kernel.kernel import run_gn_kernel_safe
    print("✓ Successfully imported run_gn_kernel_safe from gnce.gn_kernel.kernel")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    
    print("\nTrying alternative import locations...")
    # Try different import patterns
    try:
        # Maybe it's directly in gn_kernel?
        from gn_kernel.kernel import run_gn_kernel_safe
        print("✓ Successfully imported from gn_kernel.kernel")
    except ImportError as e2:
        print(f"✗ Alternative import failed: {e2}")
        
        # Last attempt: try to find and import the module directly
        print("\nSearching for kernel module...")
        for root, dirs, files in os.walk(gnce_root):
            if "kernel.py" in files:
                kernel_path = os.path.join(root, "kernel.py")
                print(f"Found kernel.py at: {kernel_path}")
                
                # Try to import it as a module
                module_dir = os.path.dirname(kernel_path)
                module_name = os.path.basename(module_dir)
                
                print(f"Module directory: {module_dir}")
                print(f"Module name: {module_name}")
                
                # Add the directory to path
                sys.path.insert(0, module_dir)
                sys.path.insert(0, os.path.dirname(module_dir))
                
                try:
                    # Try importing the module directly
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("kernel", kernel_path)
                    kernel_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(kernel_module)
                    
                    if hasattr(kernel_module, 'run_gn_kernel_safe'):
                        run_gn_kernel_safe = kernel_module.run_gn_kernel_safe
                        print("✓ Loaded kernel module directly!")
                    else:
                        print(f"✗ kernel module doesn't have run_gn_kernel_safe")
                        print(f"Available functions: {[x for x in dir(kernel_module) if not x.startswith('_')]}")
                except Exception as e3:
                    print(f"✗ Direct module load failed: {e3}")
                break

# If we still don't have the function, exit
if 'run_gn_kernel_safe' not in locals() and 'run_gn_kernel_safe' not in globals():
    print("\n✗ Could not find run_gn_kernel_safe function")
    print("\nPlease check your GNCE structure and share:")
    print("1. The directory structure starting from GNCE v0.7.2-RC")
    print("2. The location of kernel.py")
    sys.exit(1)

# Your test payload
print("\n=== Loading test payload ===")
test_payload = {
    "action": "POST_CONTENT",
    "content": "How to do something harmful (test) — should be blocked.",
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
        "mitigation_measures_in_place": True,
        "independent_audit_last_12m": True,
        "crisis_protocol_defined": True,
        "crisis_protocol_tested": True,
        "researcher_data_access": True,
        "non_profiling_option_exposed": True,
        "minors_risk_programme": True,
        "age_assurance_controls": True,
        "transparency_report_published": True,
        "internal_complaint_system_available": True,
        "out_of_court_body_recognised": True
    },
    "dma_profile": {
        "is_gatekeeper": True,
        "self_preferencing": False,
        "data_combining_without_consent": False,
        "ranking_data_discrimination": False,
        "bundling_detected": False,
        "interoperability_refused": False,
        "anti_steering_blocked": False
    },
    "audit": {
        "dma_audit_completed": True
    },
    "ai_profile": {
        "is_ai_system": True,
        "prohibited_practice": False,
        "high_risk": False,
        "transparency_notice": True,
        "model_id": "gnce-demo-model-1",
        "system_id": "gnce-demo-system-1"
    },
    "governance": {
        "owner": "Policy & Compliance Team",
        "roles_defined": True,
        "risk_management": True,
        "controls_enabled": True,
        "incident_response_process": True,
        "model_inventory": True,
        "model_id": "gnce-demo-model-1",
        "testing": {
            "completed": True,
            "last_tested_utc": "2026-01-04T20:38:10+00:00"
        },
        "eval_metrics": {
            "primary": "accuracy",
            "threshold": 0.8,
            "observed": 0.92
        },
        "monitoring": {
            "enabled": True,
            "drift_monitoring": True
        }
    }
}

print("✓ Test payload loaded")

# Run the kernel
print("\n=== RUNNING KERNEL DIAGNOSTIC ===")
try:
    result = run_gn_kernel_safe(test_payload)
    print("✓ Kernel evaluation completed")
    
    # Print results
    print(f"\n=== DECISION ===")
    l1 = result.get('L1_the_verdict_and_constitutional_outcome', {})
    print(f"Outcome: {l1.get('decision_outcome')}")
    print(f"Severity: {l1.get('severity')}")
    print(f"Rationale: {l1.get('rationale')}")
    
    print(f"\n=== POLICIES TRIGGERED ===")
    policies = result.get('L4_policy_lineage_and_constitution', {}).get('policies_triggered', [])
    print(f"Total policies: {len(policies)}")
    for i, policy in enumerate(policies[:10]):
        print(f"{i+1}. {policy.get('regime')} - {policy.get('article')} - {policy.get('status')} - Severity: {policy.get('severity')}")
    
    print(f"\n=== SUMMARY ===")
    summary = result.get('L1_the_verdict_and_constitutional_outcome', {}).get('summary', {})
    print(f"Policies considered: {summary.get('policies_considered', 0)}")
    print(f"Violations: {summary.get('violated', 0)}")
    print(f"Blocking violations: {summary.get('blocking_violations', 0)}")
    
    # Save full result to file
    output_file = "kernel_debug_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Full result saved to: {output_file}")
    
except Exception as e:
    print(f"✗ Error running kernel: {e}")
    import traceback
    traceback.print_exc()