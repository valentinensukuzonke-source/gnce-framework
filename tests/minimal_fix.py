# minimal_fix.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

with open(kernel_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix the specific line
for i, line in enumerate(lines):
    # Find the buggy line
    if 'coverage_summary[regime_key][status.lower()] += count' in line:
        print(f"Found buggy line at {i+1}")
        
        # Get the indentation
        indent = line[:len(line) - len(line.lstrip())]
        
        # Replace with safe version using .get()
        lines[i] = f'{indent}coverage_summary[regime_key][status.lower()] = coverage_summary[regime_key].get(status.lower(), 0) + count\n'
        print(f"Fixed line {i+1}")
        
        # Also fix the 'total' line if it exists nearby
        for j in range(max(0, i-2), min(len(lines), i+1)):
            if 'coverage_summary[regime_key]["total"] += count' in lines[j]:
                indent2 = lines[j][:len(lines[j]) - len(lines[j].lstrip())]
                lines[j] = f'{indent2}coverage_summary[regime_key]["total"] = coverage_summary[regime_key].get("total", 0) + count\n'
                print(f"Also fixed 'total' line at {j+1}")
        
        break

# Write back
with open(kernel_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\nMinimal fix applied!")