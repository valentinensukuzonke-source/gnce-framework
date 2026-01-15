# check_and_fix_indentation.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

with open(kernel_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Checking lines 1695-1715...")
for i in range(1694, 1715):  # Python uses 0-indexed, so 1694 = line 1695
    if i < len(lines):
        print(f"{i+1:4}: {repr(lines[i])}")

# The issue is line 1704 has wrong indentation
# Let me check what indentation level it SHOULD have
print("\nFinding proper indentation...")

# Look for the method start
method_indent = 0
for i in range(1694, 1700):
    if i < len(lines) and 'def get_summary' in lines[i]:
        method_indent = len(lines[i]) - len(lines[i].lstrip())
        print(f"Method starts at line {i+1} with indent {method_indent}")
        break

# Inside a method, code should be indented by method_indent + 4 (or 8)
print(f"\nExpected indentation for method body: {method_indent + 4} spaces")

# Check line 1703 and 1704
if 1702 < len(lines):  # Line 1703 is index 1702
    line_1703 = lines[1702]
    indent_1703 = len(line_1703) - len(line_1703.lstrip())
    print(f"Line 1703 actual indent: {indent_1703}")
    
if 1703 < len(lines):  # Line 1704 is index 1703
    line_1704 = lines[1703]
    indent_1704 = len(line_1704) - len(line_1704.lstrip())
    print(f"Line 1704 actual indent: {indent_1704}")

# Fix: line 1704 should have same indentation as line 1703
# Actually, looking at the structure:
# coverage_summary = defaultdict(dict)
# for key, count in self.metrics["rule_coverage"].items():
# Both should be at same indentation level (one level inside method)

print("\nFixing indentation...")
# Let me check a larger context to understand the structure
print("\nContext (lines 1690-1720):")
for i in range(1689, 1720):
    if i < len(lines):
        marker = ">>>" if i == 1703 else "   "
        print(f"{marker} {i+1:4}: {lines[i].rstrip()}")

# Actually, I think the issue is that when we changed line 1703,
# we might have removed or changed its indentation.
# Let me restore proper Python structure

# The structure should be:
# def get_summary(self):
#     ... 
#     coverage_summary = defaultdict(lambda: {"total": 0, "violated": 0, "satisfied": 0})
#     for key, count in self.metrics["rule_coverage"].items():
#         parts = key.split(".")
#         if len(parts) == 3:
#             regime, article, status = parts
#             regime_key = f"{regime}.{article}"
#             coverage_summary[regime_key]["total"] += count
#             coverage_summary[regime_key][status.lower()] += count

# Actually, let me just rewrite lines 1700-1715 properly
print("\nRewriting the section properly...")

# Find where the get_summary method actually starts
for i in range(1680, 1700):
    if i < len(lines) and 'def get_summary(self):' in lines[i]:
        method_start = i
        method_indent = len(lines[i]) - len(lines[i].lstrip())
        print(f"Method starts at line {i+1} with indent {method_indent}")
        
        # Now find the coverage_summary block
        for j in range(i+1, i+50):
            if j < len(lines) and 'coverage_summary = defaultdict' in lines[j]:
                print(f"Found coverage_summary at line {j+1}")
                
                # The next 10 lines should be part of this block
                # Let me replace from line j to j+10 with correct code
                
                # First, let me see what's there
                print(f"\nCurrent lines {j+1} to {j+10}:")
                for k in range(j, min(j+10, len(lines))):
                    print(f"  {k+1:4}: {lines[k].rstrip()}")
                
                # Now I need to know what the correct code should be
                # Based on the original, it should be:
                correct_lines = [
                    ' ' * (method_indent + 4) + 'coverage_summary = defaultdict(lambda: {"total": 0, "violated": 0, "satisfied": 0})',
                    ' ' * (method_indent + 4) + 'for key, count in self.metrics["rule_coverage"].items():',
                    ' ' * (method_indent + 8) + 'parts = key.split(".")',
                    ' ' * (method_indent + 8) + 'if len(parts) == 3:',
                    ' ' * (method_indent + 12) + 'regime, article, status = parts',
                    ' ' * (method_indent + 12) + 'regime_key = f"{regime}.{article}"',
                    ' ' * (method_indent + 12) + 'coverage_summary[regime_key]["total"] = coverage_summary[regime_key].get("total", 0) + count',
                    ' ' * (method_indent + 12) + 'coverage_summary[regime_key][status.lower()] = coverage_summary[regime_key].get(status.lower(), 0) + count'
                ]
                
                # Replace lines j to j+7 with correct_lines
                for k in range(len(correct_lines)):
                    if j + k < len(lines):
                        lines[j + k] = correct_lines[k] + '\n'
                    else:
                        lines.append(correct_lines[k] + '\n')
                
                print("\nFixed the block!")
                break
        break

# Write back
with open(kernel_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\nFile fixed. Testing import...")