#!/usr/bin/env python3
"""Fix double comma pattern (, ,}) left by the migration script."""
import re
from pathlib import Path

src = Path(__file__).parent.parent / "frontend" / "src"
changed = []

for f in list(src.rglob('*.ts')) + list(src.rglob('*.vue')):
    if 'node_modules' in str(f) or 'dist' in str(f):
        continue
    try:
        content = f.read_text(encoding='utf-8')
    except:
        continue
    original = content
    
    # Fix: }, , }) → } })
    content = re.sub(r',\s*,\s*\}', '}', content)
    
    if content != original:
        f.write_text(content, encoding='utf-8')
        changed.append(str(f))

print(f"Fixed {len(changed)} files")
for f in changed:
    print(f"  ✓ {Path(f).relative_to(src)}")
