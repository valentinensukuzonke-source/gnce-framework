# rewrite_get_summary.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"

with open(kernel_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the get_summary method and replace it entirely
import re

# Pattern to find the entire get_summary method
# We'll find from "def get_summary(self):" to the next "def " at same indent level
pattern = r'(def get_summary\(self\):.*?)(?=\n\S|\Z)'

match = re.search(pattern, content, re.DOTALL)
if match:
    print(f"Found get_summary method, length: {len(match.group(1))} chars")
    
    # Replace with correct implementation
    correct_method = '''def get_summary(self) -> Dict[str, Any]:
        """Get telemetry summary."""
        summary = {
            "total_evaluations": len(self.metrics["evaluation_times"]),
            "avg_evaluation_time_ms": 0.0,
            "avg_policy_count": 0.0,
            "layer_performance": {},
            "rule_coverage_summary": {},
            "error_summary": dict(self.metrics["error_counts"]),
            "warnings": self.metrics["warnings"][-100:],  # Last 100 warnings
            "current_evaluation_id": self.current_evaluation_id,
        }
        
        if self.metrics["evaluation_times"]:
            summary["avg_evaluation_time_ms"] = sum(self.metrics["evaluation_times"]) / len(self.metrics["evaluation_times"])
        
        if self.metrics["policy_counts"]:
            summary["avg_policy_count"] = sum(self.metrics["policy_counts"]) / len(self.metrics["policy_counts"])
        
        for layer, durations in self.metrics["layer_durations_ms"].items():
            if durations:
                summary["layer_performance"][layer] = {
                    "avg_ms": sum(durations) / len(durations),
                    "min_ms": min(durations),
                    "max_ms": max(durations),
                    "count": len(durations),
                    "p95_ms": sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 1 else durations[0],
                }
        
        # Aggregate rule coverage - FIXED VERSION
        coverage_summary = defaultdict(dict)
        for key, count in self.metrics["rule_coverage"].items():
            parts = key.split(".")
            if len(parts) == 3:
                regime, article, status = parts
                regime_key = f"{regime}.{article}"
                # Use .get() to handle missing keys
                current_total = coverage_summary[regime_key].get("total", 0)
                coverage_summary[regime_key]["total"] = current_total + count
                
                current_status_count = coverage_summary[regime_key].get(status.lower(), 0)
                coverage_summary[regime_key][status.lower()] = current_status_count + count
        
        summary["rule_coverage_summary"] = dict(coverage_summary)
        
        return summary'''
    
    # Replace in content
    content = content.replace(match.group(1), correct_method)
    
    # Write back
    with open(kernel_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Replaced get_summary method with correct implementation!")
else:
    print("Could not find get_summary method with regex, trying manual approach...")
    
    # Manual approach: find line numbers
    lines = content.split('\n')
    func_start = -1
    func_end = -1
    
    for i, line in enumerate(lines):
        if 'def get_summary(self):' in line:
            func_start = i
            base_indent = len(line) - len(line.lstrip())
            print(f"Found at line {i+1}, base indent: {base_indent}")
            
            # Find end (next line with <= base_indent that's not empty)
            for j in range(i + 1, len(lines)):
                if lines[j].strip() and len(lines[j]) - len(lines[j].lstrip()) <= base_indent:
                    func_end = j
                    break
            if func_end == -1:
                func_end = len(lines)
            break
    
    if func_start != -1:
        print(f"Function spans lines {func_start+1} to {func_end+1}")
        
        # Replace with correct implementation (same as above)
        correct_method_lines = correct_method.split('\n')
        
        # Replace the lines
        lines[func_start:func_end] = correct_method_lines
        
        # Write back
        with open(kernel_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"Replaced {func_end - func_start} lines with {len(correct_method_lines)} lines")
    else:
        print("Could not find get_summary method!")