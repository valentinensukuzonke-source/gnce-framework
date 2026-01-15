# fix_kernel_future_import.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

with open(kernel_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and move the __future__ import to line 1
future_line = None
for i, line in enumerate(lines):
    if 'from __future__ import annotations' in line:
        future_line = i
        break

if future_line and future_line > 0:
    print(f"Moving __future__ import from line {future_line + 1} to line 1")
    
    # Remove the line from its current position
    future_line_content = lines.pop(future_line)
    
    # Insert it at the beginning (before any imports or code)
    lines.insert(0, future_line_content)
    
    # Write back to file
    with open(kernel_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("Fixed! The __future__ import is now at the beginning.")
    
    # Show first 5 lines to verify
    print("\nFirst 5 lines after fix:")
    for i, line in enumerate(lines[:5], 1):
        print(f"{i:3}: {line.rstrip()}")
else:
    print("__future__ import not found or already at line 1")