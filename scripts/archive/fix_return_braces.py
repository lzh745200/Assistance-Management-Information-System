#!/usr/bin/env python3
"""Remove extra }) lines after return statements in API files."""
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
    original = content
    
    # Pattern: return get/post/put/del(...) followed by }) on next line
    # This happens when the original was:
    #   return api.get(url, { params: { ... } })
    # and the script unwrapped params but left the })
    lines = content.split('\n')
    result = []
    i = 0
    while i < len(lines):
        curr = lines[i].rstrip()
        # Check if current line has return ... get/post/put/del(...) ending with )
        if i + 1 < len(lines):
            next_stripped = lines[i + 1].strip()
            # If next line is just }) and current line ends with ) (not })
            if (next_stripped == '})' and 
                curr.endswith(')') and 
                not curr.endswith('})') and
                ('return ' in curr or curr.endswith(')'))):
                # Check if this looks like a return statement or function call
                if 'return ' in curr or '.then(' in curr:
                    # Skip the extra })
                    result.append(lines[i])
                    i += 2
                    continue
        result.append(lines[i])
        i += 1
    
    content = '\n'.join(result)
    
    if content != original:
        f.write_text(content, encoding='utf-8')
        changed.append(str(f))

print(f"Fixed {len(changed)} files:")
for f in changed:
    print(f"  ✓ {f}")
