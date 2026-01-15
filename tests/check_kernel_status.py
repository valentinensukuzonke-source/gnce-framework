# check_kernel_status.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

print(f"Checking kernel.py at: {kernel_path}")
print("=" * 80)

if os.path.exists(kernel_path):
    with open(kernel_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Check for critical functions
    functions_to_check = [
        '_is_allow_baseline',
        '_apply_dsa_vlop_gating',
        'run_gn_kernel'
    ]
    
    print(f"Total lines: {len(lines)}")
    
    for func in functions_to_check:
        found = False
        for i, line in enumerate(lines):
            if f'def {func}' in line:
                print(f"\n✅ Found {func} at line {i+1}")
                # Show a few lines after it
                for j in range(i, min(i+5, len(lines))):
                    print(f"  {j+1}: {lines[j].rstrip()}")
                found = True
                break
        
        if not found:
            print(f"\n❌ {func} not found in kernel.py")
    
    # Check for import re in _apply_dsa_vlop_gating
    print("\n" + "=" * 80)
    print("Checking for 'import re' in _apply_dsa_vlop_gating...")
    
    in_dsa_function = False
    for i, line in enumerate(lines):
        if 'def _apply_dsa_vlop_gating' in line:
            in_dsa_function = True
            print(f"\nFound _apply_dsa_vlop_gating at line {i+1}")
        
        if in_dsa_function:
            if 'import re' in line:
                print(f"✅ Found 'import re' at line {i+1}")
                break
            
            # If we reach the next function
            if line.strip().startswith('def ') and 'def _apply_dsa_vlop_gating' not in line:
                in_dsa_function = False
    
    # Show _is_allow_baseline function
    print("\n" + "=" * 80)
    print("Checking _is_allow_baseline function...")
    
    in_baseline = False
    baseline_lines = []
    for i, line in enumerate(lines):
        if 'def _is_allow_baseline' in line:
            in_baseline = True
        
        if in_baseline:
            baseline_lines.append((i+1, line.rstrip()))
            
            # Check if we've reached the next function
            if line.strip().startswith('def ') and 'def _is_allow_baseline' not in line:
                in_baseline = False
                break
    
    if baseline_lines:
        print(f"\n_is_allow_baseline function (lines {baseline_lines[0][0]}-{baseline_lines[-1][0]}):")
        for line_num, line_text in baseline_lines[:20]:  # Show first 20 lines
            print(f"{line_num:4}: {line_text}")
    else:
        print("❌ _is_allow_baseline function not found!")
        
else:
    print(f"❌ kernel.py not found at: {kernel_path}")