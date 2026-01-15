
# GNCE CI/CD Pre-Deploy Hook Example
from kernel_gnce_v0_7_2 import run
import sys, json

payload = json.load(sys.stdin)
result = run(payload)

if result["verdict"]["decision_outcome"] != "ALLOW":
    print("Deployment blocked by GNCE")
    sys.exit(1)

print("Deployment approved by GNCE")
