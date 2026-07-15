#!/usr/bin/env python3
"""
Fix remaining TS6133 (unused imports/params) and TS2304 (cannot find name) errors.
1. Remove unused 'get' from imports where only apiRequest is used
2. Fix 'params' parameter not being used in apiRequest calls
3. Add missing apiRequest imports
"""
import re
from pathlib import Path

src = Path(__file__).parent.parent / "frontend" / "src"
changed = []


def remove_unused_get(content):
    """Remove 'get' from imports if it's not used in the file."""
    # Check if 'get' is actually used (not just in the import line)
    # Remove the import line temporarily for checking
    lines = content.split('\n')
    import_line_idx = None
    for i, line in enumerate(lines):
        if re.match(r"import\s+\{.*\bget\b.*\}\s*from\s*['\"](?:\./|@/api/)request['\"]", line):
            import_line_idx = i
            break
    
    if import_line_idx is None:
        return content
    
    # Check if 'get(' is used anywhere (not in the import line)
    code_without_import = '\n'.join(lines[:import_line_idx] + lines[import_line_idx+1:])
    if re.search(r'\bget\s*\(', code_without_import):
        return content  # 'get' is used, keep it
    
    # Remove 'get' from the import
    old_import = lines[import_line_idx]
    # Remove 'get,' or ', get' or just 'get'
    new_import = re.sub(r'\bget\s*,\s*', '', old_import)
    new_import = re.sub(r',\s*get\b', '', new_import)
    new_import = re.sub(r'\bget\b', '', new_import)
    # Clean up any double spaces or trailing commas
    new_import = re.sub(r',\s*,', ',', new_import)
    new_import = re.sub(r'\{\s*,', '{', new_import)
    new_import = re.sub(r',\s*\}', '}', new_import)
    new_import = re.sub(r'\s+', ' ', new_import)
    
    lines[import_line_idx] = new_import
    return '\n'.join(lines)


def fix_params_not_used(content):
    """Fix 'params' declared but not used - replace 'params: undefined' with 'params'."""
    # Pattern: params: undefined → params
    content = re.sub(r'params:\s*undefined', 'params', content)
    return content


def add_missing_imports(content):
    """Add apiRequest to imports if it's used but not imported."""
    if 'apiRequest(' in content:
        # Check if already imported
        if not re.search(r"import\s+\{[^}]*\bapiRequest\b[^}]*\}\s*from", content):
            # Add apiRequest to existing import
            content = re.sub(
                r"(import\s+\{)([^}]*)(\}\s*from\s*['\"](?:\./|@/api/)request['\"])",
                lambda m: f"{m.group(1)}{m.group(2)}, apiRequest{m.group(3)}" if 'apiRequest' not in m.group(2) else m.group(0),
                content
            )
    return content


for f in list(src.rglob('*.ts')) + list(src.rglob('*.vue')):
    if 'node_modules' in str(f) or 'dist' in str(f) or '__tests__' in str(f) or '.spec.' in str(f):
        continue
    try:
        content = f.read_text(encoding='utf-8')
    except:
        continue
    
    original = content
    content = remove_unused_get(content)
    content = fix_params_not_used(content)
    content = add_missing_imports(content)
    
    if content != original:
        f.write_text(content, encoding='utf-8')
        changed.append(str(f))

print(f"Fixed {len(changed)} files:")
for f in changed:
    print(f"  ✓ {Path(f).relative_to(src)}")
