"""Analyze coverage.json to find low-coverage files."""
import json
import os

cov_path = r"c:\military-Rural Revitalization-system\backend\coverage.json"
with open(cov_path, encoding='utf-8') as f:
    data = json.load(f)

files = data.get("files", {})
total_stmts = data.get("totals", {}).get("num_statements", 0)
total_covered = data.get("totals", {}).get("covered_lines", 0)
total_missing = data.get("totals", {}).get("missing_lines", 0)

if total_stmts > 0:
    pct = total_covered / total_stmts * 100
else:
    pct = 0

print(f"=== Overall Coverage ===")
print(f"Statements: {total_stmts}, Covered: {total_covered}, Missing: {total_missing}")
print(f"Coverage: {pct:.1f}%")
print()

# Sort files by missing lines (most missing first)
file_list = []
for fname, info in files.items():
    missing = info.get("missing_lines", 0)
    total = info.get("num_statements", 0)
    covered = info.get("covered_lines", 0)
    pct = info.get("percent_covered", 0)
    if total > 0:
        file_list.append((fname, missing, total, covered, pct))

file_list.sort(key=lambda x: x[1], reverse=True)

print(f"=== Top 50 Files by Missing Lines ===")
for fname, missing, total, covered, pct in file_list[:50]:
    # Show relative path
    rel = os.path.relpath(fname, r"c:\military-Rural Revitalization-system\backend")
    print(f"  {pct:5.1f}%  missing={missing:4d}  total={total:4d}  {rel}")

# Group by directory
from collections import defaultdict
dir_stats = defaultdict(lambda: {"missing": 0, "total": 0})
for fname, missing, total, covered, pct in file_list:
    rel = os.path.relpath(fname, r"c:\military-Rural Revitalization-system\backend")
    parts = rel.split(os.sep)
    if len(parts) > 2:
        d = "/".join(parts[:2])
    else:
        d = parts[0]
    dir_stats[d]["missing"] += missing
    dir_stats[d]["total"] += total

print(f"\n=== Coverage by Directory ===")
dir_list = []
for d, s in dir_stats.items():
    if s["total"] > 0:
        pct = (s["total"] - s["missing"]) / s["total"] * 100
    else:
        pct = 100
    dir_list.append((d, s["missing"], s["total"], pct))

dir_list.sort(key=lambda x: x[1], reverse=True)
for d, missing, total, pct in dir_list:
    print(f"  {pct:5.1f}%  missing={missing:5d}  total={total:5d}  {d}")

# Count files with 100% coverage
perfect = sum(1 for _, _, _, _, p in file_list if p >= 100)
low = sum(1 for _, _, _, _, p in file_list if p < 50)
zero = sum(1 for _, _, _, _, p in file_list if p == 0)
print(f"\n=== File Summary ===")
print(f"Total files: {len(file_list)}")
print(f"100% coverage: {perfect}")
print(f"<50% coverage: {low}")
print(f"0% coverage: {zero}")
