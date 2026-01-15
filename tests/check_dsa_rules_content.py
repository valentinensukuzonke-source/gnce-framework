# check_dsa_rules_content.py
import os

dsa_rules_path = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC\gnce\gn_kernel\rules\dsa_rules.py"

print(f"Checking DSA rules file: {dsa_rules_path}")
print("=" * 80)

if os.path.exists(dsa_rules_path):
    with open(dsa_rules_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"File exists, size: {len(content)} bytes")
    
    # Check for harmful content detection
    harmful_keywords = ['harmful', 'illegal', 'violation', 'risk_indicators', 'harmful_content_flag']
    
    print("\nChecking for harmful content detection...")
    found_keywords = []
    for keyword in harmful_keywords:
        if keyword in content.lower():
            found_keywords.append(keyword)
    
    if found_keywords:
        print(f"✅ Found keywords: {', '.join(found_keywords)}")
    else:
        print("❌ No harmful content detection keywords found!")
        
    # Show the evaluate_dsa_rules function
    print("\nLooking for evaluate_dsa_rules function...")
    if 'def evaluate_dsa_rules' in content:
        # Extract the function
        lines = content.split('\n')
        in_function = False
        function_lines = []
        
        for line in lines:
            if 'def evaluate_dsa_rules' in line:
                in_function = True
            
            if in_function:
                function_lines.append(line)
                # Check if we've reached the next function
                if line.strip().startswith('def ') and 'def evaluate_dsa_rules' not in line and len(function_lines) > 10:
                    break
        
        print(f"Function found ({len(function_lines)} lines)")
        
        # Show key parts
        print("\nKey parts of function:")
        for i, line in enumerate(function_lines[:30]):  # First 30 lines
            if any(keyword in line.lower() for keyword in ['harmful', 'illegal', 'violat', 'risk']):
                print(f"  {i+1}: {line}")
                
    else:
        print("❌ evaluate_dsa_rules function not found!")
        
else:
    print(f"❌ File does not exist at: {dsa_rules_path}")