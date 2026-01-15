# simple_fix_line_1714.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

with open(kernel_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Check line 1714 (index 1713)
if 1713 < len(lines):
    print(f"Line 1714 before: {repr(lines[1713])}")
    
    # The line has "return summary" but wrong indentation
    # We need to find the correct indentation by looking at the method
    # Find the method start
    for i in range(1713, 1650, -1):  # Search upward
        if i >= 0 and 'def get_summary' in lines[i]:
            method_indent = len(lines[i]) - len(lines[i].lstrip())
            body_indent = method_indent + 4
            print(f"Found method at line {i+1}, method indent: {method_indent}, body indent: {body_indent}")
            
            # Fix line 1714
            lines[1713] = ' ' * body_indent + 'return summary\n'
            print(f"Fixed line 1714: {repr(lines[1713])}")
            
            # Also check and fix line 1712 if needed
            if 1711 < len(lines) and 'summary["rule_coverage_summary"]' in lines[1711]:
                current_indent = len(lines[1711]) - len(lines[1711].lstrip())
                if current_indent != body_indent:
                    lines[1711] = ' ' * body_indent + lines[1711].lstrip()
                    print(f"Also fixed line 1712 indentation")
            
            break

# Write back
with open(kernel_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\nFile fixed.")