#!/usr/bin/env python3
"""
Migrate `import api from './request'` (Pattern A) to named imports (Pattern B).
Handles api.get(), api.post(), api.put(), api.delete(), api.patch(), api.apiRequest().
Also handles .then((r) => r.data) chains that are no longer needed.
"""

import re
from pathlib import Path

FRONTEND_SRC = Path(__file__).parent.parent / "frontend" / "src"
changed_files = []


def determine_needed_imports(content: str) -> set:
    needed = set()
    # Check for api.get, api.post, etc.
    if re.search(r'\bapi\.get\b', content):
        needed.add('get')
    if re.search(r'\bapi\.post\b', content):
        needed.add('post')
    if re.search(r'\bapi\.put\b', content):
        needed.add('put')
    if re.search(r'\bapi\.delete\b', content):
        needed.add('del')
    if re.search(r'\bapi\.patch\b', content):
        needed.add('patch')
    if re.search(r'\bapi\.apiRequest\b', content):
        needed.add('apiRequest')
    # Check for responseType: 'blob' in api.get calls (needs apiRequest)
    if re.search(r"api\.get\([^)]*responseType:\s*'blob'", content, re.DOTALL):
        needed.add('apiRequest')
    # Check for named imports already present
    named_match = re.search(r"import api,\s*\{([^}]+)\}\s*from\s*['\"](?:\./|@/api/)request['\"]", content)
    if named_match:
        for name in named_match.group(1).split(','):
            name = name.strip()
            if name:
                needed.add(name)
    return needed


def transform_import(content: str, needed: set) -> str:
    """Transform import line."""
    # Order: get, post, put, del, patch, apiRequest, then any extras
    canonical_order = ['get', 'post', 'put', 'del', 'patch', 'apiRequest']
    imports = [name for name in canonical_order if name in needed]
    # Add any extras not in canonical order
    extras = needed - set(canonical_order) - set(imports)
    # Known extras: parseContentDisposition, downloadBlob, etc.
    extra_order = ['parseContentDisposition', 'downloadBlob', 'cancelRequest', 'cancelAllRequests',
                   'isRequestCancelled', 'prefetchCsrfToken', 'createCancelableRequest',
                   'requestWithTimeout', 'isSuccess', '_setCachedToken', 'freezeRequests',
                   'unfreezeRequests', 'getPendingRequestCount']
    for name in extra_order:
        if name in extras:
            imports.append(name)
            extras.discard(name)
    # Add any remaining
    for name in sorted(extras):
        imports.append(name)
    
    import_str = ', '.join(imports)
    
    # Pattern 1: import api from './request' or import api from '@/api/request'
    content = re.sub(
        r"import api from ['\"](?:\./|@/api/)request['\"]",
        f"import {{ {import_str} }} from './request'",
        content
    )
    
    # Pattern 2: import api, { named } from './request'
    content = re.sub(
        r"import api,\s*\{[^}]+\}\s*from\s*['\"](?:\./|@/api/)request['\"]",
        f"import {{ {import_str} }} from './request'",
        content
    )
    
    return content


def transform_api_calls(content: str) -> str:
    """Transform api.get/post/put/delete/patch calls."""
    
    # api.apiRequest(...) → apiRequest(...)
    content = re.sub(r'\bapi\.apiRequest\b', 'apiRequest', content)
    
    # api.get(url, { params: P, responseType: 'blob' }) → apiRequest({ method: 'GET', url, params: P, responseType: 'blob' })
    # This is complex - handle it with a function
    def replace_api_get_blob(match):
        url = match.group(1)
        rest = match.group(2)  # everything between { and }
        # Parse the config object
        params_match = re.search(r'params:\s*([^,]+?)(?:,\s*responseType|\s*$)', rest)
        params_val = params_match.group(1).strip() if params_match else 'undefined'
        return f"apiRequest({{ method: 'GET', url: {url}, params: {params_val}, responseType: 'blob' }})"
    
    # Multi-line: api.get(url, { params, responseType: 'blob' })
    content = re.sub(
        r"api\.get\(([^,]+),\s*\{([^}]*responseType:\s*'blob'[^}]*)\}\)",
        replace_api_get_blob,
        content,
        flags=re.DOTALL
    )
    
    # api.get(url, { responseType: 'blob' }) → apiRequest({ method: 'GET', url, responseType: 'blob' })
    def replace_api_get_blob_simple(match):
        url = match.group(1)
        return f"apiRequest({{ method: 'GET', url: {url}, responseType: 'blob' }})"
    
    content = re.sub(
        r"api\.get\(([^,]+),\s*\{\s*responseType:\s*'blob'\s*\}\)",
        replace_api_get_blob_simple,
        content
    )
    
    # api.get(url, { params: P }) → get(url, P)
    def replace_api_get_params(match):
        url = match.group(1)
        params = match.group(2)
        return f'get({url}, {params})'
    
    content = re.sub(
        r"api\.get\(([^,]+),\s*\{\s*params:\s*(\{[^}]+\})\s*\}\)",
        replace_api_get_params,
        content
    )
    
    # api.get(url, { params }) → get(url, params)  (where params is a variable)
    content = re.sub(
        r"api\.get\(([^,]+),\s*\{\s*params\s*\}\)",
        r'get(\1, params)',
        content
    )
    
    # api.get(url, { params: P, ...other }) where other is not responseType
    # This is harder - skip for now, handle manually
    
    # api.get(url) → get(url)  (simple, no second arg)
    content = re.sub(r'\bapi\.get\(', 'get(', content)
    
    # api.post(url, data) → post(url, data)
    content = re.sub(r'\bapi\.post\(', 'post(', content)
    
    # api.put(url, data) → put(url, data)
    content = re.sub(r'\bapi\.put\(', 'put(', content)
    
    # api.delete(url) → del(url)
    content = re.sub(r'\bapi\.delete\(', 'del(', content)
    
    # api.patch(url, data) → patch(url, data)
    content = re.sub(r'\bapi\.patch\(', 'patch(', content)
    
    return content


def remove_unwrap_chains(content: str) -> str:
    """
    Remove .then((r: any) => r.data) chains since get/post/put already return unwrapped data.
    Also handle .then((r) => r.data) and .then(r => r.data)
    """
    # .then((r: any) => r.data) → remove
    content = re.sub(
        r"\.then\(\(r:\s*any\)\s*=>\s*r\.data\)",
        "",
        content
    )
    # .then((r) => r.data) → remove
    content = re.sub(
        r"\.then\(\(r\)\s*=>\s*r\.data\)",
        "",
        content
    )
    # .then(r => r.data) → remove
    content = re.sub(
        r"\.then\(r\s*=>\s*r\.data\)",
        "",
        content
    )
    
    return content


def process_file(filepath: Path) -> bool:
    try:
        content = filepath.read_text(encoding='utf-8')
    except:
        return False
    
    # Check if file uses `import api from`
    if not re.search(r"import api(,|\s)from\s*['\"](?:\./|@/api/)request['\"]", content):
        return False
    
    # Check if file actually uses api.get/post/put/delete/patch/apiRequest
    if not re.search(r'\bapi\.(get|post|put|delete|patch|apiRequest)\b', content):
        return False
    
    original = content
    needed = determine_needed_imports(content)
    
    if not needed:
        return False
    
    content = transform_import(content, needed)
    content = transform_api_calls(content)
    content = remove_unwrap_chains(content)
    
    if content != original:
        filepath.write_text(content, encoding='utf-8')
        changed_files.append(str(filepath))
        return True
    return False


def main():
    print("=" * 70)
    print("Migrate api.* imports to named imports")
    print("=" * 70)
    
    files = []
    for ext in ['*.vue', '*.ts']:
        files.extend(FRONTEND_SRC.rglob(ext))
    
    print(f"\nScanning {len(files)} files...\n")
    
    for filepath in sorted(files):
        if 'node_modules' in str(filepath) or 'dist' in str(filepath):
            continue
        if '__tests__' in str(filepath) or '.spec.' in str(filepath):
            continue  # Skip test files
        process_file(filepath)
    
    print(f"\nChanged {len(changed_files)} files:")
    for f in changed_files:
        print(f"  ✓ {f}")
    
    # Verify
    print("\nVerification: checking for remaining `import api from`...")
    remaining = []
    for filepath in sorted(FRONTEND_SRC.rglob('*')):
        if filepath.suffix not in ('.vue', '.ts'):
            continue
        if 'node_modules' in str(filepath) or 'dist' in str(filepath):
            continue
        if '__tests__' in str(filepath) or '.spec.' in str(filepath):
            continue
        try:
            content = filepath.read_text(encoding='utf-8')
            if re.search(r"import api(,|\s)from\s*['\"](?:\./|@/api/)request['\"]", content):
                remaining.append(str(filepath))
        except:
            pass
    
    if remaining:
        print(f"  ⚠ {len(remaining)} files still have `import api from`:")
        for f in remaining:
            print(f"    - {f}")
    else:
        print("  ✓ No remaining `import api from` found!")
    
    # Check for remaining api.get/post/put/delete
    print("\nVerification: checking for remaining `api.get/post/put/delete` calls...")
    remaining_calls = []
    for filepath in sorted(FRONTEND_SRC.rglob('*')):
        if filepath.suffix not in ('.vue', '.ts'):
            continue
        if 'node_modules' in str(filepath) or 'dist' in str(filepath):
            continue
        if '__tests__' in str(filepath) or '.spec.' in str(filepath):
            continue
        try:
            content = filepath.read_text(encoding='utf-8')
            if re.search(r'\bapi\.(get|post|put|delete|patch)\b', content):
                remaining_calls.append(str(filepath))
        except:
            pass
    
    if remaining_calls:
        print(f"  ⚠ {len(remaining_calls)} files still have `api.get/post/put/delete` calls:")
        for f in remaining_calls:
            print(f"    - {f}")
    else:
        print("  ✓ No remaining `api.get/post/put/delete` calls found!")


if __name__ == '__main__':
    main()
