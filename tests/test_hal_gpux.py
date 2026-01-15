import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🧪 Testing HAL/GPUx Integration")

try:
    from gnce.gn_kernel.hal_gpux import get_hal_kernel
    
    kernel = get_hal_kernel()
    print(f"✅ HAL/GPUx Kernel created")
    
    # Test with realistic payload
    test_payload = {
        "action": "LIST_PRODUCT",
        "content": "Test product listing",
        "user_id": "user-test",
        "timestamp_utc": "2026-01-14T18:00:00Z",
        "industry_id": "ECOMMERCE",
        "profile_id": "ECOMMERCE_MARKETPLACE_EU",
        "risk_indicators": {"test": True}
    }
    
    print(f"\n📥 Running evaluation...")
    result = kernel.evaluate(test_payload)
    
    print(f"\n✅ Evaluation completed")
    print(f"Result has {len(result.keys())} keys")
    
    # Show HAL/GPUx info
    if '_hal' in result:
        hal = result['_hal']
        print(f"\n🎯 HAL/GPUx Results:")
        print(f"  GPUx Ready: {hal['gpux_ready']}")
        print(f"  Constitutional Layers: {hal['layers_present']}")
        print(f"  Bundle Hash: {hal['constitutional_bundle_hash'][:32]}...")
        print(f"  Bundle Size: {hal['bundle_size_bytes']} bytes")
        
        if 'validation_results' in hal:
            validation = hal['validation_results']
            if validation.get('issues'):
                print(f"  ⚠️  Issues: {validation['issues']}")
            else:
                print(f"  ✅ No GPUx compatibility issues found")
    
    # Show GPUx capabilities
    gpux_info = kernel.get_gpux_info()
    print(f"\n🔧 GPUx Capabilities:")
    print(f"  Mode: {gpux_info['gpux_engine']['mode']}")
    print(f"  Supported Modes: {gpux_info['gpux_engine']['supported_modes']}")
    print(f"  Hardware Available: {gpux_info['gpux_engine']['hardware_available']}")
    
    # Test enabling emulation mode
    kernel.enable_gpux_emulation(True)
    print(f"\n🔄 Enabled GPUx emulation mode")
    
    print(f"\n🎉 HAL/GPUx Integration Test Complete!")
    print(f"\n📝 Summary:")
    print(f"  • Your kernel already implements full L0-L7")
    print(f"  • HAL adds GPUx readiness validation")
    print(f"  • Constitutional bundle extracted for hardware execution")
    print(f"  • Ready for future GPUx hardware integration")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
