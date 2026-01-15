import sys
import re

with open("gnce/ui/gn_app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find the tab_layers section
pattern = r'with tab_layers:(.*?)(?=\n\s+with tab_|$)'
match = re.search(pattern, content, re.DOTALL)

if match:
    print("Found tab_layers section:")
    print("-" * 80)
    print(match.group(0)[:500] + "...")
    print("-" * 80)
    print("\n✅ Ready to add the constitutional layer visual!")
else:
    print("❌ Could not find tab_layers section")
