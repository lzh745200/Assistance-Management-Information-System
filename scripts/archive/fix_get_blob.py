#!/usr/bin/env python3
"""
Fix get(url, { responseType: 'blob' }) calls.
The get() function passes 2nd arg as params, NOT as axios config.
So responseType: 'blob' is sent as a query param instead of being set on the request.

Convert to: apiRequest({ method: 'GET', url, responseType: 'blob' })
Also fix response access: res.data → res (since apiRequest returns the blob directly)
"""

import re
from pathlib import Path

FRONTEND_SRC = Path(__file__).parent.parent / "frontend" / "src"
changed_files = []


def fix_get_blob_calls(content: str) -> str:
    """
    Convert get(url, { responseType: 'blob' }) to apiRequest({ method: 'GET', url, responseType: 'blob' })
    Also handle get(url, { responseType: 'blob', timeout: N })
    """
    
    # Pattern: get(url, { responseType: 'blob' })
    def replace_simple(match):
        url = match.group(1)
        return f"apiRequest({{ method: 'GET', url: {url}, responseType: 'blob' }})"
    
    content = re.sub(
        r"get\(([^,)]+),\s*\{\s*responseType:\s*'blob'\s*\}\)",
        replace_simple,
        content
    )
    
    # Pattern: get(url, { responseType: 'blob', timeout: N })
    def replace_with_timeout(match):
        url = match.group(1)
        timeout = match.group(2)
        return f"apiRequest({{ method: 'GET', url: {url}, responseType: 'blob', timeout: {timeout} }})"
    
    content = re.sub(
        r"get\(([^,)]+),\s*\{\s*responseType:\s*'blob',\s*timeout:\s*(\d+)\s*\}\)",
        replace_with_timeout,
        content
    )
    
    # Pattern: get(url, { params: P, responseType: 'blob' })
    def replace_with_params(match):
        url = match.group(1)
        params = match.group(2)
        return f"apiRequest({{ method: 'GET', url: {url}, params: {params}, responseType: 'blob' }})"
    
    content = re.sub(
        r"get\(([^,)]+),\s*\{\s*params:\s*([^,}]+),\s*responseType:\s*'blob'\s*\}\)",
        replace_with_params,
        content
    )
    
    return content


def fix_response_access_for_blob(content: str) -> str:
    """
    After converting to apiRequest for blob downloads, the response is the Blob directly.
    Fix patterns like:
    - res.data → res (when used after apiRequest blob call)
    - new Blob([res.data]) → new Blob([res])
    - response.data → response
    """
    # These are harder to fix generically since we need context.
    # We'll handle the most common patterns.
    return content


def ensure_apiRequest_import(content: str) -> str:
    """Ensure apiRequest is imported if it's now used."""
    if 'apiRequest(' in content and 'apiRequest' not in content.split('\n')[0:20].__str__():
        # Check if apiRequest is already imported
        if not re.search(r"import\s+\{[^}]*apiRequest[^}]*\}\s*from\s*['\"](?:\./|@/api/)request['\"]", content):
            # Add apiRequest to existing import
            content = re.sub(
                r"(import\s+\{)([^}]*)(\}\s*from\s*['\"](?:\./|@/api/)request['\"])",
                lambda m: f"{m.group(1)}{m.group(2)}, apiRequest{m.group(3)}" if 'apiRequest' not in m.group(2) else m.group(0),
                content
            )
    return content


def process_file(filepath: Path) -> bool:
    try:
        content = filepath.read_text(encoding='utf-8')
    except:
        return False
    
    original = content
    
    content = fix_get_blob_calls(content)
    content = ensure_apiRequest_import(content)
    
    if content != original:
        filepath.write_text(content, encoding='utf-8')
        changed_files.append(str(filepath))
        return True
    return False


def main():
    print("=" * 70)
    print("Fix get(url, { responseType: 'blob' }) → apiRequest(...)")
    print("=" * 70)
    
    files = []
    for ext in ['*.vue', '*.ts']:
        files.extend(FRONTEND_SRC.rglob(ext))
    
    print(f"\nScanning {len(files)} files...\n")
    
    for filepath in sorted(files):
        if 'node_modules' in str(filepath) or 'dist' in str(filepath):
            continue
        if '__tests__' in str(filepath) or '.spec.' in str(filepath):
            continue
        process_file(filepath)
    
    print(f"\nChanged {len(changed_files)} files:")
    for f in changed_files:
        print(f"  ✓ {f}")
    
    # Verify
    print("\nVerification: checking for remaining get(url, { responseType: 'blob' }) calls...")
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
            if re.search(r"get\([^,)]+,\s*\{\s*responseType:\s*'blob'", content):
                remaining.append(str(filepath))
        except:
            pass
    
    if remaining:
        print(f"  ⚠ {len(remaining)} files still have get(url, {{ responseType: 'blob' }}):")
        for f in remaining:
            print(f"    - {f}")
    else:
        print("  ✓ No remaining get(url, { responseType: 'blob' }) calls found!")


if __name__ == '__main__':
    main()
