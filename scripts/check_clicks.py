import os
os.chdir(r"C:\military-Rural Revitalization-system")
with open("frontend/src/views/dataPackage/ReceivePackage.vue", "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, line in enumerate(lines, 1):
    if "@click" in line:
        print(f"Line {i}: {line.rstrip()[:150]}")
