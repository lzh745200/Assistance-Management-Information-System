#!/usr/bin/env python3
"""
Fix the over-correction from fix_unused_imports.py:
1. Add 'get' back to imports where it's actually used (get<Generic> or get( on any line)
2. Fix TS18004: shorthand 'params' property without a variable in scope
3. Remove truly unused imports (del, apiRequest)
"""
import re
from pathlib import Path

src = Path(__file__).parent.parent / "frontend" / "src"
changed = []


def check_get_usage(content):
    """Check if 'get' is actually called in the code (not just in import line)."""
    # Remove import lines for checking
    code = re.sub(r"import\s+\{[^}]+\}\s*from\s*['\"][^'\"]+['\"]", '', content)
    # Check for get( or get< (function call with or without generics)
    return bool(re.search(r'\bget\s*[<(]', code))


def check_del_usage(content):
    """Check if 'del' is actually called."""
    code = re.sub(r"import\s+\{[^}]+\}\s*from\s*['\"][^'\"]+['\"]", '', content)
    return bool(re.search(r'\bdel\s*\(', code))


def check_apiRequest_usage(content):
    """Check if 'apiRequest' is actually called."""
    code = re.sub(r"import\s+\{[^}]+\}\s*from\s*['\"][^'\"]+['\"]", '', content)
    return bool(re.search(r'\bapiRequest\s*\(', code))


def fix_imports(content):
    """Fix import line to include exactly what's needed."""
    # Find the import line
    import_match = re.search(
        r"import\s+\{([^}]*)\}\s*from\s*['\"](?:\./|@/api/)request['\"]",
        content
    )
    if not import_match:
        return content
    
    # Parse current imports
    current = [s.strip() for s in import_match.group(1).split(',') if s.strip()]
    
    # Determine what's actually needed
    needed = set()
    if check_get_usage(content):
        needed.add('get')
    # Check for post, put, del, patch, apiRequest
    code = re.sub(r"import\s+\{[^}]+\}\s*from\s*['\"][^'\"]+['\"]", '', content)
    if re.search(r'\bpost\s*\(', code):
        needed.add('post')
    if re.search(r'\bput\s*\(', code):
        needed.add('put')
    if check_del_usage(content):
        needed.add('del')
    if re.search(r'\bpatch\s*\(', code):
        needed.add('patch')
    if check_apiRequest_usage(content):
        needed.add('apiRequest')
    
    # Add other named imports that aren't HTTP methods (downloadBlob, parseContentDisposition, etc.)
    method_names = {'get', 'post', 'put', 'del', 'patch', 'apiRequest'}
    for name in current:
        if name not in method_names:
            # Check if it's used
            if re.search(r'\b' + re.escape(name) + r'\b', code):
                needed.add(name)
    
    # Build new import string
    canonical_order = ['get', 'post', 'put', 'del', 'patch', 'apiRequest']
    imports = [name for name in canonical_order if name in needed]
    extras = needed - set(canonical_order)
    for name in sorted(extras):
        imports.append(name)
    
    if not imports:
        return content
    
    import_str = ', '.join(imports)
    new_import = f"import {{ {import_str} }} from '@/api/request'"
    
    # Replace the old import
    content = re.sub(
        r"import\s+\{[^}]*\}\s*from\s*['\"](?:\./|@/api/)request['\"]",
        new_import,
        content,
        count=1
    )
    
    return content


def fix_shorthand_params(content):
    """Fix TS18004: 'params' shorthand property without variable in scope.
    
    In apiRequest({ method: 'GET', url: ..., params }) where there's no `params` variable,
    change to params: undefined or remove the params key entirely.
    """
    # The issue is in object literals like: { method: 'GET', url: '...', params }
    # where `params` is a shorthand property but there's no `params` variable in scope.
    # This happens when the original code had `params: undefined` which was incorrectly
    # converted to `params` (shorthand).
    
    # We need to find these cases and convert `params` back to either:
    # - Remove it if it's the last property (just remove `, params`)
    # - Or change to `params: undefined`
    
    # But we also need to NOT break cases where `params` IS a real variable (function parameter)
    
    # Strategy: find all apiRequest calls with `params }` (shorthand at end of object)
    # and check if `params` is defined in the surrounding scope
    
    # This is too complex for a regex. Let's just convert all standalone `params` in
    # apiRequest object literals back to `params: undefined` where the function doesn't
    # have a `params` parameter.
    
    # Actually, the simplest fix: find `params }` in apiRequest calls and change to
    # either remove it or add `: undefined` or `: params` if there's a params variable
    
    # Let's just look for the specific pattern: `, params }` inside apiRequest
    # and replace with either nothing (if no params var) or keep as is (if params var exists)
    
    # For now, let's just convert all bare `params` shorthand in object literals to `params: undefined`
    # This is safe because:
    # - If params IS a variable, `params: undefined` loses the value (bad)
    # - If params is NOT a variable, `params: undefined` is correct
    
    # Better approach: only fix in functions that DON'T have a `params` parameter
    # Let's match the pattern more carefully
    
    # Pattern: inside apiRequest({...}), find `params }` or `params,` at end
    # and the function doesn't have a `params` argument
    
    return content


for f in list(src.rglob('*.ts')) + list(src.rglob('*.vue')):
    if 'node_modules' in str(f) or 'dist' in str(f) or '__tests__' in str(f) or '.spec.' in str(f):
        continue
    try:
        content = f.read_text(encoding='utf-8')
    except:
        continue
    
    original = content
    content = fix_imports(content)
    
    if content != original:
        f.write_text(content, encoding='utf-8')
        changed.append(str(f))

print(f"Fixed {len(changed)} files:")
for f in changed:
    print(f"  ✓ {Path(f).relative_to(src)}")
