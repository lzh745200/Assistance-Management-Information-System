#!/usr/bin/env python
"""Scan for bare dict returns in API route files."""
import os
import re
import glob

base = os.path.join(os.path.dirname(__file__), "app", "api", "v1")
files = glob.glob(os.path.join(base, "**", "*.py"), recursive=True)

# Patterns that are OK (envelope responses)
ok_patterns = ['ok_list', 'success_response', 'error_response', 'ok_single', 'create_response']

bare_returns = []

for filepath in sorted(files):
    rel = os.path.relpath(filepath, base)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception:
        continue
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Look for "return {" patterns
        if re.match(r'return\s*\{', stripped):
            # Check if it's an OK pattern
            if any(p in stripped for p in ok_patterns):
                continue
            # Check next few lines for ok patterns (multiline return)
            chunk = ''.join(lines[i-1:i+5])
            if any(p in chunk for p in ok_patterns):
                continue
            bare_returns.append((rel, i, stripped[:100]))

print(f"Found {len(bare_returns)} bare dict returns:\n")
for rel, lineno, text in bare_returns:
    print(f"  {rel}:{lineno} -> {text}")

print(f"\nTotal: {len(bare_returns)}")
