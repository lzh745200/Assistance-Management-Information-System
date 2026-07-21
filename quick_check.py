import json, urllib.request
url = "https://api.github.com/repos/lzh745200/Assistance-Management-Information-System/actions/runs?per_page=3"
req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "Python-urllib"})
resp = urllib.request.urlopen(req, timeout=15)
data = json.loads(resp.read().decode())
for r in data.get("workflow_runs", [])[:3]:
    sha = r["head_sha"][:8]
    print(f"Run #{r['run_number']}: {r['name']}")
    print(f"  SHA={sha} Status={r['status']} Conclusion={r['conclusion']}")
