# fix_return_statement.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

with open(kernel_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the method start to get indentation
method_start = -1
method_indent = 0
for i in range(1680, 1720):
    if i < len(lines) and 'def get_summary(self):' in lines[i]:
        method_start = i
        method_indent = len(lines[i]) - len(lines[i].lstrip())
        print(f"Method starts at line {i+1} with indent {method_indent}")
        break

if method_start != -1:
    body_indent = method_indent + 4
    print(f"Method body indent: {body_indent} spaces")
    
    # Now we need to fix lines 1712 and 1714
    # Line 1712 is index 1711, line 1714 is index 1713
    print(f"\nChecking lines around return statement...")
    for i in range(1710, 1720):
        if i < len(lines):
            print(f"{i+1:4}: {repr(lines[i])}")
    
    # Fix line 1712 (summary["rule_coverage_summary"] = dict(coverage_summary))
    if 1711 < len(lines) and 'summary["rule_coverage_summary"]' in lines[1711]:
        current_indent = len(lines[1711]) - len(lines[1711].lstrip())
        print(f"\nLine 1712 has {current_indent} spaces, should have {body_indent} spaces")
        
        # Remove current line and insert correctly indented version
        line_content = lines[1711].strip()
        lines[1711] = ' ' * body_indent + line_content + '\n'
        print(f"Fixed line 1712 indentation")
    
    # Fix line 1714 (return summary)
    if 1713 < len(lines) and lines[1713].strip() == 'return summary':
        current_indent = len(lines[1713]) - len(lines[1713].lstrip())
        print(f"\nLine 1714 has {current_indent} spaces, should have {body_indent} spaces")
        
        lines[1713] = ' ' * body_indent + 'return summary\n'
        print(f"Fixed line 1714 indentation")
    
    # Also check if there's an empty line at 1713 that might have wrong indentation
    if 1712 < len(lines) and lines[1712].strip() == '':
        # Empty line should also have body_indent
        lines[1712] = ' ' * body_indent + '\n'
        print(f"Fixed empty line 1713 indentation")
    
    # Write back
    with open(kernel_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"\nFixed return statement and surrounding lines")
    
    # Show the fixed section
    print(f"\nFixed section (lines 1700-1720):")
    for i in range(1699, 1720):
        if i < len(lines):
            print(f"{i+1:4}: {lines[i].rstrip()}")
else:
    print("Could not find get_summary method!")