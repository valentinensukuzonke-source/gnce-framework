# fix_re_import.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

print(f"Fixing 're' import in: {kernel_path}")
print("=" * 80)

with open(kernel_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Check if import re exists at module level
if 'import re' in content:
    # Find where it is
    lines = content.split('\n')
    for i, line in enumerate(lines[:50]):  # Check first 50 lines
        if 'import re' in line and 'def ' not in line:
            print(f"✅ 'import re' found at module level (line {i+1})")
            print(f"   Content: {line}")
            break
    else:
        print("❌ 'import re' exists but not at module level")
        
        # Check if it's inside a function
        for i, line in enumerate(lines):
            if 'import re' in line and 'def ' in lines[i-1] if i > 0 else False:
                print(f"⚠️ 'import re' is inside a function at line {i+1}")
                print(f"   Function starts at line {i}: {lines[i-1]}")
                
                # Move it to module level
                print("\nMoving 'import re' to module level...")
                
                # Find all imports at the top
                import_section_end = 0
                for j, line in enumerate(lines[:30]):
                    if line.strip() and not line.strip().startswith(('import ', 'from ', '#', '"""', "'''")):
                        import_section_end = j
                        break
                
                # Insert import re at the right place
                if import_section_end > 0:
                    # Remove from function
                    lines[i] = line.replace('import re', '').rstrip()
                    if not lines[i].strip():
                        lines[i] = ''
                    
                    # Add to imports section
                    lines.insert(import_section_end, 'import re')
                    
                    # Write back
                    new_content = '\n'.join(lines)
                    with open(kernel_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    print(f"✅ Moved 'import re' to line {import_section_end+1}")
else:
    print("❌ 'import re' not found in file")
    print("\nAdding 'import re' at module level...")
    
    lines = content.split('\n')
    
    # Find where to insert (after other imports)
    insert_line = 0
    for i, line in enumerate(lines[:30]):
        if line.strip().startswith(('import ', 'from ')):
            insert_line = i + 1
        elif line.strip() and not line.startswith(('#', '"""', "'''")):
            break
    
    # Insert import re
    lines.insert(insert_line, 'import re')
    
    # Write back
    new_content = '\n'.join(lines)
    with open(kernel_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Added 'import re' at line {insert_line+1}")

print("\n" + "=" * 80)
print("Verification check...")
print("=" * 80)

# Verify the fix
with open(kernel_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Check first 30 lines for import re
found = False
for i, line in enumerate(lines[:30]):
    if 'import re' in line and 'def ' not in line:
        print(f"✅ Verified: 'import re' at module level (line {i+1})")
        found = True
        break

if not found:
    print("❌ 'import re' not found at module level after fix")
    