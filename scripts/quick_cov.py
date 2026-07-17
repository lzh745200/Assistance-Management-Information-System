"""Quick coverage summary - reads only totals."""
import json

with open(r"c:\military-Rural Revitalization-system\backend\coverage.json", encoding='utf-8') as f:
    data = json.load(f)

t = data.get("totals", {})
print(f"Statements: {t.get('num_statements', 0)}")
print(f"Covered: {t.get('covered_lines', 0)}")
print(f"Missing: {t.get('missing_lines', 0)}")
pct = t.get('percent_covered', 0)
print(f"Coverage: {pct:.2f}%")

# Top missing files
files = data.get("files", {})
results = []
for fname, info in files.items():
    missing = info.get("missing_lines", 0)
    total = info.get("num_statements", 0)
    p = info.get("percent_covered", 0)
    if total > 0 and missing > 0:
        results.append((fname, missing, total, p))

results.sort(key=lambda x: x[1], reverse=True)
print(f"\nTop 40 files by missing lines:")
for fname, missing, total, p in results[:40]:
    import os
    short = os.path.basename(fname)
    d = os.path.basename(os.path.dirname(fname))
    print(f"  {p:5.1f}%  miss={missing:4d}/{total:4d}  {d}/{short}")
