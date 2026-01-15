# re_add_import_re.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

print("Adding 'import re' back to kernel.py...")
print("=" * 80)

# Read file
with open(kernel_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Check if import re already exists
has_import_re = False
for i, line in enumerate(lines[:20]):
    if line.strip() == 'import re':
        has_import_re = True
        print(f"✅ 'import re' already exists at line {i+1}")
        break

if not has_import_re:
    # Find where to insert (after __future__ import)
    insert_at = 0
    for i, line in enumerate(lines[:10]):
        if 'from __future__ import annotations' in line:
            insert_at = i + 1
            break
    
    # Insert import re
    lines.insert(insert_at, 'import re')
    print(f"✅ Added 'import re' at line {insert_at+1}")
    
    # Write back
    with open(kernel_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
else:
    print("No change needed")

# Also check for inner import re in _apply_dsa_vlop_gating
print("\n" + "=" * 80)
print("Checking for inner 'import re' in _apply_dsa_vlop_gating...")
print("=" * 80)

in_function = False
found_inner = False
for i, line in enumerate(lines):
    if 'def _apply_dsa_vlop_gating' in line:
        in_function = True
    
    if in_function and 'import re' in line:
        print(f"❌ Found inner 'import re' at line {i+1}: {line.strip()}")
        found_inner = True
        
        # Remove it
        lines[i] = line.replace('import re', '').rstrip()
        if not lines[i].strip():
            lines[i] = ''
        print(f"✅ Removed inner 'import re'")
    
    if in_function and line.strip().startswith('def ') and 'def _apply_dsa_vlop_gating' not in line:
        in_function = False

if not found_inner:
    print("✅ No inner 'import re' found")

# Write back if we made changes
if not has_import_re or found_inner:
    with open(kernel_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

# Verify
print("\n" + "=" * 80)
print("Final check - First 15 lines:")
print("=" * 80)

with open(kernel_path, 'r', encoding='utf-8') as f:
    for i in range(15):
        line = f.readline().rstrip()
        print(f"{i+1:2}: {line}")