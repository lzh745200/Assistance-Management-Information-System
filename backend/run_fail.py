import subprocess, sys
r = subprocess.run(
    [sys.executable, "-m", "pytest",
     "tests/unit/test_policy_api.py", "tests/unit/test_assessment_api.py",
     "-k", "test_duplicate_ids or test_import_policies",
     "--tb=short", "-q", "--timeout=60"],
    capture_output=True, text=True, cwd=r"c:\military-Rural Revitalization-system\backend"
)
print(r.stdout[-3000:] if len(r.stdout) > 3000 else r.stdout)
print(r.stderr[-2000:] if len(r.stderr) > 2000 else r.stderr)
