# simple_discovery.py
import os

gnce_root = r"C:\Users\Valentine Nsukuzonke\Pictures\MY IP\Meta Pitch Deck\GNCE v0.7.2-RC"
print(f"Exploring: {gnce_root}")
print("=" * 80)

# List top-level contents
print("\nTop-level contents:")
for item in os.listdir(gnce_root):
    full_path = os.path.join(gnce_root, item)
    if os.path.isdir(full_path):
        print(f"📁 {item}/")
    else:
        print(f"📄 {item}")

# Look for kernel.py specifically
print("\n" + "=" * 80)
print("Searching for kernel.py...")
found_kernel = False

for root, dirs, files in os.walk(gnce_root):
    # Skip virtual environment and cache directories
    if '.venv' in root or '__pycache__' in root:
        continue
        
    if 'kernel.py' in files:
        print(f"\n✅ Found kernel.py at: {root}")
        print(f"   Relative path from GNCE root: {os.path.relpath(root, gnce_root)}")
        
        # Show Python files in that directory
        py_files = [f for f in files if f.endswith('.py')]
        print(f"   Python files in this directory ({len(py_files)}):")
        for py_file in py_files[:15]:  # Show first 15
            print(f"     - {py_file}")
        
        # Check for gnce directory structure
        parent_dir = os.path.dirname(root)
        if 'gnce' in os.listdir(parent_dir) if os.path.exists(parent_dir) else False:
            print(f"   📁 'gnce' directory exists in parent: {parent_dir}")
        
        found_kernel = True
        break

if not found_kernel:
    print("\n❌ kernel.py not found!")

# Check for common GNCE directories
print("\n" + "=" * 80)
print("Looking for GNCE-specific directories...")
gnce_dirs = ['gnce', 'gn_kernel', 'kernel', 'rules', 'regimes']
for dir_name in gnce_dirs:
    dir_path = os.path.join(gnce_root, dir_name)
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        print(f"✅ Found {dir_name}/ directory")
        # Show first few items
        try:
            items = os.listdir(dir_path)[:5]
            print(f"   Contains: {', '.join(items)}" + ("..." if len(items) >= 5 else ""))
        except:
            pass