#!/usr/bin/env python3
"""Fix get(url, { params }) → get(url, params) shorthand pattern."""
import re
from pathlib import Path

src = Path(__file__).parent.parent / "frontend" / "src"
changed = []

for f in list(src.rglob('*.ts')) + list(src.rglob('*.vue')):
    if 'node_modules' in str(f) or 'dist' in str(f) or '__tests__' in str(f) or '.spec.' in str(f):
        continue
    try:
        content = f.read_text(encoding='utf-8')
    except:
        continue
    if re.search(r'get\([^,)]+,\s*\{\s*params\s*\}\)', content, flags=re.DOTALL):
        new_content = re.sub(r'get\(([^,)]+),\s*\{\s*params\s*\}\)', r'get(\1, params)', content, flags=re.DOTALL)
        f.write_text(new_content, encoding='utf-8')
        changed.append(str(f))

print(f"Fixed {len(changed)} files:")
for f in changed:
    print(f"  ✓ {f}")
