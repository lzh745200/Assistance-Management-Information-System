#!/usr/bin/env python3
"""Remove extra }) lines left by previous migration scripts."""
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
    
    # Remove extra }) that appears right after a get/post/put/del call's closing })
    # Pattern: a line ending with }) followed by a line that is just }) (with whitespace)
    # and then a line that starts with const/var/let/tableData/return/} catch/} finally
    lines = content.split('\n')
    result = []
    i = 0
    while i < len(lines):
        # Check if current line ends with }) and next line is just })
        curr = lines[i].rstrip()
        if i + 1 < len(lines) and curr.endswith('})') and lines[i+1].strip() == '})':
            # Check if the line after the extra }) is code (not end of block)
            if i + 2 < len(lines):
                next_next = lines[i+2].strip()
                # If next_next starts a new statement, the middle }) is extra
                if (next_next.startswith('const ') or 
                    next_next.startswith('let ') or 
                    next_next.startswith('var ') or
                    next_next.startswith('tableData') or
                    next_next.startswith('total') or
                    next_next.startswith('return') or
                    next_next.startswith('} catch') or
                    next_next.startswith('} finally') or
                    next_next.startswith('if ') or
                    next_next.startswith('if(') or
                    next_next.startswith('pagination') or
                    next_next.startswith('ElMessage') or
                    next_next.startswith('pendingCount') or
                    next_next.startswith('items') or
                    next_next.startswith('raw') or
                    next_next.startswith('the') or
                    next_next.startswith('//') or
                    next_next == ''):
                    # Keep current line, skip the extra }), keep rest
                    result.append(lines[i])
                    i += 2  # Skip the extra })
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
