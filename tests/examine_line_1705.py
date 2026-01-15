# examine_line_1705.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

print("Examining line 1705 and surrounding code...")
print("=" * 80)

with open(kernel_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Show more context
start_line = max(0, 1695)
end_line = min(len(lines), 1715)

print(f"Lines {start_line+1} to {end_line+1}:\n")
for i in range(start_line, end_line):
    line = lines[i].rstrip()
    marker = ">>> INDENTATION ERROR" if i == 1704 else ""
    print(f"{i+1:4}: {line} {marker}")

# Show the function this is in
print("\n" + "=" * 80)
print("Finding which function contains line 1705...")
print("=" * 80)

current_function = None
function_start = 0

for i, line in enumerate(lines[:1800]):
    if line.strip().startswith('def '):
        current_function = line.strip()
        function_start = i
    
    if i == 1704 and current_function:
        # Show the function
        print(f"Line 1705 is in function: {current_function}")
        print(f"Function starts at line {function_start+1}")
        
        # Show function start
        print(f"\nFunction start (lines {function_start+1}-{function_start+10}):")
        for j in range(function_start, min(function_start + 10, len(lines))):
            print(f"{j+1:4}: {lines[j].rstrip()}")
        break

if not current_function:
    print("❌ Could not find function containing line 1705")