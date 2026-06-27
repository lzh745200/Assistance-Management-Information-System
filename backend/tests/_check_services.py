"""Check which service files have the most uncovered lines."""
import json

cov = json.load(open("coverage.json"))
services = {k: v for k, v in cov.items() if "services" in k and k.endswith(".py") and v.get("missing", 0) > 0}
for p, d in sorted(services.items(), key=lambda x: -x[1]["missing"]):
    print(f"{p}: {d.get('missing', 0)}/{d.get('statements', 0)} missing ({d.get('missing_percent', 0):.1f}%)")
