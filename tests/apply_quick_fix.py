# apply_quick_fix.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"
backup_path = kernel_path + ".backup"

print(f"Backing up kernel.py to: {backup_path}")

# Read current kernel.py
with open(kernel_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Create backup
with open(backup_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("✅ Backup created")

# Check and fix import re issue
if 'import re' in content:
    print("✅ 'import re' already present in file")
else:
    print("⚠️ 'import re' not found in file")
    
    # Look for _apply_dsa_vlop_gating function
    if 'def _apply_dsa_vlop_gating' in content:
        print("Found _apply_dsa_vlop_gating function")
        
        # Simple fix: add import re at the beginning of the function
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            fixed_lines.append(line)
            if 'def _apply_dsa_vlop_gating' in line:
                # Add import re on the next line
                fixed_lines.append('    import re')
        
        content = '\n'.join(fixed_lines)
        
        # Write fixed version
        with open(kernel_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Added 'import re' to _apply_dsa_vlop_gating function")

print("\nFixing _is_allow_baseline function...")

# Define the fixed version
fixed_baseline_function = '''def _is_allow_baseline(payload: Dict[str, Any]) -> bool:
    """
    Baseline mode is allowed ONLY when no regime-specific context is present.
    CRITICAL FIX: Always return False if any compliance signals exist.
    """
    if not isinstance(payload, dict):
        return True

    # CRITICAL: If ANY risk indicators exist, force full evaluation
    if "risk_indicators" in payload:
        risk = payload.get("risk_indicators", {})
        # Even an empty dict means we should evaluate
        if risk or isinstance(risk, dict):
            return False
    
    # Force evaluation for ANY compliance profile
    compliance_profiles = [
        "dsa", "dma_profile", "ai_profile", "platform_behavior",
        "pci_profile", "hipaa_profile", "sec_17a4_profile",
        "finra_profile", "sox_profile", "data_types"
    ]
    
    for profile in compliance_profiles:
        if profile in payload:
            return False
    
    # Force evaluation for content-related actions
    action = str(payload.get("action", "")).upper()
    if action in ["POST_CONTENT", "LIST_PRODUCT", "EXPORT_DATA", "PROCESS_TRANSACTION"]:
        return False
    
    # Force evaluation if content exists
    if payload.get("content"):
        return False
    
    # Force evaluation for VLOP signals
    meta = payload.get("meta") or {}
    if meta.get("is_vlop") or meta.get("vlop"):
        return False
    
    # Only allow baseline for truly empty/neutral payloads
    return True'''

# Read the file again to find and replace the function
with open(kernel_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the _is_allow_baseline function
in_function = False
start_line = -1
end_line = -1
function_indent = ""

for i, line in enumerate(lines):
    if 'def _is_allow_baseline' in line:
        in_function = True
        start_line = i
        # Get the indentation level
        function_indent = line[:len(line) - len(line.lstrip())]
    
    if in_function and i > start_line:
        # Check if we've reached the next function or end of function
        stripped = line.lstrip()
        if stripped.startswith('def ') or (stripped == '' and i > start_line + 10):
            # Check if next non-empty line starts a new function
            for j in range(i+1, min(i+3, len(lines))):
                if lines[j].strip().startswith('def '):
                    end_line = i
                    in_function = False
                    break
        
        # Also end if we hit a line with less indentation (but not empty)
        if line.strip() and not line.startswith(function_indent) and i > start_line:
            end_line = i
            in_function = False

if end_line == -1 and start_line != -1:
    end_line = len(lines)

# Replace the function
if start_line != -1 and end_line != -1:
    print(f"Found _is_allow_baseline at lines {start_line+1}-{end_line+1}")
    
    # Replace with fixed version
    new_lines = lines[:start_line] + [fixed_baseline_function + '\n'] + lines[end_line:]
    
    # Write back
    with open(kernel_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ Successfully replaced _is_allow_baseline function")
else:
    print("❌ Could not find _is_allow_baseline function in the file")

print("\n" + "=" * 80)
print("QUICK FIX APPLIED")
print("=" * 80)
print("1. Created backup of kernel.py")
print("2. Added 'import re' if missing")
print("3. Replaced _is_allow_baseline with fixed version")
print("\nNow run: python working_diagnostic.py")