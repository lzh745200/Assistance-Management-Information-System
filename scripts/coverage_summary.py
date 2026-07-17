"""Quick coverage summary writer."""
import json
import os

cov_path = r"c:\military-Rural Revitalization-system\backend\coverage.json"
out_path = r"c:\military-Rural Revitalization-system\scripts\cov_summary.txt"

with open(cov_path, encoding='utf-8') as f:
    data = json.load(f)

files = data.get("files", {})
total_stmts = data.get("totals", {}).get("num_statements", 0)
total_covered = data.get("totals", {}).get("covered_lines", 0)
total_missing = data.get("totals", {}).get("missing_lines", 0)

pct = total_covered / total_stmts * 100 if total_stmts > 0 else 0

lines = []
lines.append(f"Overall: {pct:.1f}% (covered={total_covered}, missing={total_missing}, total={total_stmts})")
lines.append("")

file_list = []
for fname, info in files.items():
    missing = info.get("missing_lines", 0)
    total = info.get("num_statements", 0)
    covered = info.get("covered_lines", 0)
    p = info.get("percent_covered", 0)
    if total > 0:
        file_list.append((fname, missing, total, covered, p))

file_list.sort(key=lambda x: x[1], reverse=True)

lines.append("=== Top 60 Files by Missing Lines ===")
for fname, missing, total, covered, p in file_list[:60]:
    rel = os.path.relpath(fname, r"c:\military-Rural Revitalization-system\backend")
    lines.append(f"  {p:5.1f}%  miss={missing:4d}  total={total:4d}  {rel}")

# Directory summary
from collections import defaultdict
dir_stats = defaultdict(lambda: {"missing": 0, "total": 0})
for fname, missing, total, covered, p in file_list:
    rel = os.path.relpath(fname, r"c:\military-Rural Revitalization-system\backend")
    parts = rel.split(os.sep)
    if len(parts) > 2:
        d = "/".join(parts[:2])
    else:
        d = parts[0]
    dir_stats[d]["missing"] += missing
    dir_stats[d]["total"] += total

lines.append("")
lines.append("=== Coverage by Directory ===")
dir_list = []
for d, s in dir_stats.items():
    pp = (s["total"] - s["missing"]) / s["total"] * 100 if s["total"] > 0 else 100
    dir_list.append((d, s["missing"], s["total"], pp))
dir_list.sort(key=lambda x: x[1], reverse=True)
for d, missing, total, pp in dir_list:
    lines.append(f"  {pp:5.1f}%  miss={missing:5d}  total={total:5d}  {d}")

perfect = sum(1 for _, _, _, _, p in file_list if p >= 100)
low = sum(1 for _, _, _, _, p in file_list if p < 50)
zero = sum(1 for _, _, _, _, p in file_list if p == 0)
lines.append("")
lines.append(f"Total files: {len(file_list)}, 100%: {perfect}, <50%: {low}, 0%: {zero}")

with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f"Written to {out_path}")
