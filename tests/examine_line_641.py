# examine_line_641.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

print(f"Examining line 641 in: {kernel_path}")
print("=" * 80)

with open(kernel_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Show context around line 641
start = max(0, 635)
end = min(len(lines), 650)

print(f"Lines {start+1} to {end+1}:\n")
for i in range(start, end):
    marker = ">>>" if i == 640 else "   "  # Line 641 is index 640
    print(f"{marker} {i+1:4}: {lines[i].rstrip()}")

# Show the function signature
print("\n" + "=" * 80)
print("Finding the function signature...")
print("=" * 80)

for i, line in enumerate(lines):
    if 'def _apply_dsa_vlop_gating' in line:
        print(f"Function found at line {i+1}:")
        # Show 10 lines after
        for j in range(i, min(i+15, len(lines))):
            print(f"{j+1:4}: {lines[j].rstrip()}")
        break