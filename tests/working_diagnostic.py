# working_diagnostic.py
import sys
import os
import json

print("=" * 80)
print("WORKING GNCE KERNEL DIAGNOSTIC")
print("=" * 80)

# Get the absolute path to GNCE root
gnce_root = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC"
kernel_path = os.path.join(gnce_root, "gnce", "gn_kernel", "kernel.py")

print(f"GNCE root: {gnce_root}")
print(f"Kernel path: {kernel_path}")
print(f"Kernel exists: {os.path.exists(kernel_path)}")

# Add the correct paths to sys.path
sys.path.insert(0, os.path.join(gnce_root, "gnce"))  # Add gnce directory
sys.path.insert(0, os.path.join(gnce_root, "gnce", "gn_kernel"))  # Add gn_kernel directory
sys.path.insert(0, gnce_root)  # Add root directory

print(f"\nPython path (first 5):")
for p in sys.path[:5]:
    print(f"  - {p}")

# Now import - this should work!
print("\nAttempting import...")
try:
    # Option 1: Try the full path
    from gnce.gn_kernel.kernel import run_gn_kernel_safe
    print("✅ Successfully imported: from gnce.gn_kernel.kernel import run_gn_kernel_safe")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("\nTrying alternative import...")
    
    # Option 2: Try direct import from gn_kernel
    try:
        from gn_kernel.kernel import run_gn_kernel_safe
        print("✅ Successfully imported: from gn_kernel.kernel import run_gn_kernel_safe")
    except ImportError as e2:
        print(f"❌ Alternative import failed: {e2}")
        sys.exit(1)

# Test payload
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

print(f"\nTest payload loaded:")
print(f"  - Action: {test_payload['action']}")
print(f"  - Has harmful content: {test_payload['risk_indicators']['harmful_content_flag']}")
print(f"  - Industry: {test_payload['industry_id']}")
print(f"  - Profile: {test_payload['profile_id']}")

# Run kernel
print("\n" + "=" * 80)
print("RUNNING KERNEL...")
print("=" * 80)

try:
    result = run_gn_kernel_safe(test_payload)
    print("✅ Kernel execution completed")
    
    # Analyze the result
    print("\n" + "=" * 80)
    print("RESULT ANALYSIS")
    print("=" * 80)
    
    # Get L1 decision
    l1 = result.get('L1_the_verdict_and_constitutional_outcome', {})
    decision = l1.get('decision_outcome', 'UNKNOWN')
    rationale = l1.get('rationale', 'No rationale')
    
    print(f"DECISION: {decision}")
    print(f"Severity: {l1.get('severity', 'UNKNOWN')}")
    print(f"Rationale: {rationale}")
    
    # Check summary
    summary = l1.get('summary', {})
    print(f"\nSummary:")
    print(f"  - Policies considered: {summary.get('policies_considered', 0)}")
    print(f"  - Violations: {summary.get('violated', 0)}")
    print(f"  - Blocking violations: {summary.get('blocking_violations', 0)}")
    
    # Check policies
    policies = result.get('L4_policy_lineage_and_constitution', {}).get('policies_triggered', [])
    print(f"\nTotal policies triggered: {len(policies)}")
    
    if policies:
        print("\nFirst 10 policies:")
        for i, policy in enumerate(policies[:10]):
            status = policy.get('status', 'UNKNOWN')
            severity = policy.get('severity', 'UNKNOWN')
            article = policy.get('article', 'No article')
            regime = policy.get('regime', 'No regime')
            notes = policy.get('notes', '')[:50]
            print(f"  {i+1}. [{status}/{severity}] {regime} - {article}")
            if notes:
                print(f"     Notes: {notes}...")
    else:
        print("⚠️ CRITICAL: No policies were triggered!")
    
    # Check enabled regimes
    enabled_regimes = result.get('governance_context', {}).get('scope_enabled_regimes', [])
    if enabled_regimes:
        print(f"\nEnabled regimes: {enabled_regimes}")
    
    # Save detailed result
    output_file = "kernel_debug_output.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Full result saved to: {output_file}")
    
    # Critical issue detection
    if decision == "ALLOW" and test_payload['risk_indicators']['harmful_content_flag']:
        print("\n" + "!" * 80)
        print("❌❌❌ CRITICAL BUG CONFIRMED ❌❌❌")
        print(f"  Harmful content (flag=True) was ALLOWED!")
        print(f"  Policies considered: {summary.get('policies_considered', 0)}")
        print(f"  Violations found: {summary.get('violated', 0)}")
        print("!" * 80)
        
        # Debug why
        print("\nDebugging why...")
        print(f"1. Baseline check would return: {_is_allow_baseline(test_payload) if '_is_allow_baseline' in locals() else 'Function not available'}")
        print(f"2. Has risk indicators: {bool(test_payload.get('risk_indicators'))}")
        print(f"3. Has DSA profile: {bool(test_payload.get('dsa'))}")
        print(f"4. Has DMA profile: {bool(test_payload.get('dma_profile'))}")
        print(f"5. Has AI profile: {bool(test_payload.get('ai_profile'))}")
    
except Exception as e:
    print(f"\n❌ Error running kernel: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)