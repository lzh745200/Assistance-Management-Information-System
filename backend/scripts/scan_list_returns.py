#!/usr/bin/env python
"""Scan for bare dict returns that look like LIST endpoints (need ok_list)."""
import os
import re
import glob

base = os.path.join(os.path.dirname(__file__), "app", "api", "v1")
files = glob.glob(os.path.join(base, "**", "*.py"), recursive=True)

# Patterns that indicate a list response (should use ok_list)
list_indicators = [
    r'return\s*\{.*"items"',           # return {"items": ...}
    r'return\s*\{.*"total"',           # return {"total": ...}
    r'return\s*\{.*"data".*\[',        # return {"data": [...]}
    r'return\s*\{.*"list"',            # return {"list": ...}
]

# Patterns that are OK
ok_patterns = ['ok_list', 'success_response', 'error_response', 'ok_single']

list_returns = []

for filepath in sorted(files):
    rel = os.path.relpath(filepath, base)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception:
        continue
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Skip comments
        if stripped.startswith('#'):
            continue
        # Check if it's a list-like return
        is_list = any(re.search(p, stripped) for p in list_indicators)
        if not is_list:
            # Also check multiline (return { followed by "items" on next line)
            if re.match(r'return\s*\{$', stripped):
                chunk = ''.join(lines[i-1:i+10])
                if '"items"' in chunk or '"total"' in chunk:
                    is_list = True
        if not is_list:
            continue
        # Check if it's an OK pattern
        chunk = ''.join(lines[i-1:i+10])
        if any(p in chunk for p in ok_patterns):
            continue
        list_returns.append((rel, i, stripped[:120]))

print(f"Found {len(list_returns)} bare LIST dict returns (should use ok_list):\n")
for rel, lineno, text in list_returns:
    print(f"  {rel}:{lineno} -> {text}")

print(f"\nTotal: {len(list_returns)}")
