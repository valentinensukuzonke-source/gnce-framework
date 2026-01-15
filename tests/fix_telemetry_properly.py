# fix_telemetry_properly.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

with open(kernel_path, 'r', encoding='utf-8') as f:
    content = f.read()

# We need to fix the get_summary method properly
# Find and replace the problematic section
import re

# Pattern to find the coverage_summary initialization and usage
pattern = r'(coverage_summary = defaultdict\(lambda: \{"total": 0, "violated": 0, "satisfied": 0\}\)\s*\n\s*for key, count in self\.metrics\["rule_coverage"\]\.items\(\):\s*\n\s*parts = key\.split\("\\."\)\s*\n\s*if len\(parts\) == 3:\s*\n\s*regime, article, status = parts\s*\n\s*regime_key = f"\{regime\}\.\{article\}"\s*\n\s*coverage_summary\[regime_key\]\["total"\] \+= count\s*\n\s*coverage_summary\[regime_key\]\[status\.lower\(\)\] \+= count)'

match = re.search(pattern, content, re.DOTALL)
if match:
    print("Found the buggy section")
    
    # Replace with a fixed version
    fixed_section = '''coverage_summary = defaultdict(lambda: defaultdict(int))
    for key, count in self.metrics["rule_coverage"].items():
        parts = key.split(".")
        if len(parts) == 3:
            regime, article, status = parts
            regime_key = f"{regime}.{article}"
            coverage_summary[regime_key]["total"] += count
            coverage_summary[regime_key][status.lower()] += count'''
    
    content = content.replace(match.group(1), fixed_section)
    
    # Write back
    with open(kernel_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed the telemetry bug!")
else:
    print("Could not find the pattern, trying alternative approach...")
    
    # Try a simpler fix - just make sure the key exists before incrementing
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'coverage_summary[regime_key][status.lower()] += count' in line:
            print(f"Found line at {i+1}")
            
            # Replace with safer version
            lines[i] = '        coverage_summary[regime_key][status.lower()] = coverage_summary[regime_key].get(status.lower(), 0) + count'
            
            # Also need to ensure the defaultdict creates dicts that can handle any key
            # Find the defaultdict line
            for j in range(i-10, i):
                if 'coverage_summary = defaultdict' in lines[j]:
                    print(f"Found defaultdict at line {j+1}")
                    # Change to create regular dicts that can handle any key
                    lines[j] = '    coverage_summary = defaultdict(dict)'
                    break
            
            break
    
    with open(kernel_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("Applied alternative fix!")