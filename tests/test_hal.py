#!/usr/bin/env python3
"""Test HAL integration"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gnce.gn_kernel.hal import ConstitutionalBundle, GPUxEngine

def test_hal():
    """Test Hardware Abstraction Layer"""
    
    # Create sample bundle (mimicking L0-L4 outputs)
    bundle = ConstitutionalBundle(
        l0={"layer": "L0", "validated": True, "severity": "LOW"},
        l1={"layer": "L1", "verdict": "DENY", "severity": "CRITICAL"},
        l2={"layer": "L2", "input_hash": "sha256:abc123"},
        l3={"layer": "L3", "total_rules": 10, "failed": 1},
        l4={"layer": "L4", "total_policies": 10}
    )
    
    print("🧪 Testing HAL Integration")
    print(f"Bundle content hash: {bundle.get_content_hash()}")
    print(f"Bundle JSON size: {len(bundle.to_json())} bytes")
    
    # Test GPUx engine
    engine = GPUxEngine(mode='SOFTWARE')
    capabilities = engine.get_capabilities()
    
    print(f"\n🖥️  GPUx Engine Mode: {capabilities['mode']}")
    print(f"Available modes: {capabilities['available_modes']}")
    
    # Execute bundle
    result = engine.execute(bundle)
    
    print(f"\n✅ Execution Result:")
    for layer, data in result.items():
        print(f"  {layer}: {data}")
    
    print("\n🎯 HAL Integration Test Complete!")
    return True

if __name__ == "__main__":
    test_hal()
