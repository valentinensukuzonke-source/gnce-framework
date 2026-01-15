# better_fix_1705.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

print("Better fix for line 1705...")
print("=" * 80)

# Read file
with open(kernel_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Show the function
print("Current get_summary function (lines 1673-1720):")
lines = content.split('\n')
for i in range(1672, 1720):
    if i < len(lines):
        marker = ">>>" if i == 1704 else "   "
        print(f"{marker} {i+1:4}: {lines[i]}")

print("\n" + "=" * 80)
print("ANALYSIS:")
print("=" * 80)
print("The code has two issues:")
print("1. Line 1704: '#     for key, count in self.metrics[\"rule_coverage\"].items():' - Commented out")
print("2. Lines 1705-1711: Indented as if inside the for loop, but not commented")
print("3. Line 1714: 'pass  # TEMPORARY FIX - was: return summary' - Debug code left in")

print("\n" + "=" * 80)
print("OPTION 1: Uncomment and fix the for loop")
print("OPTION 2: Comment out lines 1705-1711")
print("OPTION 3: Remove the problematic block entirely")

# Let's implement OPTION 2 (safest): Comment out lines 1705-1711
print("\n" + "=" * 80)
print("Applying OPTION 2: Comment out lines 1705-1711")
print("=" * 80)

new_lines = []
for i, line in enumerate(lines):
    if i == 1703:  # Line 1704 (0-indexed)
        # Keep this line as is (it's already commented)
        new_lines.append(line)
    elif 1704 <= i <= 1710:  # Lines 1705-1711
        # Comment out these lines
        if line.strip() and not line.strip().startswith('#'):
            # Add comment
            new_lines.append('# ' + line)
            print(f"Line {i+1}: Commented out: {line.strip()[:50]}...")
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

# Write back
with open(kernel_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print("\n✅ Fixed by commenting out problematic lines")

# Verify
print("\n" + "=" * 80)
print("Fixed function (lines 1673-1720):")
print("=" * 80)

with open(kernel_path, 'r', encoding='utf-8') as f:
    fixed_content = f.read()
    fixed_lines = fixed_content.split('\n')

for i in range(1672, 1720):
    if i < len(fixed_lines):
        print(f"{i+1:4}: {fixed_lines[i]}")