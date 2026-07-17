#!/usr/bin/env python3
"""
Final fix pass:
1. Fix TS2304: add missing 'post', 'put', 'del', 'apiRequest' back to imports
2. Fix TS6133: add 'params' back to apiRequest calls where 'params' IS a function parameter
3. Fix TS6133: remove truly unused 'get' imports
"""
import re
from pathlib import Path

src = Path(__file__).parent.parent / "frontend" / "src"
changed = []


def get_code_without_imports(content):
    """Remove ALL import lines for usage checking."""
    lines = content.split('\n')
    code_lines = []
    for line in lines:
        if line.strip().startswith('import '):
            continue
        code_lines.append(line)
    return '\n'.join(code_lines)


def fix_import_line(content):
    """Fix the import line to include all actually-used names."""
    code = get_code_without_imports(content)
    
    # Find what's actually used
    needed = set()
    # Check for get usage: get( or get<T>(
    if re.search(r'\bget\s*[<(]', code):
        needed.add('get')
    if re.search(r'\bpost\s*[<(]', code):
        needed.add('post')
    if re.search(r'\bput\s*[<(]', code):
        needed.add('put')
    if re.search(r'\bdel\s*\(', code):
        needed.add('del')
    if re.search(r'\bpatch\s*[<(]', code):
        needed.add('patch')
    if re.search(r'\bapiRequest\s*\(', code):
        needed.add('apiRequest')
    
    # Check for other named imports (downloadBlob, parseContentDisposition, etc.)
    # Find current imports
    import_match = re.search(
        r"import\s+\{([^}]*)\}\s*from\s*['\"](?:\./|@/api/)request['\"]",
        content
    )
    if not import_match:
        return content
    
    current = [s.strip() for s in import_match.group(1).split(',') if s.strip()]
    method_names = {'get', 'post', 'put', 'del', 'patch', 'apiRequest'}
    for name in current:
        if name not in method_names:
            if re.search(r'\b' + re.escape(name) + r'\b', code):
                needed.add(name)
    
    # Build new import
    canonical_order = ['get', 'post', 'put', 'del', 'patch', 'apiRequest']
    imports = [name for name in canonical_order if name in needed]
    extras = needed - set(canonical_order)
    for name in sorted(extras):
        imports.append(name)
    
    if not imports:
        return content
    
    import_str = ', '.join(imports)
    new_import = f"import {{ {import_str} }} from '@/api/request'"
    
    content = re.sub(
        r"import\s+\{[^}]*\}\s*from\s*['\"](?:\./|@/api/)request['\"]",
        new_import,
        content,
        count=1
    )
    
    return content


def fix_params_in_apirequest(content):
    """
    Fix TS6133 'params' declared but never read.
    In functions that have a 'params' parameter, add 'params: params' to apiRequest calls
    where it was removed by the previous fix script.
    """
    # This is complex - we need to find functions that accept 'params' as a parameter
    # and then find apiRequest calls inside them that don't use 'params'
    
    # For now, let's just check if the function has 'params' in its signature
    # and if so, add 'params' back to the apiRequest call
    
    # Pattern: function foo(params?: any) { ... apiRequest({ ... }) ... }
    # where apiRequest doesn't have 'params:' in it
    
    # Simple approach: find all apiRequest calls that don't have 'params' 
    # and check if the enclosing function has a 'params' parameter
    
    # Even simpler: find lines with 'params' in function signature and 
    # apiRequest calls without 'params' in the same function
    
    lines = content.split('\n')
    result = []
    in_function_with_params = False
    
    for i, line in enumerate(lines):
        # Detect function with 'params' parameter
        if re.search(r'(function|async function|=>)\s*\([^)]*\bparams\b', line) or \
           re.search(r'\bparams\s*[?:]', line):
            in_function_with_params = True
        
        # Detect end of function (rough heuristic)
        if in_function_with_params and line.strip() == '}':
            in_function_with_params = False
        
        # If we're in a function with params and see apiRequest without params:
        if in_function_with_params and 'apiRequest(' in line and 'params' not in line:
            # Add params to the apiRequest call
            # Pattern: apiRequest({ method: 'GET', url: '...', responseType: 'blob' })
            # → apiRequest({ method: 'GET', url: '...', params, responseType: 'blob' })
            if 'responseType' in line:
                line = re.sub(
                    r"(url:\s*[^,]+,\s*)(responseType)",
                    r"\1params, \2",
                    line
                )
            elif 'method:' in line:
                line = re.sub(
                    r"(url:\s*[^,}]+)(\s*[,}])",
                    r"\1, params\2",
                    line
                )
        
        result.append(line)
    
    return '\n'.join(result)


for f in list(src.rglob('*.ts')) + list(src.rglob('*.vue')):
    if 'node_modules' in str(f) or 'dist' in str(f) or '__tests__' in str(f) or '.spec.' in str(f):
        continue
    try:
        content = f.read_text(encoding='utf-8')
    except:
        continue
    
    original = content
    content = fix_import_line(content)
    content = fix_params_in_apirequest(content)
    
    if content != original:
        f.write_text(content, encoding='utf-8')
        changed.append(str(f))

print(f"Fixed {len(changed)} files:")
for f in changed:
    print(f"  ✓ {Path(f).relative_to(src)}")
