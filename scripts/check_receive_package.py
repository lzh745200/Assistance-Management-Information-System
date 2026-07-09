"""Check ReceivePackage.vue for the multi-line @click issue."""
with open("frontend/src/views/dataPackage/ReceivePackage.vue", "r", encoding="utf-8") as f:
    content = f.read()

lines = content.split('\n')
problematic = False
for i, line in enumerate(lines, 1):
    if '@click="' in line and line.strip().endswith('"') and i + 1 < len(lines):
        next_line = lines[i].strip()
        if next_line and not next_line.startswith('>') and not next_line.startswith('//'):
            # Check if the next non-empty lines contain more JS (multi-line @click)
            remaining = []
            for j in range(i, min(i + 5, len(lines))):
                l = lines[j].strip()
                if l and not l.startswith('>') and '@click' not in l:
                    remaining.append(l)
            if remaining and any('(' in r or '=' in r for r in remaining):
                problematic = True
                print(f"PROBLEM at line {i}: {line.strip()}")
                for r in remaining:
                    print(f"  continuation: {r}")

if not problematic:
    print("OK: No multi-line @click found")
    
# Also check for the fixed version
if 'clearLocalImport(); showLocalImport = false' in content:
    print("OK: Fixed single-line version found")
elif 'clearLocalImport()' in content:
    print("WARNING: clearLocalImport() found but might still be multi-line")
