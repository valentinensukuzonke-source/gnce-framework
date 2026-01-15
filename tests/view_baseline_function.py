# view_baseline_function.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

print("Reading _is_allow_baseline function...")
print("=" * 80)

with open(kernel_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and print the entire function
in_function = False
function_lines = []

for i, line in enumerate(lines):
    if 'def _is_allow_baseline' in line:
        in_function = True
    
    if in_function:
        function_lines.append((i+1, line.rstrip()))
        
        # Check if we've reached the next function
        next_line = i + 1
        if next_line < len(lines) and lines[next_line].strip().startswith('def '):
            break

print(f"Found function (lines {function_lines[0][0]}-{function_lines[-1][0]}):\n")
for line_num, line_text in function_lines:
    print(f"{line_num:4}: {line_text}")

print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)

# Extract just the function code
function_text = '\n'.join([line for _, line in function_lines])

# Check key parts
if "risk_indicators" in function_text:
    print("✅ Function checks for 'risk_indicators'")
else:
    print("❌ Function does NOT check for 'risk_indicators'")

# Check the logic
print("\nLooking for the return logic...")
for line_num, line_text in function_lines:
    if 'return' in line_text:
        print(f"Line {line_num}: {line_text}")
        