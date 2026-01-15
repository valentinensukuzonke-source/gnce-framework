# simple_comment_fix.py
import os

kernel_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\kernel.py"
line_number = 1704  # From the error message

print(f"Commenting out problematic line {line_number}...")
print("=" * 80)

# Read the file
with open(kernel_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Check line number exists
if line_number <= len(lines):
    print(f"Line {line_number}: {lines[line_number-1].rstrip()}")
    
    # Comment it out
    original_line = lines[line_number-1]
    if not original_line.strip().startswith('#'):
        lines[line_number-1] = '# ' + original_line
        print(f"Commented out line {line_number}")
        
        # Write back
        with open(kernel_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"\n✅ Line {line_number} has been commented out")
        
        # Also check a few lines before and after for related issues
        print(f"\nChecking context (lines {line_number-5} to {line_number+5}):")
        for i in range(max(0, line_number-6), min(len(lines), line_number+4)):
            line_num = i + 1
            line_text = lines[i].rstrip()
            if line_num == line_number:
                print(f">>> {line_num:4}: {line_text}")
            else:
                print(f"    {line_num:4}: {line_text}")
    else:
        print(f"Line {line_number} is already commented out")
else:
    print(f"❌ Line {line_number} does not exist in file")
    print(f"File has {len(lines)} lines total")