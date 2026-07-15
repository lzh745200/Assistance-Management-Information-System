#!/usr/bin/env python3
"""
Fix TS18004: shorthand 'params' property in apiRequest calls where no 'params' variable exists.
Replace bare 'params' (shorthand) with nothing (remove the key) when the function doesn't have a params parameter.
"""
import re
from pathlib import Path

src = Path(__file__).parent.parent / "frontend" / "src"
changed = []


def fix_params_shorthand(content):
    """
    Find apiRequest calls with bare 'params' shorthand and remove it if no 'params' variable exists.
    """
    # Find all apiRequest calls
    # Pattern: apiRequest({ ... params ... })
    # We need to find bare 'params' (not 'params: something') inside apiRequest object literals
    
    # Strategy: find each apiRequest({ ... }) call, check if it contains bare 'params',
    # and if so, check if there's a 'params' variable in the enclosing function
    
    lines = content.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this line has apiRequest with bare 'params'
        if 'apiRequest(' in line and 'params' in line:
            # Check if it's a shorthand: ', params,' or ', params }' or ', params)'
            # (not 'params:' which is a key-value pair)
            if re.search(r',\s*params\s*[,})]', line) and 'params:' not in line:
                # This might be a shorthand - remove it
                # Replace ', params,' with ',' and ', params }' with ' }' etc.
                new_line = re.sub(r',\s*params\s*,', ',', line)
                new_line = re.sub(r',\s*params\s*\}', ' }', new_line)
                new_line = re.sub(r',\s*params\s*\)', ')', new_line)
                result.append(new_line)
                i += 1
                continue
        
        result.append(line)
        i += 1
    
    return '\n'.join(result)


for f in list(src.rglob('*.ts')) + list(src.rglob('*.vue')):
    if 'node_modules' in str(f) or 'dist' in str(f) or '__tests__' in str(f) or '.spec.' in str(f):
        continue
    try:
        content = f.read_text(encoding='utf-8')
    except:
        continue
    
    original = content
    content = fix_params_shorthand(content)
    
    if content != original:
        f.write_text(content, encoding='utf-8')
        changed.append(str(f))

print(f"Fixed {len(changed)} files:")
for f in changed:
    print(f"  ✓ {Path(f).relative_to(src)}")
