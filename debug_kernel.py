import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gnce.gn_kernel.kernel as km

print("🔍 Debugging Kernel Function")

# Check what run_gn_kernel returns
test_payload = {
    "action": "LIST_PRODUCT",
    "content": "Test",
    "user_id": "test",
    "timestamp_utc": "2026-01-14T18:00:00Z",
    "industry_id": "ECOMMERCE",
    "profile_id": "ECOMMERCE_MARKETPLACE_EU"
}

try:
    if hasattr(km, 'run_gn_kernel'):
        print("Calling run_gn_kernel...")
        result = km.run_gn_kernel(test_payload)
        print(f"Result type: {type(result)}")
        
        if isinstance(result, tuple):
            print(f"Tuple length: {len(result)}")
            for i, item in enumerate(result):
                print(f"\nItem {i}: {type(item)}")
                if isinstance(item, dict):
                    print(f"  Keys: {list(item.keys())}")
                    # Check for layer info
                    if 'layer' in item:
                        print(f"  Layer: {item['layer']}")
                else:
                    print(f"  Value: {str(item)[:100]}...")
        elif isinstance(result, dict):
            print(f"Dict keys: {list(result.keys())}")
        else:
            print(f"Result: {result}")
            
    else:
        print("run_gn_kernel not found")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
