#!/usr/bin/env python3
"""
Complete frontend request import migration - single pass, no follow-up fixes needed.
Handles: import request/api from, request.*/api.* calls, params wrapper, responseType blob,
response access patterns, and .then(r => r.data) chains.

Uses balanced paren/brace matching for multiline patterns instead of fragile regex.
"""
import re
from pathlib import Path

FRONTEND_SRC = Path(__file__).parent.parent / "frontend" / "src"


def find_matching_brace(text, start_idx, open_char='{', close_char='}'):
    """Find the matching closing brace starting from start_idx (which should be the opening brace)."""
    depth = 0
    i = start_idx
    while i < len(text):
        if text[i] == open_char:
            depth += 1
        elif text[i] == close_char:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def find_matching_paren(text, start_idx):
    """Find the matching closing paren starting from start_idx (which should be the opening paren)."""
    return find_matching_brace(text, start_idx, '(', ')')


def determine_needed_imports(content):
    """Determine which named exports are needed."""
    needed = set()
    # Check for request.* and api.* calls
    for pattern in [r'\brequest\.get\b', r'\bapi\.get\b']:
        if re.search(pattern, content):
            needed.add('get')
    for pattern in [r'\brequest\.post\b', r'\bapi\.post\b']:
        if re.search(pattern, content):
            needed.add('post')
    for pattern in [r'\brequest\.put\b', r'\bapi\.put\b']:
        if re.search(pattern, content):
            needed.add('put')
    for pattern in [r'\brequest\.delete\b', r'\bapi\.delete\b']:
        if re.search(pattern, content):
            needed.add('del')
    for pattern in [r'\brequest\.patch\b', r'\bapi\.patch\b']:
        if re.search(pattern, content):
            needed.add('patch')
    # Check for request({...}) function call pattern
    if re.search(r'\brequest\(\s*\{', content):
        needed.add('apiRequest')
    # Check for blob downloads (responseType: 'blob' in get calls)
    if re.search(r"(request|api)\.get\([^)]*responseType:\s*'blob'", content, re.DOTALL):
        needed.add('apiRequest')
    # Check for api.apiRequest
    if re.search(r'\bapi\.apiRequest\b', content):
        needed.add('apiRequest')
    return needed


def transform_imports(content, needed):
    """Transform all import patterns."""
    # Get existing named imports if any
    existing_named = set()
    for m in re.finditer(r"import\s+(?:request|api),\s*\{([^}]+)\}\s*from\s*['\"](?:\./|@/api/)request['\"]", content):
        for name in m.group(1).split(','):
            name = name.strip()
            if name:
                existing_named.add(name)
    
    needed = needed | existing_named
    
    # Build import string
    canonical_order = ['get', 'post', 'put', 'del', 'patch', 'apiRequest']
    imports = [name for name in canonical_order if name in needed]
    extras = needed - set(canonical_order)
    extra_order = ['parseContentDisposition', 'downloadBlob', 'cancelRequest', 'cancelAllRequests',
                   'isRequestCancelled', 'prefetchCsrfToken', 'createCancelableRequest',
                   'requestWithTimeout', 'isSuccess', '_setCachedToken', 'freezeRequests',
                   'unfreezeRequests', 'getPendingRequestCount', 'RequestConfig']
    for name in extra_order:
        if name in extras:
            imports.append(name)
            extras.discard(name)
    for name in sorted(extras):
        imports.append(name)
    
    if not imports:
        return content
    
    import_str = ', '.join(imports)
    
    # Pattern: import request, { named } from '...' or import api, { named } from '...'
    content = re.sub(
        r"import (?:request|api),\s*\{[^}]+\}\s*from\s*['\"](?:\./|@/api/)request['\"]",
        f"import {{ {import_str} }} from '@/api/request'",
        content
    )
    
    # Pattern: import request from '...' or import api from '...'
    content = re.sub(
        r"import (?:request|api)\s+from\s*['\"](?:\./|@/api/)request['\"]",
        f"import {{ {import_str} }} from '@/api/request'",
        content
    )
    
    return content


def transform_dynamic_imports(content):
    """Transform dynamic import patterns."""
    # const { default: request } = await import('@/api/request')
    content = re.sub(
        r"const\s*\{\s*default:\s*request\s*\}\s*=\s*await import\(['\"]@/api/request['\"]\)",
        "const { get } = await import('@/api/request')",
        content
    )
    # const { default: api } = await import('@/api/request')
    content = re.sub(
        r"const\s*\{\s*default:\s*api\s*\}\s*=\s*await import\(['\"]@/api/request['\"]\)",
        "const { get } = await import('@/api/request')",
        content
    )
    # m.default.get(url, ...) in dynamic import chains
    content = re.sub(
        r"m\.default\.get\b",
        "m.get",
        content
    )
    content = re.sub(
        r"m\.default\.post\b",
        "m.post",
        content
    )
    # m.default({...}) → m.apiRequest({...})
    content = re.sub(
        r"m\.default\(",
        "m.apiRequest(",
        content
    )
    return content


def transform_get_calls(content):
    """Transform request.get and api.get calls using balanced paren matching."""
    result = []
    i = 0
    
    while i < len(content):
        # Find request.get( or api.get(
        match = re.search(r'\b(?:request|api)\.get\(', content[i:])
        if not match:
            result.append(content[i:])
            break
        
        # Append content before the match
        start = i + match.start()
        result.append(content[i:start])
        
        # Find the opening paren
        paren_start = i + match.end() - 1
        paren_end = find_matching_paren(content, paren_start)
        if paren_end == -1:
            result.append(content[start:])
            break
        
        # Extract the full call content between parens
        call_content = content[paren_start+1:paren_end]
        
        # Parse the call content to find URL and config
        # The URL is the first argument (string or template literal)
        # The config is the second argument (object)
        
        # Find the first argument (URL)
        url_end = find_first_arg_end(call_content)
        if url_end == -1:
            # Single argument - just replace request.get/api.get with get
            replacement = f"get({call_content})"
            result.append(replacement)
            i = paren_end + 1
            continue
        
        url = call_content[:url_end].strip()
        rest = call_content[url_end:].lstrip()
        if rest.startswith(','):
            rest = rest[1:].lstrip()
        
        if not rest:
            # Only URL, no config
            replacement = f"get({url})"
            result.append(replacement)
            i = paren_end + 1
            continue
        
        # Check if rest is an object (starts with {)
        if rest.startswith('{'):
            brace_start = call_content.index('{', url_end)
            brace_end = find_matching_brace(call_content, brace_start)
            if brace_end == -1:
                result.append(f"get({call_content})")
                i = paren_end + 1
                continue
            
            config_str = call_content[brace_start:brace_end+1]
            
            # Check for responseType: 'blob'
            has_blob = "responseType: 'blob'" in config_str or "responseType:'blob'" in config_str
            
            # Check for params: wrapper
            params_match = re.search(r'\bparams:\s*', config_str)
            has_showError = 'showError' in config_str
            
            if has_blob:
                # Convert to apiRequest
                params_val = 'undefined'
                if params_match:
                    # Extract the params value
                    after_params = config_str[params_match.end():]
                    # Find the value (until next comma or closing brace)
                    if after_params.startswith('{'):
                        val_end = find_matching_brace(after_params, 0)
                        params_val = after_params[:val_end+1]
                    else:
                        # Simple value (variable, etc.)
                        comma_idx = after_params.find(',')
                        if comma_idx == -1:
                            params_val = after_params.rstrip(' }').strip()
                        else:
                            params_val = after_params[:comma_idx].strip()
                
                replacement = f"apiRequest({{ method: 'GET', url: {url}, params: {params_val}, responseType: 'blob' }})"
                result.append(replacement)
                i = paren_end + 1
                continue
            
            elif params_match and not has_showError:
                # Unwrap params: { ... } → { ... }
                after_params = config_str[params_match.end():]
                if after_params.startswith('{'):
                    # params: { ... } - extract the inner object
                    val_end = find_matching_brace(after_params, 0)
                    inner_params = after_params[:val_end+1]
                    
                    # Check if there's more after the params object
                    remaining = after_params[val_end+1:].strip()
                    remaining = remaining.rstrip(',').strip()
                    remaining = remaining.rstrip('}').strip()
                    
                    if remaining:
                        # There are other config options (e.g., timeout)
                        # Use apiRequest instead
                        replacement = f"apiRequest({{ method: 'GET', url: {url}, params: {inner_params}, {remaining} }})"
                    else:
                        replacement = f"get({url}, {inner_params})"
                    
                    result.append(replacement)
                    i = paren_end + 1
                    continue
                else:
                    # params: variable (shorthand or explicit)
                    comma_idx = after_params.find(',')
                    if comma_idx == -1:
                        params_val = after_params.rstrip(' }').strip()
                    else:
                        params_val = after_params[:comma_idx].strip()
                    
                    replacement = f"get({url}, {params_val})"
                    result.append(replacement)
                    i = paren_end + 1
                    continue
            
            elif has_showError:
                # Drop useless showError config
                replacement = f"get({url})"
                result.append(replacement)
                i = paren_end + 1
                continue
            
            else:
                # Other config object - pass as params (might be wrong but better than crashing)
                # Actually, if it's not params and not responseType, it's probably being used as params
                # by the caller. Let's just pass it through.
                replacement = f"get({url}, {config_str})"
                result.append(replacement)
                i = paren_end + 1
                continue
        else:
            # Second argument is not an object - just replace the method name
            replacement = f"get({call_content})"
            result.append(replacement)
            i = paren_end + 1
            continue
    
    return ''.join(result)


def find_first_arg_end(text):
    """Find the end index of the first argument in a function call string."""
    # Handle string literals and template literals
    i = 0
    while i < len(text):
        c = text[i]
        if c == ',':
            return i
        elif c == "'" or c == '"':
            # Skip string literal
            quote = c
            i += 1
            while i < len(text) and text[i] != quote:
                if text[i] == '\\':
                    i += 1
                i += 1
            i += 1
        elif c == '`':
            # Skip template literal
            i += 1
            while i < len(text) and text[i] != '`':
                if text[i] == '\\':
                    i += 1
                i += 1
            i += 1
        elif c == '(':
            # Skip nested parens
            end = find_matching_paren(text, i)
            if end == -1:
                return -1
            i = end + 1
        elif c == '{':
            # Skip nested braces
            end = find_matching_brace(text, i)
            if end == -1:
                return -1
            i = end + 1
        else:
            i += 1
    return -1  # No comma found - single argument


def transform_other_calls(content):
    """Transform request.post/put/delete/patch and api.post/put/delete/patch calls."""
    # Simple replacements - these methods take the same args in both patterns
    content = re.sub(r'\brequest\.post\b', 'post', content)
    content = re.sub(r'\bapi\.post\b', 'post', content)
    content = re.sub(r'\brequest\.put\b', 'put', content)
    content = re.sub(r'\bapi\.put\b', 'put', content)
    content = re.sub(r'\brequest\.delete\b', 'del', content)
    content = re.sub(r'\bapi\.delete\b', 'del', content)
    content = re.sub(r'\brequest\.patch\b', 'patch', content)
    content = re.sub(r'\bapi\.patch\b', 'patch', content)
    content = re.sub(r'\bapi\.apiRequest\b', 'apiRequest', content)
    
    # request({...}) function call → apiRequest({...})
    # Match request( followed by { (not .get or .post etc.)
    content = re.sub(r'\brequest\(\s*\{', 'apiRequest({', content)
    
    return content


def transform_response_access(content):
    """Transform response access patterns."""
    # const { data } = await get/post/put/del(...)
    content = re.sub(
        r"const\s*\{\s*data\s*\}\s*=\s*await\s+(get|post|put|del|patch)\(",
        r"const data = await \1(",
        content
    )
    
    # res.data?.data || res.data || [] → res.data || res || []
    content = re.sub(
        r"(\w+)\.data\?\.data\s*\|\|\s*\1\.data\s*\|\|\s*\[\]",
        r"\1.data || \1 || []",
        content
    )
    
    # res.data?.data || res.data → res.data || res
    content = re.sub(
        r"(\w+)\.data\?\.data\s*\|\|\s*\1\.data(?!\s*\|\|)",
        r"\1.data || \1",
        content
    )
    
    # res.data?.data?.field || res.data?.field → res.data?.field || res.field
    content = re.sub(
        r"(\w+)\.data\?\.data\?\.(\w+)\s*\|\|\s*\1\.data\?\.(\w+)",
        r"\1.data?.\2 || \1.\3",
        content
    )
    
    # response?.data || response → response (only when response was assigned from get/post/etc)
    content = re.sub(
        r"(\w+)\?\.data\s*\|\|\s*\1\b(?!\s*\.data)",
        r"\1",
        content
    )
    
    # .then((r: any) => r.data) → remove (get/post already unwraps)
    content = re.sub(r"\.then\(\(r:\s*any\)\s*=>\s*r\.data\)", "", content)
    content = re.sub(r"\.then\(\(r\)\s*=>\s*r\.data\)", "", content)
    content = re.sub(r"\.then\(r\s*=>\s*r\.data\)", "", content)
    
    return content


def ensure_imports(content):
    """Ensure apiRequest is imported if it's used."""
    if 'apiRequest(' in content:
        # Check if already imported
        if not re.search(r"import\s+\{[^}]*apiRequest[^}]*\}\s*from\s*['\"](?:\./|@/api/)request['\"]", content):
            # Add apiRequest to existing import
            content = re.sub(
                r"(import\s+\{)([^}]*)(\}\s*from\s*['\"](?:\./|@/api/)request['\"])",
                lambda m: f"{m.group(1)}{m.group(2)}, apiRequest{m.group(3)}" if 'apiRequest' not in m.group(2) else m.group(0),
                content
            )
    return content


def process_file(filepath):
    try:
        content = filepath.read_text(encoding='utf-8')
    except:
        return False
    
    # Check if file needs migration
    has_request_import = bool(re.search(r"import (?:request|api)(?:,|\s)from\s*['\"](?:\./|@/api/)request['\"]", content))
    has_dynamic_import = bool(re.search(r"const\s*\{\s*default:\s*(?:request|api)\s*\}\s*=\s*await import", content))
    has_request_calls = bool(re.search(r'\brequest\.(get|post|put|delete|patch)\b', content)) or bool(re.search(r'\brequest\(\s*\{', content))
    has_api_calls = bool(re.search(r'\bapi\.(get|post|put|delete|patch|apiRequest)\b', content))
    
    if not (has_request_import or has_dynamic_import or has_request_calls or has_api_calls):
        return False
    
    # Skip test files
    if '__tests__' in str(filepath) or '.spec.' in str(filepath):
        return False
    
    original = content
    
    # Determine needed imports
    needed = determine_needed_imports(content)
    
    # Transform imports
    content = transform_imports(content, needed)
    
    # Transform dynamic imports
    content = transform_dynamic_imports(content)
    
    # Transform get calls (most complex - uses balanced paren matching)
    content = transform_get_calls(content)
    
    # Transform other method calls (post, put, delete, patch)
    content = transform_other_calls(content)
    
    # Transform response access patterns
    content = transform_response_access(content)
    
    # Ensure apiRequest is imported if needed
    content = ensure_imports(content)
    
    if content != original:
        filepath.write_text(content, encoding='utf-8')
        return True
    return False


def main():
    print("=" * 70)
    print("Complete frontend request import migration (single pass)")
    print("=" * 70)
    
    files = []
    for ext in ['*.vue', '*.ts']:
        files.extend(FRONTEND_SRC.rglob(ext))
    
    print(f"\nScanning {len(files)} files...\n")
    
    changed = 0
    for filepath in sorted(files):
        if 'node_modules' in str(filepath) or 'dist' in str(filepath):
            continue
        if '__tests__' in str(filepath) or '.spec.' in str(filepath):
            continue
        if process_file(filepath):
            changed += 1
            print(f"  ✓ {filepath.relative_to(FRONTEND_SRC)}")
    
    print(f"\n{'=' * 70}")
    print(f"Migration complete! Changed {changed} files.")
    
    # Verify
    print("\nVerification:")
    remaining_request = 0
    remaining_api = 0
    for filepath in sorted(FRONTEND_SRC.rglob('*')):
        if filepath.suffix not in ('.vue', '.ts'):
            continue
        if 'node_modules' in str(filepath) or 'dist' in str(filepath):
            continue
        if '__tests__' in str(filepath) or '.spec.' in str(filepath):
            continue
        try:
            content = filepath.read_text(encoding='utf-8')
            if re.search(r"import (?:request|api)(?:,|\s)from\s*['\"](?:\./|@/api/)request['\"]", content):
                remaining_request += 1
                print(f"  ⚠ Still has import: {filepath.relative_to(FRONTEND_SRC)}")
            if re.search(r'\b(?:request|api)\.(get|post|put|delete|patch)\b', content):
                remaining_api += 1
        except:
            pass
    
    if remaining_request == 0:
        print("  ✓ No remaining `import request/api from` found!")
    if remaining_api == 0:
        print("  ✓ No remaining `request.*/api.*` method calls found!")


if __name__ == '__main__':
    main()
