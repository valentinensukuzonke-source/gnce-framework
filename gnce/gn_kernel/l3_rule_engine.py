from concurrent.futures import ThreadPoolExecutor, as_completed

# Add this to your evaluate function:

def evaluate_regimes_parallel(regime_ids: list[str], payload: dict):
    if len(regime_ids) <= 2:
        # Sequential for small counts
        return [evaluate_single_regime(r, payload) for r in regime_ids]
    
    # Parallel for 3+
    results = []
    with ThreadPoolExecutor(max_workers=min(4, len(regime_ids))) as executor:
        futures = {
            executor.submit(evaluate_single_regime, r, payload): r 
            for r in regime_ids
        }
        for future in as_completed(futures):
            results.append(future.result())
    return results