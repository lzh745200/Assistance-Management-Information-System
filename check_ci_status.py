"""等待并检查 CI 构建结果"""
import json
import urllib.request
import time
import os

owner = "lzh745200"
repo = "Assistance-Management-Information-System"

def check_runs():
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs?per_page=5"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "Python-urllib",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode()).get("workflow_runs", [])

# 检查当前状态
print("=== Current CI Status ===")
runs = check_runs()
for run in runs[:5]:
    sha = run['head_sha'][:8]
    print(f"Run #{run['run_number']}: {run['name']}")
    print(f"  SHA: {sha}, Status: {run['status']}, Conclusion: {run['conclusion']}")

    # 只关注 2de97ea9 的构建
    if sha == '2de97ea9':
        if run['status'] in ('in_progress', 'queued'):
            print(f"  >>> STILL RUNNING <<<")
        elif run['conclusion'] == 'failure':
            # 获取失败的 job 详情
            jobs_url = run['jobs_url']
            try:
                req2 = urllib.request.Request(jobs_url, headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "Python-urllib",
                })
                with urllib.request.urlopen(req2, timeout=15) as resp2:
                    jobs_data = json.loads(resp2.read().decode())
                for job in jobs_data.get("jobs", []):
                    print(f"  Job: {job['name']} - {job['conclusion']}")
                    for step in job.get("steps", []):
                        if step['conclusion'] == 'failure':
                            print(f"    FAILED: {step['name']}")
            except Exception as e:
                print(f"  Could not fetch jobs: {e}")
        elif run['conclusion'] == 'success':
            print(f"  >>> SUCCESS! <<<")
    print()

# 如果还在运行，等待并重试
running = any(r['head_sha'][:8] == '2de97ea9' and r['status'] in ('in_progress', 'queued') for r in runs[:5])
if running:
    print("Builds still in progress. Waiting 120 seconds...")
    time.sleep(120)
    print("\n=== Rechecking ===")
    runs = check_runs()
    for run in runs[:5]:
        sha = run['head_sha'][:8]
        if sha == '2de97ea9':
            print(f"Run #{run['run_number']}: {run['name']}")
            print(f"  Status: {run['status']}, Conclusion: {run['conclusion']}")
            if run['conclusion'] == 'failure':
                jobs_url = run['jobs_url']
                try:
                    req2 = urllib.request.Request(jobs_url, headers={
                        "Accept": "application/vnd.github+json",
                        "User-Agent": "Python-urllib",
                    })
                    with urllib.request.urlopen(req2, timeout=15) as resp2:
                        jobs_data = json.loads(resp2.read().decode())
                    for job in jobs_data.get("jobs", []):
                        print(f"  Job: {job['name']} - {job['conclusion']}")
                        for step in job.get("steps", []):
                            if step['conclusion'] == 'failure':
                                print(f"    FAILED: {step['name']}")
                except Exception as e:
                    print(f"  Could not fetch jobs: {e}")
            elif run['conclusion'] == 'success':
                print("  >>> SUCCESS! <<<")
