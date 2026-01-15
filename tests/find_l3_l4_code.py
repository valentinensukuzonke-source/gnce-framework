# find_l3_l4_code.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

print("Finding L3/L4 evaluation code in kernel.py...")
print("=" * 80)

with open(kernel_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Look for the L3/L4 section in run_gn_kernel
in_l3l4 = False
found_section = False

for i, line in enumerate(lines):
    if 'L3 + L4 — Policy evaluation' in line or 'L3/L4 — Policy evaluation' in line:
        in_l3l4 = True
        found_section = True
        print(f"\nFound L3/L4 section at line {i+1}")
        print("=" * 60)
    
    if in_l3l4:
        # Show context
        if i < len(lines) - 1 and 'L1 — Verdict' in lines[i+1]:
            in_l3l4 = False
            print("=" * 60)
            break
        
        # Print the line
        print(f"{i+1:4}: {line.rstrip()}")
        
        # Check for re usage
        if 're.' in line or ' re ' in line:
            print(f"   ^^^ Contains 're' reference")

if not found_section:
    print("Could not find L3/L4 section header")
    
# Also search for where _evaluate_policies is called
print("\n" + "=" * 80)
print("Searching for _evaluate_policies calls...")
print("=" * 80)

for i, line in enumerate(lines):
    if '_evaluate_policies' in line:
        # Show context
        start = max(0, i-2)
        end = min(len(lines), i+3)
        
        print(f"\nCall at or near line {i+1}:")
        for j in range(start, end):
            marker = ">>>" if j == i else "   "
            print(f"{marker} {j+1:4}: {lines[j].rstrip()}")