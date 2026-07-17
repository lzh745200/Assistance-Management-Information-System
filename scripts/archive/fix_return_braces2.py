#!/usr/bin/env python3
"""Fix remaining extra }) after return statements that end with })."""
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
    # Where the return line ends with }) (closing the function call)
    # and the next line is just }) (extra, leftover from params wrapper)
    lines = content.split('\n')
    result = []
    i = 0
    while i < len(lines):
        curr = lines[i].rstrip()
        if i + 1 < len(lines):
            next_stripped = lines[i + 1].strip()
            # If next line is just })
            if next_stripped == '})':
                # Check if current line is a return statement
                if 'return ' in curr:
                    # The next }) is extra if it's followed by } (end of function)
                    if i + 2 < len(lines):
                        next_next = lines[i + 2].strip()
                        if next_next == '}' or next_next.startswith('}'):
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
