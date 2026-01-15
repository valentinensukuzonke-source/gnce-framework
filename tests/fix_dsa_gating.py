# fix_dsa_gating.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

with open(kernel_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Track if we're in the function and need to add import
in_function = False
added_import = False
fixed_kernel_ref = False

for i, line in enumerate(lines):
    # Check if we're entering _apply_dsa_vlop_gating
    if 'def _apply_dsa_vlop_gating' in line:
        in_function = True
        print(f"Found function at line {i+1}")
    
    # Inside the function, look for where to add import re
    if in_function and not added_import:
        # Look for the first line that's not a docstring or empty
        if line.strip() and not line.strip().startswith('"""') and not line.strip().startswith("'''"):
            # This should be the first line of actual code in the function
            # Add import re right before it
            lines.insert(i, '    import re\n')
            added_import = True
            print(f"Added import re at line {i+1}")
            # Adjust indices for the rest of the loop
            continue
    
    # Fix kernel_module reference
    if 'kernel_module._utc_now_iso()' in line:
        lines[i] = line.replace('kernel_module._utc_now_iso()', '_utc_now_iso()')
        fixed_kernel_ref = True
        print(f"Fixed kernel_module reference at line {i+1}")
    
    # Check if we're leaving the function (next function definition)
    if in_function and added_import and 'def ' in line and line != lines[i] and '_apply_dsa_vlop_gating' not in line:
        in_function = False

# Write back
with open(kernel_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"\nSummary:")
print(f"- Added import re: {added_import}")
print(f"- Fixed kernel_module reference: {fixed_kernel_ref}")
if not added_import:
    print("WARNING: Could not find where to add import re in function!")