# complete_kernel_fix.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

print("COMPLETE KERNEL FIX")
print("=" * 80)
print(f"Fixing: {kernel_path}")

# Read file
with open(kernel_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Create backup
backup_path = kernel_path + ".complete_backup"
with open(backup_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"✅ Backup created: {backup_path}")

lines = content.split('\n')
new_lines = []

# Track changes
changes_made = []

# 1. Ensure import re is at the very top
if lines[0].strip() != 'import re':
    lines.insert(0, 'import re')
    changes_made.append("Added 'import re' as first line")
    print("1. ✅ Added 'import re' as first line")

# 2. Remove any inner import re from _apply_dsa_vlop_gating
in_function = False
for i, line in enumerate(lines):
    if 'def _apply_dsa_vlop_gating' in line:
        in_function = True
    
    if in_function and 'import re' in line:
        # Skip this line
        changes_made.append(f"Removed inner 'import re' at line {i+1}")
        print(f"2. ✅ Removed inner 'import re' at line {i+1}")
        continue
    
    if in_function and line.strip().startswith('def ') and 'def _apply_dsa_vlop_gating' not in line:
        in_function = False
    
    new_lines.append(line)

# If no changes were made in step 2, use original lines
if not any("Removed inner" in change for change in changes_made):
    new_lines = lines

# 3. Ensure typing imports include Pattern if needed
typing_import_found = False
for i, line in enumerate(new_lines):
    if 'from typing import' in line and 'Pattern' not in line:
        # Check if Pattern is used anywhere
        if 'Pattern' in content:
            # Add Pattern to imports
            new_lines[i] = line.replace('from typing import', 'from typing import Pattern,')
            changes_made.append("Added Pattern to typing imports")
            print("3. ✅ Added 'Pattern' to typing imports")
            typing_import_found = True
            break

# Write back
with open(kernel_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print(f"\n✅ Applied {len(changes_made)} changes")
for change in changes_made:
    print(f"  - {change}")

# Verify
print("\n" + "=" * 80)
print("VERIFICATION")
print("=" * 80)

with open(kernel_path, 'r', encoding='utf-8') as f:
    first_10 = [f.readline().strip() for _ in range(10)]

print("First 10 lines:")
for i, line in enumerate(first_10, 1):
    print(f"{i:2}: {line}")

# Count import re occurrences
import_re_count = content.count('import re')
print(f"\n'import re' occurrences: {import_re_count}")

print("\n" + "=" * 80)
print("Now test with: python working_diagnostic.py")