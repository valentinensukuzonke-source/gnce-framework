# check_dsa_gating.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

print("Checking _apply_dsa_vlop_gating function...")
print("=" * 80)

with open(kernel_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the function
in_function = False
function_lines = []
for i, line in enumerate(lines):
    if 'def _apply_dsa_vlop_gating' in line:
        in_function = True
    
    if in_function:
        function_lines.append((i+1, line.rstrip()))
        
        # Check for next function
        next_line = i + 1
        if next_line < len(lines) and lines[next_line].strip().startswith('def '):
            break

print(f"Function (lines {function_lines[0][0]}-{function_lines[-1][0]}):\n")
for line_num, line_text in function_lines[:30]:  # Show first 30 lines
    print(f"{line_num:4}: {line_text}")

print("\n" + "=" * 80)
print("Checking for 'import re'...")

# Check if import re is at module level (top of file)
has_module_re = any('import re' in line and 'def ' not in line for line in lines[:100])
print(f"Module-level 'import re': {'✅ Yes' if has_module_re else '❌ No'}")

# Check if import re is in the function
has_function_re = any('import re' in line_text for _, line_text in function_lines)
print(f"In-function 'import re': {'✅ Yes' if has_function_re else '❌ No'}")

# Find where re is used
print("\nChecking where 're' is used in function...")
for line_num, line_text in function_lines:
    if 're.' in line_text or ' re ' in line_text:
        print(f"Line {line_num}: {line_text}")