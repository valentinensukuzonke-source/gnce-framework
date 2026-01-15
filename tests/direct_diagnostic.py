# direct_diagnostic.py
import sys
import os
import json

print("=" * 80)
print("GNCE KERNEL DIAGNOSTIC")
print("=" * 80)

# First, let's find where we are
current_dir = os.getcwd()
print(f"Current directory: {current_dir}")

# Look for kernel.py from current directory
print("\nSearching for kernel.py...")
kernel_path = None

for root, dirs, files in os.walk('.'):
    if 'kernel.py' in files:
        kernel_path = os.path.abspath(os.path.join(root, 'kernel.py'))
        print(f"✅ Found kernel.py at: {kernel_path}")
        
        # Add the directory containing kernel.py to sys.path
        kernel_dir = os.path.dirname(kernel_path)
        sys.path.insert(0, kernel_dir)
        
        # Also add parent directory
        parent_dir = os.path.dirname(kernel_dir)
        sys.path.insert(0, parent_dir)
        
        # Add current directory
        sys.path.insert(0, current_dir)
        break

if not kernel_path:
    print("❌ kernel.py not found! Searching more broadly...")
    # Try searching from GNCE root
    gnce_root = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC"
    for root, dirs, files in os.walk(gnce_root):
        if 'kernel.py' in files:
            kernel_path = os.path.join(root, 'kernel.py')
            print(f"✅ Found kernel.py at: {kernel_path}")
            
            kernel_dir = os.path.dirname(kernel_path)
            sys.path.insert(0, kernel_dir)
            sys.path.insert(0, os.path.dirname(kernel_dir))
            break

print(f"\nPython path:")
for p in sys.path[:10]:  # Show first 10
    print(f"  - {p}")

# Now try to import
print("\nAttempting imports...")

# Try multiple import strategies
import_success = False
kernel_module = None

try:
    # Strategy 1: Direct import from gnce.gn_kernel.kernel
    from gnce.gn_kernel.kernel import run_gn_kernel_safe
    print("✅ Imported: from gnce.gn_kernel.kernel import run_gn_kernel_safe")
    import_success = True
except ImportError as e1:
    print(f"❌ Strategy 1 failed: {e1}")
    
    try:
        # Strategy 2: Import from gn_kernel.kernel
        from gn_kernel.kernel import run_gn_kernel_safe
        print("✅ Imported: from gn_kernel.kernel import run_gn_kernel_safe")
        import_success = True
    except ImportError as e2:
        print(f"❌ Strategy 2 failed: {e2}")
        
        try:
            # Strategy 3: Import kernel module directly
            import importlib.util
            spec = importlib.util.spec_from_file_location("kernel", kernel_path)
            kernel_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(kernel_module)
            
            if hasattr(kernel_module, 'run_gn_kernel_safe'):
                run_gn_kernel_safe = kernel_module.run_gn_kernel_safe
                print("✅ Loaded kernel module directly")
                import_success = True
            else:
                print("❌ kernel module doesn't have run_gn_kernel_safe")
                print(f"Available functions: {[x for x in dir(kernel_module) if not x.startswith('_')][:10]}")
        except Exception as e3:
            print(f"❌ Strategy 3 failed: {e3}")

if not import_success:
    print("\n❌ All import strategies failed!")
    print("\nPlease check:")
    print("1. Are you in the correct directory?")
    print("2. Is kernel.py in your project?")
    print("3. Try running from GNCE root directory instead")
    sys.exit(1)

# Test payload
print("\n" + "=" * 80)
print("TEST PAYLOAD")
print("=" * 80)

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

print(f"Payload keys: {list(test_payload.keys())}")
print(f"Has harmful content flag: {test_payload['risk_indicators']['harmful_content_flag']}")

# Run kernel
print("\n" + "=" * 80)
print("RUNNING KERNEL")
print("=" * 80)

try:
    result = run_gn_kernel_safe(test_payload)
    print("✅ Kernel execution completed")
    
    # Analyze result
    print("\n" + "=" * 80)
    print("RESULT ANALYSIS")
    print("=" * 80)
    
    l1 = result.get('L1_the_verdict_and_constitutional_outcome', {})
    decision = l1.get('decision_outcome', 'UNKNOWN')
    rationale = l1.get('rationale', 'No rationale provided')
    
    print(f"Decision: {decision}")
    print(f"Severity: {l1.get('severity', 'UNKNOWN')}")
    print(f"Rationale: {rationale}")
    
    # Check policies
    policies = result.get('L4_policy_lineage_and_constitution', {}).get('policies_triggered', [])
    print(f"\nTotal policies triggered: {len(policies)}")
    
    if policies:
        print("\nFirst 5 policies:")
        for i, policy in enumerate(policies[:5]):
            status = policy.get('status', 'UNKNOWN')
            severity = policy.get('severity', 'UNKNOWN')
            article = policy.get('article', 'No article')
            regime = policy.get('regime', 'No regime')
            print(f"  {i+1}. [{status}/{severity}] {regime} - {article}")
    else:
        print("⚠️ No policies were triggered!")
    
    # Summary
    summary = l1.get('summary', {})
    print(f"\nSummary:")
    print(f"  - Policies considered: {summary.get('policies_considered', 0)}")
    print(f"  - Violations: {summary.get('violated', 0)}")
    print(f"  - Blocking violations: {summary.get('blocking_violations', 0)}")
    
    # Save result
    output_file = "kernel_result_detailed.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Full result saved to: {output_file}")
    
    # Critical check
    if decision == "ALLOW" and test_payload['risk_indicators']['harmful_content_flag']:
        print("\n❌❌❌ CRITICAL ISSUE DETECTED ❌❌❌")
        print("Harmful content was ALLOWED instead of DENIED!")
        print("This confirms the bug we need to fix.")
        
except Exception as e:
    print(f"\n❌ Error running kernel: {e}")
    import traceback
    traceback.print_exc()