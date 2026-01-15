import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
from gnce.gn_kernel.kernel import run_gn_kernel

def test_baseline():
    """Simple request - 1-2 regimes"""
    request = {
        "user_id": "user_001",
        "action": "post_text",
        "content": "Hello world",
        "user_location": "EU"
    }
    
    adra = run_gn_kernel(request)
    regimes = adra.get('domains_triggered', [])
    
    print(f"\n=== BASELINE TEST ===")
    print(f"Request: {request}")
    print(f"Regimes triggered: {regimes}")
    print(f"Count: {len(regimes)}")
    
    times = []
    for i in range(10):
        start = time.perf_counter()
        adra = run_gn_kernel(request)
        end = time.perf_counter()
        times.append((end - start) * 1000)
    
    avg = sum(times) / len(times)
    print(f"Performance: {avg:.0f}ms avg, {min(times):.0f}ms min, {max(times):.0f}ms max")
    return avg < 500

def test_multi_regime():
    """Complex request - 5-7 regimes"""
    request = {
        "user_id": "user_002",
        "action": "ai_content_decision",
        "content": "User generated content",
        "user_location": "EU",
        "contains_pii": True,
        "ai_decision": True,
        "financial_transaction": False
    }
    
    adra = run_gn_kernel(request)
    regimes = adra.get('domains_triggered', [])
    
    print(f"\n=== MULTI-REGIME TEST ===")
    print(f"Request keys: {list(request.keys())}")
    print(f"Regimes triggered: {regimes}")
    print(f"Count: {len(regimes)}")
    
    times = []
    for i in range(10):
        start = time.perf_counter()
        adra = run_gn_kernel(request)
        end = time.perf_counter()
        times.append((end - start) * 1000)
    
    avg = sum(times) / len(times)
    print(f"Performance: {avg:.0f}ms avg, {min(times):.0f}ms min, {max(times):.0f}ms max")
    return avg < 1000

def test_worst_case():
    """Worst case - 8+ regimes"""
    request = {
        "user_id": "user_003",
        "action": "ai_financial_health_decision",
        "user_location": "EU",
        "contains_phi": True,
        "contains_pii": True,
        "financial_transaction": True,
        "payment_card_data": True,
        "ai_decision": True,
        "sox_entity": True,
        "aml_screening": True,
        "hipaa_entity": True
    }
    
    adra = run_gn_kernel(request)
    regimes = adra.get('domains_triggered', [])
    
    print(f"\n=== WORST CASE TEST ===")
    print(f"Request keys: {list(request.keys())}")
    print(f"Regimes triggered: {regimes}")
    print(f"Count: {len(regimes)}")
    
    times = []
    for i in range(10):
        start = time.perf_counter()
        adra = run_gn_kernel(request)
        end = time.perf_counter()
        times.append((end - start) * 1000)
    
    avg = sum(times) / len(times)
    print(f"Performance: {avg:.0f}ms avg, {min(times):.0f}ms min, {max(times):.0f}ms max")
    return avg < 2000

if __name__ == "__main__":
    print("\n=== GNCE Performance & Regime Trigger Test ===\n")
    
    baseline_ok = test_baseline()
    multi_ok = test_multi_regime()
    worst_ok = test_worst_case()
    
    print(f"\n=== Final Results ===")
    print(f"Baseline: {'PASS ' if baseline_ok else 'FAIL '}")
    print(f"Multi-regime: {'PASS ' if multi_ok else 'FAIL '}")
    print(f"Worst case: {'PASS ' if worst_ok else 'FAIL '}")
