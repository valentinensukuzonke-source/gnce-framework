# final_comprehensive_fix.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

print("FINAL COMPREHENSIVE FIX")
print("=" * 80)

# Read file
with open(kernel_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Create backup
backup_path = kernel_path + ".final_backup"
with open(backup_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"✅ Backup created: {backup_path}")

lines = content.split('\n')
new_lines = []
changes = []

# Fix 1: Ensure import re at top
if lines[0].strip() != 'import re':
    lines.insert(0, 'import re')
    changes.append("Added 'import re' as first line")

# Process each line
in_problem_function = False
for i, line in enumerate(lines):
    # Fix 2: Remove inner import re from _apply_dsa_vlop_gating
    if 'def _apply_dsa_vlop_gating' in line:
        in_problem_function = True
    
    if in_problem_function and 'import re' in line:
        # Skip this line
        changes.append(f"Removed inner 'import re' from _apply_dsa_vlop_gating")
        continue
    
    if in_problem_function and line.strip().startswith('def ') and 'def _apply_dsa_vlop_gating' not in line:
        in_problem_function = False
    
    # Fix 3: Fix line 1705 indentation issue
    if i == 1704 and 'parts = key.split(".")' in line:
        # This should be commented out or properly indented
        # Let's comment it out for safety
        if not line.strip().startswith('#'):
            line = '# ' + line
            changes.append("Commented out line 1705")
    
    # Fix 4: Check for other obvious indentation errors
    stripped = line.lstrip()
    if stripped and line.startswith(' ') and not line.startswith('    '):
        # Fix 2-space or irregular indentation to 4-space
        indent_level = (len(line) - len(stripped) + 3) // 4  # Round up to nearest 4
        fixed_line = ' ' * (indent_level * 4) + stripped
        if fixed_line != line:
            line = fixed_line
            changes.append(f"Fixed indentation at line {i+1}")
    
    new_lines.append(line)

# Write back
with open(kernel_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print(f"\n✅ Applied {len(changes)} changes:")
for change in changes:
    print(f"  - {change}")

print("\n" + "=" * 80)
print("Now test with: python working_diagnostic.py")