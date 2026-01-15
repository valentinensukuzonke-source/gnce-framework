# check_current_state.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

with open(kernel_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Current state around line 1714:")
for i in range(1700, 1730):
    if i < len(lines):
        print(f"{i+1:4}: {repr(lines[i])}")

# Let me find the actual get_summary method
print("\n\nSearching for get_summary method...")
for i, line in enumerate(lines):
    if 'def get_summary' in line:
        print(f"Found at line {i+1}: {line.strip()}")
        # Show next 30 lines
        print(f"Method body (lines {i+2} to {i+32}):")
        for j in range(i+1, min(i+32, len(lines))):
            indent = len(lines[j]) - len(lines[j].lstrip())
            print(f"  {j+1:4} [{indent} spaces]: {lines[j].rstrip()}")
        break