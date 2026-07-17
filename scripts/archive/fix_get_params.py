#!/usr/bin/env python3
"""
Fix remaining issues from the first migration pass:
1. Unwrap { params: { ... } } → { ... } in get() calls
2. Convert get() calls with responseType/timeout to apiRequest()
3. Fix response access patterns
"""

import re
from pathlib import Path

FRONTEND_SRC = Path(__file__).parent.parent / "frontend" / "src"
changed_files = []


def fix_get_with_params_wrapper(content: str) -> str:
    """
    Fix: get(url, { params: { ... } })
    → get(url, { ... })
    
    Handles both single-line and multi-line cases, including trailing commas.
    """
    # Multi-line pattern: get(url, { params: { ... } }) where ... may span lines
    # The key insight: we need to match the balanced braces for the inner object
    
    # Strategy: find get( calls with params: wrapper and unwrap
    def replace_params_wrapper(match):
        url = match.group(1)
        inner = match.group(2)  # The content inside { params: { ... } }
        return f'get({url}, {inner})'
    
    # Pattern: get(url, { params: { ANYTHING } })
    # Use a greedy match for the inner content since we need to find the matching }
    # We'll use a different approach: find get(url, { params: { and then find the matching }s
    
    # Simpler approach: match get(url, {\n params: { ... } \n}) and unwrap
    # The inner object can contain nested braces, so we need balanced matching
    
    # Let's use a different approach: find all get() calls that have params: wrapper
    # and manually unwrap them
    
    lines = content.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this line has get(url, { with params: on next line(s)
        # Pattern: get('url', {  followed by  params: { ... }  followed by  })
        get_match = re.search(r"\bget\(([^,]+),\s*\{$", line)
        if get_match:
            url = get_match.group(1)
            # Look ahead for params: {
            j = i + 1
            if j < len(lines) and re.search(r'\bparams:\s*\{', lines[j]):
                # Found params wrapper - need to unwrap
                # Find the matching closing braces
                # Count braces from the params: { line
                brace_count = 0
                found_params_open = False
                inner_lines = []
                closing_line_idx = None
                
                for k in range(j, len(lines)):
                    for char in lines[k]:
                        if char == '{':
                            brace_count += 1
                            found_params_open = True
                        elif char == '}':
                            brace_count -= 1
                    
                    if found_params_open and brace_count <= 0:
                        # We've closed all braces including the outer wrapper
                        # The inner content is from j+1 to k (excluding the outer })
                        # But we need to figure out which } closes the inner vs outer
                        
                        # Re-parse: the structure is:
                        # line j: "  params: {"  → opens inner brace
                        # lines j+1 to k-1: inner content
                        # line k: "  }" or "  },}" or similar → closes inner brace
                        # Then we need the outer } to close the wrapper
                        
                        # Let's just rebuild the get() call properly
                        # Extract inner object content (between params: { and the matching })
                        inner_text = '\n'.join(lines[j:k+1])
                        # Remove "params: " prefix and the outer braces
                        inner_text = re.sub(r'^\s*params:\s*\{', '{', inner_text)
                        
                        # Find the last } that closes the inner object
                        # and remove the trailing wrapper }
                        # The structure is: { inner_content }
                        # followed by optional , and the wrapper }
                        
                        # Count braces in inner_text
                        count = 0
                        last_close = -1
                        for idx, char in enumerate(inner_text):
                            if char == '{':
                                count += 1
                            elif char == '}':
                                count -= 1
                                if count == 0:
                                    last_close = idx
                                    break
                        
                        if last_close >= 0:
                            # Extract just the inner object
                            inner_obj = inner_text[:last_close+1]
                            # Check if there's responseType or timeout after
                            remaining = inner_text[last_close+1:].strip()
                            
                            if remaining.startswith(','):
                                remaining = remaining[1:].strip()
                            
                            if remaining.startswith('}'):
                                remaining = remaining[1:].strip()
                            
                            if remaining:
                                # There are extra config options like responseType
                                # Need to use apiRequest instead
                                # For now, just append them
                                result.append(f'{line[:get_match.start()]}apiRequest({{ method: \'GET\', url: {url}, params: {inner_obj[1:-1].strip() if inner_obj.startswith("{") else inner_obj}, {remaining}')
                            else:
                                result.append(f'{line[:get_match.start()]}get({url}, {inner_obj})')
                            
                            # Skip to after the closing
                            i = k + 1
                            break
                else:
                    result.append(line)
                    i += 1
            else:
                result.append(line)
                i += 1
        else:
            result.append(line)
            i += 1
    
    return '\n'.join(result)


def fix_get_with_response_type(content: str) -> str:
    """
    Convert get(url, { responseType: 'blob' }) to apiRequest({ method: 'GET', url, responseType: 'blob' })
    Also handle get(url, { params: {...}, responseType: 'blob' })
    """
    
    # Pattern: get(url, { responseType: 'blob' })
    def replace_simple_blob(match):
        url = match.group(1)
        return f"apiRequest({{ method: 'GET', url: {url}, responseType: 'blob' }})"
    
    content = re.sub(
        r"get\(([^,)]+),\s*\{\s*responseType:\s*'blob'\s*\}\)",
        replace_simple_blob,
        content
    )
    
    # Pattern: get(url, { responseType: 'blob', timeout: N })
    def replace_blob_timeout(match):
        url = match.group(1)
        timeout = match.group(2)
        return f"apiRequest({{ method: 'GET', url: {url}, responseType: 'blob', timeout: {timeout} }})"
    
    content = re.sub(
        r"get\(([^,)]+),\s*\{\s*responseType:\s*'blob',\s*timeout:\s*(\d+)\s*\}\)",
        replace_blob_timeout,
        content
    )
    
    return content


def fix_response_access_patterns(content: str) -> str:
    """Fix common response access patterns that were missed."""
    
    # Pattern: const { data } = await get(...) → const data = await get(...)
    content = re.sub(
        r"const\s*\{\s*data\s*\}\s*=\s*await\s+(get|post|put|del)\(",
        r"const data = await \1(",
        content
    )
    
    return content


def process_file(filepath: Path) -> bool:
    try:
        content = filepath.read_text(encoding='utf-8')
    except:
        return False
    
    original = content
    
    # Fix params wrapper
    content = fix_get_with_params_wrapper(content)
    
    # Fix responseType blob calls
    content = fix_get_with_response_type(content)
    
    # Fix response access
    content = fix_response_access_patterns(content)
    
    if content != original:
        filepath.write_text(content, encoding='utf-8')
        changed_files.append(str(filepath))
        return True
    return False


def main():
    print("=" * 70)
    print("Fix pass: unwrap params, fix responseType, fix response access")
    print("=" * 70)
    
    files = []
    for ext in ['*.vue', '*.ts']:
        files.extend(FRONTEND_SRC.rglob(ext))
    
    print(f"\nScanning {len(files)} files...\n")
    
    for filepath in sorted(files):
        if 'node_modules' in str(filepath) or 'dist' in str(filepath):
            continue
        process_file(filepath)
    
    print(f"\nFixed {len(changed_files)} files:")
    for f in changed_files:
        print(f"  ✓ {f}")
    
    # Verify: check for remaining params: wrapper in get() calls
    print("\nVerification: checking for remaining params: wrapper in get() calls...")
    remaining = []
    for filepath in sorted(FRONTEND_SRC.rglob('*')):
        if filepath.suffix not in ('.vue', '.ts'):
            continue
        if 'node_modules' in str(filepath) or 'dist' in str(filepath):
            continue
        try:
            content = filepath.read_text(encoding='utf-8')
            # Check for get(url, { params: pattern
            if re.search(r"\bget\([^)]+,\s*\{\s*params:", content):
                remaining.append(str(filepath))
        except:
            pass
    
    if remaining:
        print(f"  ⚠ {len(remaining)} files still have params: wrapper:")
        for f in remaining:
            print(f"    - {f}")
    else:
        print("  ✓ No remaining params: wrapper found!")


if __name__ == '__main__':
    main()
