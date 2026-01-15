# auto_fix_indent.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

print("Auto-fixing indentation issues...")
print("=" * 80)

# Read file
with open(kernel_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Split into lines
lines = content.split('\n')
new_lines = []

# Track indentation
indent_stack = [0]  # Start with 0 indentation
previous_line_empty = False
fixes_applied = 0

for i, line in enumerate(lines, 1):
    stripped = line.lstrip()
    
    if not stripped:  # Empty line
        new_lines.append(line)
        previous_line_empty = True
        continue
    
    # Calculate current indentation
    current_indent = len(line) - len(stripped)
    
    # Check for common indentation errors
    if current_indent % 4 != 0 and current_indent > 0:
        # Fix to nearest multiple of 4
        fixed_indent = (current_indent // 4) * 4
        fixed_line = ' ' * fixed_indent + stripped
        if fixed_line != line:
            print(f"Line {i}: Fixed indentation {current_indent} -> {fixed_indent}")
            new_lines.append(fixed_line)
            fixes_applied += 1
        else:
            new_lines.append(line)
    elif line.startswith(' ') and not line.startswith('    '):
        # Might be 2-space or 8-space when should be 4
        # Check if it's consistent with context
        new_lines.append(line)
    else:
        new_lines.append(line)
    
    previous_line_empty = False

# Write back if fixes were applied
if fixes_applied > 0:
    # Create backup
    backup_path = kernel_path + ".indent_backup"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Write fixed version
    with open(kernel_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print(f"\n✅ Applied {fixes_applied} indentation fixes")
    print(f"✅ Backup saved to: {backup_path}")
else:
    print("\n✅ No indentation issues found")

# Verify the fix worked
print("\n" + "=" * 80)
print("Verifying line 1705...")
print("=" * 80)

with open(kernel_path, 'r', encoding='utf-8') as f:
    fixed_lines = f.readlines()

if len(fixed_lines) > 1704:
    line_1705 = fixed_lines[1704]
    print(f"Line 1705 after fix: {repr(line_1705)}")
    
    # Check if it's valid
    if line_1705.strip().startswith('parts = key.split(".")'):
        # Check indentation
        indent = len(line_1705) - len(line_1705.lstrip())
        print(f"Indentation: {indent} spaces")
        
        if indent % 4 == 0 and indent > 0:
            print("✅ Indentation looks correct")
        else:
            print(f"⚠️ Indentation might still be wrong: {indent} spaces")
            
        # Show context again
        print(f"\nContext (lines 1700-1710):")
        for i in range(1699, 1710):
            if i < len(fixed_lines):
                print(f"{i+1:4}: {fixed_lines[i].rstrip()}")
    else:
        print(f"❌ Line 1705 doesn't contain expected text")
else:
    print(f"❌ File has only {len(fixed_lines)} lines")