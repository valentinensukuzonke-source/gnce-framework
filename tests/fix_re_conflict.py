# fix_re_conflict.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

print(f"Fixing re conflict in: {kernel_path}")
print("=" * 80)

with open(kernel_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Create backup
backup_path = kernel_path + ".backup3"
with open(backup_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"✅ Backup created: {backup_path}")

# Find the _apply_dsa_vlop_gating function and remove the inner import re
lines = content.split('\n')
new_lines = []
skip_next_empty = False

for i, line in enumerate(lines):
    # Check if this is the line with import re inside the function
    if 'import re' in line and i > 0 and 'def _apply_dsa_vlop_gating' in '\n'.join(lines[max(0,i-10):i]):
        print(f"Found 'import re' inside function at line {i+1}: {line}")
        
        # Remove this line (don't add it to new_lines)
        # But check if it's the only thing on the line
        if line.strip() == 'import re':
            print(f"Removing inner 'import re' at line {i+1}")
            skip_next_empty = True  # Skip next line if it's empty
            continue
        
        # If there are other imports with it, keep them but remove 're'
        if 'import' in line and ',' in line:
            # Like: import re, json, os
            imports = [imp.strip() for imp in line.replace('import', '').split(',')]
            imports = [imp for imp in imports if imp != 're']
            if imports:
                new_line = 'import ' + ', '.join(imports)
                new_lines.append(new_line)
                print(f"Modified line {i+1}: {new_line}")
            else:
                # All imports were 're', skip the line entirely
                continue
        else:
            # Just 'import re', skip it
            continue
    
    # Skip empty line after removed import
    if skip_next_empty and line.strip() == '':
        skip_next_empty = False
        continue
    
    new_lines.append(line)

# Write back
new_content = '\n'.join(new_lines)
with open(kernel_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("\n✅ Removed inner 'import re' from _apply_dsa_vlop_gating function")
print("   (It's already imported at module level, line 10)")

# Verify
print("\n" + "=" * 80)
print("Verification...")
print("=" * 80)

with open(kernel_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Count import re occurrences
import_re_count = sum(1 for line in lines if 'import re' in line)
print(f"Total 'import re' occurrences: {import_re_count}")

# Check module level import
module_level = False
for i, line in enumerate(lines[:30]):
    if 'import re' in line and 'def ' not in line:
        module_level = True
        print(f"✅ Module-level 'import re' at line {i+1}")
        break

if not module_level:
    print("❌ No module-level 'import re' found!")

# Check if function still has import re
function_has_import = False
in_function = False
for i, line in enumerate(lines):
    if 'def _apply_dsa_vlop_gating' in line:
        in_function = True
    
    if in_function and 'import re' in line:
        function_has_import = True
        print(f"❌ Function still has 'import re' at line {i+1}")
        break
    
    if in_function and line.strip().startswith('def ') and 'def _apply_dsa_vlop_gating' not in line:
        in_function = False

if not function_has_import:
    print("✅ Function no longer has inner 'import re'")