import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gnce.gn_kernel.kernel as km

print("Testing minimal working payload...")

# Based on your successful earlier test
working_payload = {
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

try:
    result = km.run_gn_kernel(working_payload)
    print(f"✅ Kernel executed successfully!")
    print(f"Result type: {type(result)}")
    print(f"Number of keys: {len(result.keys())}")
    
    # Show L0-L7 keys
    layer_keys = [k for k in result.keys() if any(f'L{i}' in k for i in range(8))]
    print(f"Layer keys found: {layer_keys}")
    
    # Check for patent-relevant fields
    patent_fields = []
    for key in result.keys():
        if any(term in key.lower() for term in ['policy', 'article', 'clause', 'rationale', 'veto', 'token', 'crypt', 'drift']):
            patent_fields.append(key)
    
    print(f"Patent-relevant fields: {patent_fields[:10]}...")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
