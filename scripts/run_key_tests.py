"""Run key unit tests to verify no regressions after safe_commit fix."""
import subprocess
import os

backend = r"c:\military-Rural Revitalization-system\backend"
python = os.path.join(backend, ".venv", "Scripts", "python.exe")

env = os.environ.copy()
env["ENVIRONMENT"] = "test"
env["SECRET_KEY"] = "test-secret-key-for-ci"

test_files = [
    "tests/unit/test_projects_api.py",
    "tests/unit/test_fund_service.py",
    "tests/unit/test_fund_event_handler.py",
    "tests/unit/test_fund_budgets_api.py",
]

result = subprocess.run(
    [python, "-m", "pytest"] + test_files + ["-v", "--tb=short", "--timeout=60"],
    capture_output=True, text=True, timeout=300,
    cwd=backend,
    env=env
)
# Print last 3000 chars of stdout
stdout = result.stdout
if len(stdout) > 3000:
    stdout = stdout[-3000:]
print("STDOUT:", stdout)
print("RC:", result.returncode)
