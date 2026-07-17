"""Quick check: run alembic current and heads."""
import subprocess
import os

backend = r"c:\military-Rural Revitalization-system\backend"
python = os.path.join(backend, ".venv", "Scripts", "python.exe")

result = subprocess.run(
    [python, "-m", "alembic", "current"],
    capture_output=True, text=True, timeout=30,
    cwd=backend
)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("RC:", result.returncode)
