# fix_baseline_direct.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"
backup_path = kernel_path + ".backup2"

print(f"Fixing _is_allow_baseline in: {kernel_path}")

# Read the file
with open(kernel_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Create backup
with open(backup_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"✅ Backup created: {backup_path}")

# Define the CORRECTED version
corrected_function = '''def _is_allow_baseline(payload: Dict[str, Any]) -> bool:
    """
    Baseline mode is allowed ONLY when no regime-specific context is present.
    CRITICAL FIX: Always return False if any compliance signals exist.
    
    SAFETY FIRST: If any doubt, force full evaluation.
    """
    if not isinstance(payload, dict):
        return True  # Default to baseline for non-dicts

    # CRITICAL SAFETY CHECK 1: If ANY risk indicators key exists, force full evaluation
    if "risk_indicators" in payload:
        # Even if risk_indicators dict is empty, we should evaluate
        # because the presence of the key indicates this is a compliance-aware request
        return False
    
    # CRITICAL SAFETY CHECK 2: Force evaluation for ANY compliance profile
    compliance_profiles = [
        "dsa", "dma_profile", "ai_profile", "platform_behavior",
        "pci_profile", "hipaa_profile", "sec_17a4_profile",
        "finra_profile", "sox_profile", "data_types", "export"
    ]
    
    for profile in compliance_profiles:
        if profile in payload and payload[profile]:
            # Profile exists and is not empty/false
            return False
    
    # CRITICAL SAFETY CHECK 3: Force evaluation for content-related actions
    action = str(payload.get("action", "")).upper()
    content_actions = [
        "POST_CONTENT", "LIST_PRODUCT", "EXPORT_DATA", "PROCESS_TRANSACTION",
        "ACCESS_DATA", "MODIFY_DATA", "DELETE_DATA", "QUERY_DATA",
        "CREATE_ORDER", "CANCEL_ORDER", "REFUND", "SHIP_PRODUCT"
    ]
    
    if action in content_actions:
        return False
    
    # CRITICAL SAFETY CHECK 4: Force evaluation if content exists
    if payload.get("content"):
        return False
    
    # CRITICAL SAFETY CHECK 5: Force evaluation for VLOP/enterprise signals
    meta = payload.get("meta") or {}
    if meta:
        # If meta exists (even empty), likely a compliance-aware request
        return False
    
    # CRITICAL SAFETY CHECK 6: Force evaluation for any governance context
    if payload.get("governance") or payload.get("audit"):
        return False
    
    # ONLY allow baseline for TRULY empty/neutral payloads
    # This should be very rare - most real requests should go through full evaluation
    empty_keys = [k for k in payload.keys() if k not in ["timestamp_utc", "user_id", "request_id"]]
    if not empty_keys:
        return True
    
    # Default to False (force evaluation) when in doubt
    return False'''

# Find and replace the function
import re

# Pattern to find the function
pattern = r'def _is_allow_baseline\(payload: Dict\[str, Any\]\) -> bool:.*?(?=\n\s*def |\Z)'
match = re.search(pattern, content, re.DOTALL)

if match:
    print(f"✅ Found _is_allow_baseline function (length: {len(match.group(0))} chars)")
    
    # Replace it
    new_content = content[:match.start()] + corrected_function + content[match.end():]
    
    # Write the fixed version
    with open(kernel_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Successfully replaced _is_allow_baseline with corrected version")
    
    # Show what was changed
    print("\n" + "=" * 80)
    print("KEY CHANGES APPLIED:")
    print("=" * 80)
    print("1. Changed: 'if risk or isinstance(risk, dict):' → 'if \"risk_indicators\" in payload:'")
    print("   REASON: Presence of risk_indicators key ALWAYS triggers evaluation")
    print("\n2. Added: 'if meta:' → returns False")
    print("   REASON: Any meta object indicates compliance-aware request")
    print("\n3. Added: 'if payload.get(\"governance\") or payload.get(\"audit\"):' → returns False")
    print("   REASON: Governance/audit signals require full evaluation")
    print("\n4. Changed final return logic:")
    print("   OLD: return True (too permissive)")
    print("   NEW: Checks for truly empty payloads, defaults to False")
    
else:
    print("❌ Could not find _is_allow_baseline function with regex")
    print("Trying line-by-line replacement...")
    
    # Fallback: line-by-line replacement
    lines = content.split('\n')
    new_lines = []
    replacing = False
    replaced = False
    
    for line in lines:
        if 'def _is_allow_baseline' in line:
            replacing = True
            new_lines.append(corrected_function)
            replaced = True
            continue
        
        if replacing:
            # Skip lines until we hit the next function
            if line.strip().startswith('def ') and 'def _is_allow_baseline' not in line:
                replacing = False
                new_lines.append(line)
            # Skip the lines we're replacing
            continue
        
        new_lines.append(line)
    
    if replaced:
        new_content = '\n'.join(new_lines)
        with open(kernel_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ Replaced function using line-by-line method")
    else:
        print("❌ Failed to replace function")

print("\n" + "=" * 80)
print("TEST THE FIX")
print("=" * 80)
print("Now run: python working_diagnostic.py")
print("Expected: Harmful content should now trigger DENY verdict")