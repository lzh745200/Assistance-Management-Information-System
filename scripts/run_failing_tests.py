"""Run only the previously failing tests."""
import subprocess
import os

backend = r"c:\military-Rural Revitalization-system\backend"
python = os.path.join(backend, ".venv", "Scripts", "python.exe")

env = os.environ.copy()
env["ENVIRONMENT"] = "test"
env["SECRET_KEY"] = "test-secret"

tests = [
    "tests/unit/test_projects_api.py::TestProjectsAPI::test_create_project_fund_fail",
    "tests/unit/test_projects_api.py::TestProjectsAPI::test_create_project_task_fail",
    "tests/unit/test_projects_api.py::TestProjectsAPI::test_update_project_task_fail",
    "tests/unit/test_projects_api.py::TestProjectsAPI::test_delete_project_task_fail",
]

result = subprocess.run(
    [python, "-m", "pytest"] + tests + ["-v", "--tb=short", "--timeout=60"],
    capture_output=True, text=True, timeout=120,
    cwd=backend,
    env=env
)
print("STDOUT:", result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
print("RC:", result.returncode)
