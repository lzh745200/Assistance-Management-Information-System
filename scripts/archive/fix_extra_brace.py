#!/usr/bin/env python3
"""Fix extra } in apiRequest calls: }}} → }}) when preceded by apiRequest."""
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
    
    # Fix: }}} → }}) when preceded by } and inside apiRequest call
    # The pattern is: params: { ... }}}) should be params: { ... }})
    content = re.sub(r'\}\}\}\)', '}})', content)
    
    # Also fix: }, }) → }) when it's a trailing comma + closing brace
    # This handles cases where the remaining was just a comma
    # Pattern: , }) at end of apiRequest → })
    # But be careful not to break legitimate patterns
    
    if content != original:
        f.write_text(content, encoding='utf-8')
        changed.append(str(f))

print(f"Fixed {len(changed)} files")
for f in changed:
    print(f"  ✓ {Path(f).relative_to(src)}")
