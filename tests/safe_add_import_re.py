# safe_add_import_re.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

print("Safely adding 'import re' to kernel.py...")
print("=" * 80)

# Read file
with open(kernel_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Check if import re already exists at top
has_import_re = False
for i, line in enumerate(lines[:20]):
    if line.strip() == 'import re':
        has_import_re = True
        print(f"✅ 'import re' already exists at line {i+1}")
        break

if not has_import_re:
    # Find where to insert (after __future__ imports if any)
    insert_at = 0
    for i, line in enumerate(lines[:10]):
        if line.strip().startswith('from __future__'):
            insert_at = i + 1
        elif line.strip() and not line.startswith('#') and 'import' not in line:
            break
    
    # Insert import re
    lines.insert(insert_at, 'import re')
    print(f"✅ Added 'import re' at line {insert_at+1}")
    
    # Write back
    with open(kernel_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
else:
    print("No change needed")

# Verify
print("\n" + "=" * 80)
print("First 10 lines after fix:")
print("=" * 80)

with open(kernel_path, 'r', encoding='utf-8') as f:
    for i in range(10):
        line = f.readline().rstrip()
        print(f"{i+1:2}: {line}")