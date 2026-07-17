#!/usr/bin/env python3
"""
Migrate frontend files from raw `import request from '@/api/request'` (Pattern A)
to auto-unwrapped `import { get, post, put, del, apiRequest } from '@/api/request'` (Pattern B).

Pattern A (raw axios):                Pattern B (auto-unwrapped):
  request.get(url, {params:{...}})  → get(url, {...})
  request.get(url)                  → get(url)
  request.post(url, data)           → post(url, data)
  request.post(url, data, {h:...})  → post(url, data, {h:...})
  request.put(url, data)            → put(url, data)
  request.delete(url)               → del(url)
  request.patch(url, data)          → patch(url, data)

Response access changes:
  res.data?.data || res.data        → res.data || res
  res.data?.data                    → res.data
  response.data.xxx                 → response.xxx
  const {data} = await request.get  → const data = await get
"""

import re
import os
import sys
from pathlib import Path

FRONTEND_SRC = Path(__file__).parent.parent / "frontend" / "src"

# Track files changed
changed_files = []
skipped_files = []


def determine_needed_imports(content: str) -> set:
    """Determine which named exports are needed based on usage."""
    needed = set()
    if re.search(r'\brequest\.get\b', content):
        needed.add('get')
    if re.search(r'\brequest\.post\b', content):
        needed.add('post')
    if re.search(r'\brequest\.put\b', content):
        needed.add('put')
    if re.search(r'\brequest\.delete\b', content):
        needed.add('del')
    if re.search(r'\brequest\.patch\b', content):
        needed.add('patch')
    # Always include apiRequest for edge cases with custom configs
    if re.search(r'\brequest\.get\b.*\bshowError\b', content):
        needed.add('apiRequest')
    return needed


def transform_import_line(content: str, needed: set) -> str:
    """Replace the import line."""
    # Sort imports in canonical order
    order = ['get', 'post', 'put', 'del', 'patch', 'apiRequest']
    imports = [name for name in order if name in needed]
    import_str = ', '.join(imports)

    # Match: import request from '@/api/request'
    # Also: import request from "./request"
    pattern = r"""import request from ['"]@/api/request['"]"""
    replacement = f"import {{ {import_str} }} from '@/api/request'"
    content = re.sub(pattern, replacement, content)

    # Also handle: import request from './request'
    pattern2 = r"""import request from ['"]\./request['"]"""
    if re.search(pattern2, content):
        content = re.sub(pattern2, replacement, content)

    return content


def transform_get_calls(content: str) -> str:
    """Transform request.get() calls to get() calls."""

    # Pattern: request.get(url, { params: { ... } })
    # → get(url, { ... })
    def replace_get_with_params(match):
        url = match.group(1)
        params_body = match.group(2)
        return f'get({url}, {params_body})'

    # Match request.get('url', { params: { ... } }) - single line
    content = re.sub(
        r"request\.get\(([^,]+),\s*\{\s*params:\s*(\{[^}]+\})\s*\}\)",
        replace_get_with_params,
        content
    )

    # Match request.get('url', { params: { ... } }) - multiline params
    # This is trickier - need to handle multiline
    def replace_multiline_get_params(match):
        url = match.group(1)
        params_content = match.group(2)
        return f'get({url}, {params_content})'

    content = re.sub(
        r"request\.get\(([^,]+),\s*\{\s*params:\s*(\{[\s\S]*?\})\s*\}\)",
        replace_multiline_get_params,
        content
    )

    # Pattern: request.get(url, { showError: false } as any)
    # → apiRequest({ method: 'GET', url })  (drop useless showError)
    content = re.sub(
        r"request\.get\(([^,)]+),\s*\{\s*showError:\s*false\s*\}\s*as\s*any\)",
        lambda m: f"apiRequest({{ method: 'GET', url: {m.group(1)} }})",
        content
    )

    # Pattern: request.get(url) - simple, no second arg
    # Be careful not to match already-transformed get() calls
    content = re.sub(
        r"\brequest\.get\(([^)]+)\)",
        lambda m: f"get({m.group(1)})",
        content
    )

    return content


def transform_post_calls(content: str) -> str:
    """Transform request.post() calls to post() calls."""

    # Pattern: request.post(url, data, { headers: ... })
    # → post(url, data, { headers: ... })
    # This is handled by simple replacement since post() accepts 3rd arg

    # Pattern: request.post(url, data)
    # → post(url, data)
    content = re.sub(
        r"\brequest\.post\b",
        "post",
        content
    )

    return content


def transform_put_calls(content: str) -> str:
    """Transform request.put() calls to put() calls."""
    content = re.sub(r"\brequest\.put\b", "put", content)
    return content


def transform_delete_calls(content: str) -> str:
    """Transform request.delete() calls to del() calls."""
    content = re.sub(r"\brequest\.delete\b", "del", content)
    return content


def transform_patch_calls(content: str) -> str:
    """Transform request.patch() calls to patch() calls."""
    content = re.sub(r"\brequest\.patch\b", "patch", content)
    return content


def transform_response_access(content: str) -> str:
    """
    Transform response access patterns.
    
    Key insight: In Pattern A, `const res = await request.get(url)` returns AxiosResponse.
    In Pattern B, `const res = await get(url)` returns res.data (the body) directly.
    
    So `res.data` in Pattern A → `res` in Pattern B (accessing the body).
    But `res.data.data` in Pattern A → `res.data` in Pattern B (accessing inner data field).
    """
    
    # Pattern: const { data } = await request.get/post/put(...)
    # → const data = await get/post/put(...)
    # This works because get() already returns the unwrapped data
    content = re.sub(
        r"const\s*\{\s*data\s*\}\s*=\s*await\s+(get|post|put|del|patch)\(",
        r"const data = await \1(",
        content
    )

    # Pattern: res.data?.data || res.data || []
    # → res.data || res || []
    content = re.sub(
        r"(\w+)\.data\?\.data\s*\|\|\s*\1\.data\s*\|\|\s*\[\]",
        r"\1.data || \1 || []",
        content
    )

    # Pattern: res.data?.data || res.data
    # → res.data || res
    content = re.sub(
        r"(\w+)\.data\?\.data\s*\|\|\s*\1\.data",
        r"\1.data || \1",
        content
    )

    # Pattern: res.data?.data?.message || res.data?.message
    # → res.data?.message || res.message
    content = re.sub(
        r"(\w+)\.data\?\.data\?\.(\w+)\s*\|\|\s*\1\.data\?\.(\w+)",
        r"\1.data?.\2 || \1.\3",
        content
    )

    # Pattern: response?.data || response
    # → response (since get() returns the body directly)
    # But we need to be careful - this could match other patterns
    # Only apply when the variable was assigned from get/post/put/del
    content = re.sub(
        r"(\w+)\?\.data\s*\|\|\s*\1\b",
        r"\1",
        content
    )

    # Pattern: response.data?.data → response.data
    content = re.sub(
        r"(\w+)\.data\?\.data(?!\?)(?!\s*\|\|)",
        r"\1.data",
        content
    )

    # Pattern: response.data?.data?.field → response.data?.field
    content = re.sub(
        r"(\w+)\.data\?\.data\?\.(\w+)",
        r"\1.data?.\2",
        content
    )

    return content


def transform_cancel_token(content: str) -> str:
    """Transform request.CancelToken.source() and request.isCancel() if used."""
    # These are axios static methods, not instance methods
    # request.CancelToken.source() → axios.CancelToken.source()
    # request.isCancel() → axios.isCancel()
    if 'request.CancelToken' in content or 'request.isCancel' in content:
        # Need to add axios import
        if "import axios" not in content:
            content = re.sub(
                r"(import \{[^}]+\} from '@/api/request')",
                r"import axios from 'axios'\n\1",
                content
            )
        content = content.replace('request.CancelToken', 'axios.CancelToken')
        content = content.replace('request.isCancel', 'axios.isCancel')
    return content


def process_file(filepath: Path) -> bool:
    """Process a single file. Returns True if changed."""
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        print(f"  ERROR reading {filepath}: {e}")
        return False

    # Check if file uses `import request from`
    if not re.search(r"""import request from ['"]@/api/request['"]""", content) and \
       not re.search(r"""import request from ['"]\./request['"]""", content):
        return False

    # Check if file actually uses request.get/post/put/delete/patch
    if not re.search(r'\brequest\.(get|post|put|delete|patch)\b', content):
        print(f"  SKIP {filepath.name}: imports request but doesn't use HTTP methods")
        skipped_files.append(str(filepath))
        return False

    original = content

    # Determine needed imports
    needed = determine_needed_imports(content)
    if not needed:
        print(f"  SKIP {filepath.name}: no HTTP method calls found")
        skipped_files.append(str(filepath))
        return False

    # Transform
    content = transform_import_line(content, needed)
    content = transform_get_calls(content)
    content = transform_post_calls(content)
    content = transform_put_calls(content)
    content = transform_delete_calls(content)
    content = transform_patch_calls(content)
    content = transform_response_access(content)
    content = transform_cancel_token(content)

    if content != original:
        filepath.write_text(content, encoding='utf-8')
        changed_files.append(str(filepath))
        return True
    return False


def main():
    print("=" * 70)
    print("Frontend request import migration: Pattern A → Pattern B")
    print("=" * 70)

    # Find all .vue and .ts files
    files = []
    for ext in ['*.vue', '*.ts']:
        files.extend(FRONTEND_SRC.rglob(ext))

    print(f"\nFound {len(files)} files to check...\n")

    for filepath in sorted(files):
        # Skip node_modules, dist, test files
        rel = str(filepath.relative_to(FRONTEND_SRC.parent))
        if 'node_modules' in rel or 'dist/' in rel:
            continue
        process_file(filepath)

    print(f"\n{'=' * 70}")
    print(f"Migration complete!")
    print(f"  Changed: {len(changed_files)} files")
    print(f"  Skipped: {len(skipped_files)} files")
    print(f"{'=' * 70}\n")

    if changed_files:
        print("Changed files:")
        for f in changed_files:
            print(f"  ✓ {f}")

    # Verify no remaining `import request from`
    print("\nVerification: checking for remaining `import request from`...")
    remaining = []
    for filepath in sorted(FRONTEND_SRC.rglob('*')):
        if filepath.suffix not in ('.vue', '.ts'):
            continue
        if 'node_modules' in str(filepath) or 'dist' in str(filepath):
            continue
        try:
            content = filepath.read_text(encoding='utf-8')
            if re.search(r"""import request from ['"]@/api/request['"]""", content) or \
               re.search(r"""import request from ['"]\./request['"]""", content):
                remaining.append(str(filepath))
        except:
            pass

    if remaining:
        print(f"\n  ⚠ {len(remaining)} files still have `import request from`:")
        for f in remaining:
            print(f"    - {f}")
    else:
        print("  ✓ No remaining `import request from` found!")


if __name__ == '__main__':
    main()
