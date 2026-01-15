# simple_fix.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

print("SIMPLE FIX: Removing inner 'import re'")
print("=" * 80)

# Read file
with open(kernel_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Split into lines
lines = content.split('\n')

# Process line by line
output = []
in_target_function = False
removed = False

for i, line in enumerate(lines, 1):
    # Check if we're in the target function
    if 'def _apply_dsa_vlop_gating' in line:
        in_target_function = True
        print(f"Found function at line {i}")
    
    # Remove 'import re' only if inside the function
    if in_target_function and 'import re' in line and not removed:
        print(f"REMOVING at line {i}: {line}")
        removed = True
        continue  # Skip this line
    
    # Check if we've left the function
    if in_target_function and line.strip().startswith('def ') and 'def _apply_dsa_vlop_gating' not in line:
        in_target_function = False
    
    output.append(line)

# Write back if we removed something
if removed:
    with open(kernel_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    print(f"\n✅ Fixed! Removed inner 'import re'")
    
    # Verify
    with open(kernel_path, 'r') as f:
        final_content = f.read()
    
    if 'import re' in final_content:
        # Count occurrences
        count = final_content.count('import re')
        print(f"✅ 'import re' still appears {count} times (module level is OK)")
    else:
        print("❌ 'import re' completely removed - need to add it back at module level!")
        
else:
    print(f"\n❌ Could not find 'import re' inside _apply_dsa_vlop_gating")
    print("The file might already be fixed or the structure changed.")
    
    # Show what we found
    print("\nSearching for 'import re' in file...")
    for i, line in enumerate(lines, 1):
        if 'import re' in line:
            print(f"Line {i}: {line.strip()}")