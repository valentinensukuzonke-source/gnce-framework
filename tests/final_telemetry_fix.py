# final_telemetry_fix.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

with open(kernel_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# We need to completely rewrite lines 1702-1710
# Current messed up state:
# 1702:         # Aggregate rule coverage
# 1703:     coverage_summary = defaultdict(dict)
# 1704:         for key, count in self.metrics["rule_coverage"].items():
# 1705:             parts = key.split(".")
# 1706:             if len(parts) == 3:
# 1707:                 regime, article, status = parts
# 1708:                 regime_key = f"{regime}.{article}"
# 1709:                 coverage_summary[regime_key]["total"] += count
# 1710:         coverage_summary[regime_key][status.lower()] = coverage_summary[regime_key].get(status.lower(), 0) + count

# Should be:
#         # Aggregate rule coverage
#         coverage_summary = defaultdict(dict)
#         for key, count in self.metrics["rule_coverage"].items():
#             parts = key.split(".")
#             if len(parts) == 3:
#                 regime, article, status = parts
#                 regime_key = f"{regime}.{article}"
#                 # Use .get() to handle missing keys
#                 coverage_summary[regime_key]["total"] = coverage_summary[regime_key].get("total", 0) + count
#                 coverage_summary[regime_key][status.lower()] = coverage_summary[regime_key].get(status.lower(), 0) + count

# Find the method start to get correct indentation
method_indent = 0
for i in range(1680, 1700):
    if i < len(lines) and 'def get_summary(self):' in lines[i]:
        method_indent = len(lines[i]) - len(lines[i].lstrip())
        print(f"Method starts at line {i+1} with indent {method_indent}")
        break

# Standard Python: method body indentation = method_indent + 4
body_indent = method_indent + 4
print(f"Method body should be indented {body_indent} spaces")

# Now replace lines 1702-1710
if 1701 < len(lines):  # Line 1702 is index 1701
    # Build the corrected block
    corrected_block = [
        ' ' * body_indent + '# Aggregate rule coverage',
        ' ' * body_indent + 'coverage_summary = defaultdict(dict)',
        ' ' * body_indent + 'for key, count in self.metrics["rule_coverage"].items():',
        ' ' * (body_indent + 4) + 'parts = key.split(".")',
        ' ' * (body_indent + 4) + 'if len(parts) == 3:',
        ' ' * (body_indent + 8) + 'regime, article, status = parts',
        ' ' * (body_indent + 8) + 'regime_key = f"{regime}.{article}"',
        ' ' * (body_indent + 8) + '# Use .get() to handle missing keys',
        ' ' * (body_indent + 8) + 'coverage_summary[regime_key]["total"] = coverage_summary[regime_key].get("total", 0) + count',
        ' ' * (body_indent + 8) + 'coverage_summary[regime_key][status.lower()] = coverage_summary[regime_key].get(status.lower(), 0) + count'
    ]
    
    # Replace lines 1702-1711 (indices 1701-1710) with corrected block
    # But keep the rest of the method after line 1710
    
    # First, let's see what we're replacing
    print(f"\nReplacing lines {1702} to {1711}:")
    for i in range(1701, min(1711, len(lines))):
        print(f"  {i+1:4}: {lines[i].rstrip()}")
    
    # Keep everything before line 1702
    new_lines = lines[:1701]
    
    # Add corrected block
    for line in corrected_block:
        new_lines.append(line + '\n')
    
    # Keep everything after line 1711
    if 1711 < len(lines):
        new_lines.extend(lines[1711:])
    
    # Write back
    with open(kernel_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"\nFixed lines {1702}-{1711}")
    
    # Show the fixed section
    print(f"\nFixed section (lines {1702}-{1712 + len(corrected_block) - 10}):")
    for i in range(1701, min(1701 + len(corrected_block) + 5, len(new_lines))):
        print(f"{i+1:4}: {new_lines[i].rstrip()}")
else:
    print("Could not find line 1702!")