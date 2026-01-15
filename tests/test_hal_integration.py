import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🧪 Testing HAL Integration with Real Kernel")

try:
    # Import HAL kernel
    from gnce.gn_kernel.hal_integration import get_hal_kernel
    
    # Create HAL-enhanced kernel
    hal_kernel = get_hal_kernel()
    print(f"✅ HAL Kernel created: {type(hal_kernel)}")
    
    # Test with your L0-L7 example payload
    test_payload = {
        "action": "LIST_PRODUCT",
        "content": "Attempt to list a prohibited/unsafe item (should be blocked by marketplace policy).",
        "user_id": "user-ecommerce_marketplace_eu-demo",
        "timestamp_utc": "2026-01-04T21:31:00+00:00",
        "risk_indicators": {"harmful_content_flag": True},
        "meta": {},
        "industry_id": "ECOMMERCE",
        "profile_id": "ECOMMERCE_MARKETPLACE_EU",
        "listing": {"category": "PROHIBITED_LISTING"}
    }
    
    print(f"\n📥 Test payload prepared")
    print(f"Action: {test_payload['action']}")
    print(f"Industry: {test_payload['industry_id']}")
    print(f"Profile: {test_payload['profile_id']}")
    
    # Evaluate
    result = hal_kernel.evaluate(test_payload)
    
    print(f"\n✅ Evaluation successful!")
    print(f"Result type: {type(result)}")
    
    # Check for layers
    layers_found = [key for key in result.keys() if key.startswith('L') and len(key) == 2]
    print(f"Layers found: {sorted(layers_found)}")
    
    # Check HAL integration
    if '_hal' in result:
        print(f"\n🎯 HAL Integration Active!")
        hal_info = result['_hal']
        print(f"  GPUx Ready: {hal_info.get('gpux_ready', False)}")
        print(f"  Bundle Hash: {hal_info.get('constitutional_bundle_hash', '')[:32]}...")
    
    # Show L1 verdict if available
    if 'L1' in result:
        l1 = result['L1']
        print(f"\n📊 L1 Verdict:")
        print(f"  Outcome: {l1.get('decision_outcome', 'UNKNOWN')}")
        print(f"  Severity: {l1.get('severity', 'UNKNOWN')}")
    
    # Show L7 veto if available
    if 'L7' in result:
        l7 = result['L7']
        print(f"\n🚫 L7 Veto:")
        print(f"  Execution Authorized: {l7.get('execution_authorized', False)}")
        print(f"  Veto Triggered: {l7.get('veto_triggered', False)}")
    
    print(f"\n🎉 HAL Integration Test Complete!")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
except AttributeError as e:
    print(f"❌ Attribute Error: {e}")
    print("\nTrying to find kernel structure...")
    import gnce.gn_kernel.kernel as km
    print(f"Available in kernel module: {[x for x in dir(km) if not x.startswith('_')]}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
