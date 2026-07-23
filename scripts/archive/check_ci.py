"""等待 ARM64 构建完成"""
import json
import urllib.request
import time

owner = "lzh745200"
repo = "Assistance-Management-Information-System"

url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs?per_page=3"
req = urllib.request.Request(url, headers={
    "Accept": "application/vnd.github+json",
    "User-Agent": "Python-urllib",
})
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read().decode())

for run in data.get("workflow_runs", [])[:3]:
    sha = run['head_sha'][:8]
    name = run['name']
    status = run['status']
    conclusion = run['conclusion']
    print(f"Run #{run['run_number']}: {name}")
    print(f"  SHA: {sha}, Status: {status}, Conclusion: {conclusion}")

    if sha == '2de97ea9':
        if status in ('in_progress', 'queued'):
            print("  >>> STILL RUNNING - waiting 180s <<<")
            time.sleep(180)
            # 重新检查
            req2 = urllib.request.Request(url, headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "Python-urllib",
            })
            with urllib.request.urlopen(req2, timeout=15) as resp2:
                data2 = json.loads(resp2.read().decode())
            for run2 in data2.get("workflow_runs", [])[:3]:
                if run2['head_sha'][:8] == '2de97ea9':
                    print(f"\n  Updated: Run #{run2['run_number']}: {run2['name']}")
                    print(f"    Status: {run2['status']}, Conclusion: {run2['conclusion']}")
                    if run2['conclusion'] == 'success':
                        print("    >>> SUCCESS! <<<")
                    elif run2['conclusion'] == 'failure':
                        print("    >>> FAILED <<<")
                        # 获取失败详情
                        jobs_url = run2['jobs_url']
                        req3 = urllib.request.Request(jobs_url, headers={
                            "Accept": "application/vnd.github+json",
                            "User-Agent": "Python-urllib",
                        })
                        with urllib.request.urlopen(req3, timeout=15) as resp3:
                            jobs_data = json.loads(resp3.read().decode())
                        for job in jobs_data.get("jobs", []):
                            print(f"    Job: {job['name']} - {job['conclusion']}")
                            for step in job.get("steps", []):
                                if step['conclusion'] == 'failure':
                                    print(f"      FAILED: {step['name']}")
        elif conclusion == 'success':
            print("  >>> SUCCESS! <<<")
        elif conclusion == 'failure':
            print("  >>> FAILED <<<")
    print()
