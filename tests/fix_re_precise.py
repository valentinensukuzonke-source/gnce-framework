# fix_re_precise.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

with open(kernel_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the exact location of _apply_dsa_vlop_gating function
lines = content.split('\n')
function_start = -1
function_indent = ""

for i, line in enumerate(lines):
    if 'def _apply_dsa_vlop_gating' in line:
        function_start = i
        # Get the indentation of the function definition
        function_indent = line[:len(line) - len(line.lstrip())]
        print(f"Found function at line {i+1} with indent: '{function_indent}'")
        break

if function_start != -1:
    # Find the end of the function signature/docstring
    # Look for the first line that's not a continuation of the signature or docstring
    body_start = -1
    for i in range(function_start + 1, len(lines)):
        line = lines[i]
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            continue
            
        # Skip lines that are part of docstring (triple quotes)
        if stripped.startswith('"""') or stripped.startswith("'''"):
            # Find the end of the docstring
            for j in range(i + 1, len(lines)):
                if '"""' in lines[j] or "'''" in lines[j]:
                    i = j  # Skip to end of docstring
                    break
            continue
            
        # Skip continuation lines (lines that start with the same indent as function def)
        if line.startswith(function_indent) and not line.startswith(function_indent + " " * 4):
            # This is still part of function signature (multiline)
            continue
            
        # This should be the first line of actual function body
        body_start = i
        break
    
    if body_start != -1:
        print(f"Function body starts at line {body_start+1}: '{lines[body_start][:50]}...'")
        
        # Check if import re is already there
        needs_import = True
        for i in range(body_start, min(body_start + 5, len(lines))):
            if 'import re' in lines[i]:
                print(f"import re already exists at line {i+1}")
                needs_import = False
                break
        
        if needs_import:
            # Insert import re at body_start
            lines.insert(body_start, function_indent + "    import re")
            print(f"Added import re at line {body_start+1}")
    
    # Write back
    with open(kernel_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("Fix applied!")
else:
    print("Could not find _apply_dsa_vlop_gating function!")