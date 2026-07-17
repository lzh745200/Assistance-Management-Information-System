"""Count source and test files."""
import os

backend = r"c:\military-Rural Revitalization-system\backend"

src_files = []
for root, dirs, files in os.walk(os.path.join(backend, "app")):
    for f in files:
        if f.endswith('.py'):
            src_files.append(os.path.join(root, f))

test_files = []
for root, dirs, files in os.walk(os.path.join(backend, "tests")):
    for f in files:
        if f.endswith('.py'):
            test_files.append(os.path.join(root, f))

src_lines = 0
for fp in src_files:
    with open(fp, encoding='utf-8') as fh:
        src_lines += sum(1 for _ in fh)

test_lines = 0
for fp in test_files:
    with open(fp, encoding='utf-8') as fh:
        test_lines += sum(1 for _ in fh)

print(f"Source files: {len(src_files)}, lines: {src_lines}")
print(f"Test files: {len(test_files)}, lines: {test_lines}")

# List source files by directory
from collections import Counter
dirs = Counter()
for fp in src_files:
    rel = os.path.relpath(fp, os.path.join(backend, "app"))
    parts = rel.split(os.sep)
    if len(parts) > 1:
        dirs[parts[0] + "/" + (parts[1] if len(parts) > 2 else "")] += 1
    else:
        dirs[parts[0]] += 1

print("\nSource files by directory:")
for d, count in dirs.most_common():
    print(f"  {d}: {count}")
