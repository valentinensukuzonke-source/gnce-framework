# test_evaluation_pipeline.py
import sys
import os

# Setup paths
gnce_root = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC"
sys.path.insert(0, os.path.join(gnce_root, "gnce"))
sys.path.insert(0, os.path.join(gnce_root, "gnce", "gn_kernel"))

print("Testing evaluation pipeline directly...")
print("=" * 80)

try:
    # Try to import the _evaluate_policies function directly
    import importlib.util
    kernel_path = os.path.join(gnce_root, "gnce", "gn_kernel", "kernel.py")
    spec = importlib.util.spec_from_file_location("kernel", kernel_path)
    kernel = importlib.util.module_from_spec(spec)
    
    # We need to set up the module namespace
    import json
    import hashlib
    from datetime import datetime, timezone, timedelta
    from typing import Any, Dict, List, Tuple, Optional, Set, Union, Callable, Collection
    import uuid
    import copy
    import re  # This is critical!
    
    # Add these to the kernel module's namespace before execution
    kernel.__dict__.update({
        'json': json,
        'hashlib': hashlib,
        'datetime': datetime,
        'timezone': timezone,
        'timedelta': timedelta,
        'Any': Any,
        'Dict': Dict,
        'List': List,
        'Tuple': Tuple,
        'Optional': Optional,
        'Set': Set,
        'Union': Union,
        'Callable': Callable,
        'Collection': Collection,
        'uuid': uuid,
        'copy': copy,
        're': re,
    })
    
    # Now execute
    spec.loader.exec_module(kernel)
    print("✅ Kernel module loaded")
    
    # Test _evaluate_policies directly
    test_payload = {
        "action": "POST_CONTENT",
        "content": "harmful test",
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
    
    print(f"\nCalling _evaluate_policies directly...")
    policies, summary = kernel._evaluate_policies(test_payload, enabled_regimes=["DSA"])
    
    print(f"Result: {len(policies)} policies, summary: {summary}")
    
    if policies:
        print("\nPolicies found:")
        for i, p in enumerate(policies[:5]):
            print(f"{i+1}. {p.get('regime')} - {p.get('article')} - {p.get('status')}")
    else:
        print("\n❌ No policies returned!")
        
        # Try with all regimes
        print("\nTrying with all regimes enabled...")
        policies2, summary2 = kernel._evaluate_policies(test_payload, enabled_regimes=None)
        print(f"All regimes: {len(policies2)} policies")
        
        if policies2:
            print("First few policies:")
            for i, p in enumerate(policies2[:3]):
                print(f"{i+1}. {p.get('regime')} - {p.get('article')} - {p.get('status')}")
                
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()