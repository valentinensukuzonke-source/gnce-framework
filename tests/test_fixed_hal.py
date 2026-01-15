import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🧪 Testing Fixed HAL Integration")

try:
    from gnce.gn_kernel.hal_integration_fixed import get_hal_kernel
    
    # Get HAL kernel
    kernel = get_hal_kernel()
    print(f"✅ HAL Kernel created: {type(kernel)}")
    
    # Test payload from your L0-L7 example
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
    
    print(f"\n📥 Test payload:")
    print(f"  Action: {test_payload['action']}")
    print(f"  Industry: {test_payload['industry_id']}")
    print(f"  Profile: {test_payload['profile_id']}")
    
    # Evaluate
    print(f"\n⚡ Running evaluation...")
    result = kernel.evaluate(test_payload)
    
    print(f"\n✅ Evaluation completed!")
    print(f"Result type: {type(result)}")
    
    # Show all layers found
    layers = [k for k in result.keys() if isinstance(k, str) and k.startswith('L') and len(k) == 2]
    print(f"Layers found: {sorted(layers)}")
    
    # Show HAL info
    if '_hal' in result:
        print(f"\n🎯 HAL Integration:")
        hal = result['_hal']
        print(f"  Enabled: {hal.get('enabled', False)}")
        print(f"  GPUx Ready: {hal.get('gpux_ready', False)}")
        print(f"  Bundle Hash: {hal.get('constitutional_bundle_hash', '')[:32]}...")
    
    # Show L1 if available
    if 'L1' in result:
        l1 = result['L1']
        if isinstance(l1, dict):
            print(f"\n📊 L1 Verdict:")
            print(f"  Outcome: {l1.get('decision_outcome', l1.get('verdict', 'UNKNOWN'))}")
            print(f"  Severity: {l1.get('severity', 'UNKNOWN')}")
    
    # Show GPUx layers
    for layer in ['L5', 'L6', 'L7']:
        if layer in result:
            data = result[layer]
            if isinstance(data, dict):
                print(f"\n🔧 {layer}: {data.get('title', '')}")
                if layer == 'L5':
                    print(f"  Hash: {data.get('content_hash_sha256', '')[:40]}...")
                elif layer == 'L7':
                    print(f"  Execution Authorized: {data.get('execution_authorized', False)}")
                    print(f"  Veto Triggered: {data.get('veto_triggered', False)}")
    
    print(f"\n🎉 Fixed HAL Integration Test Complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
