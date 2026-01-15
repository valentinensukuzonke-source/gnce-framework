# proper_telemetry_fix.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

with open(kernel_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the get_summary method
import re

# Pattern to find the entire get_summary method
# We'll replace just the problematic section
lines = content.split('\n')

# Find start and end of get_summary method
method_start = -1
method_end = -1
indent_level = 0

for i, line in enumerate(lines):
    if 'def get_summary(self)' in line:
        method_start = i
        # Get base indentation
        indent_level = len(line) - len(line.lstrip())
        print(f"Found get_summary at line {i+1}, indentation: {indent_level}")
        
        # Find end of method (next line with same or less indentation that's not empty/comment)
        for j in range(i + 1, len(lines)):
            if lines[j].strip() and not lines[j].startswith(' ' * (indent_level + 4)):
                # This line has less indentation, so it's the end of the method
                method_end = j
                break
        if method_end == -1:
            method_end = len(lines)
        break

if method_start != -1 and method_end != -1:
    print(f"Method spans lines {method_start+1} to {method_end+1}")
    
    # Find the specific problematic lines (1700-1720 in original)
    # Actually, let me just rebuild the method with proper fix
    
    # Extract method body
    method_body = lines[method_start:method_end]
    
    # Fix the specific lines
    for i in range(len(method_body)):
        # Fix line 1703 (relative to method start)
        if 'coverage_summary = defaultdict(dict)' in method_body[i]:
            # This should have proper indentation (8 spaces/two levels)
            # The method has indent_level, inside method should be indent_level + 4
            method_body[i] = ' ' * (indent_level + 4) + 'coverage_summary = defaultdict(dict)'
            print(f"Fixed line {method_start + i + 1}")
        
        # Fix line 1710 (the actual buggy line)
        if 'coverage_summary[regime_key][status.lower()] += count' in method_body[i]:
            # Replace with safe version
            method_body[i] = ' ' * (indent_level + 12) + 'coverage_summary[regime_key][status.lower()] = coverage_summary[regime_key].get(status.lower(), 0) + count'
            print(f"Fixed buggy increment line {method_start + i + 1}")
        
        # Also fix the previous line for 'total' to be consistent
        if 'coverage_summary[regime_key]["total"] += count' in method_body[i] and i > 0:
            # Make sure 'total' key exists
            method_body[i] = ' ' * (indent_level + 12) + 'coverage_summary[regime_key]["total"] = coverage_summary[regime_key].get("total", 0) + count'
            print(f"Also fixed 'total' increment at line {method_start + i + 1}")
    
    # Replace the method in the original lines
    lines[method_start:method_end] = method_body
    
    # Write back
    with open(kernel_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("\nFixed get_summary method!")
    
    # Show the fixed lines
    print("\nFixed section (lines 1700-1715):")
    for i in range(method_start, min(method_start + 30, len(lines))):
        if i < len(lines):
            print(f"{i+1:4}: {lines[i].rstrip()}")
else:
    print("Could not find get_summary method!")
    