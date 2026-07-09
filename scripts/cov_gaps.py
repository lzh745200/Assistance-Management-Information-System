"""Find the biggest uncovered modules for targeted test writing."""
import subprocess, re, sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "backend/tests/unit/", "-q", "--tb=no",
     "--cov=backend/app", "--cov-report=term-missing",
     "--ignore=backend/tests/unit/test_deep_services.py",
     "--ignore=backend/tests/unit/test_deep_svc2.py",
     "--ignore=backend/tests/unit/test_svc_batch.py",
     "--ignore=backend/tests/unit/test_api_coverage.py",
     "--ignore=backend/tests/unit/utils/test_chart.py",
     "--ignore=backend/tests/unit/test_token_blacklist_service_full.py",
     "--ignore=backend/tests/unit/test_import_export_history_service_full.py",
     "--ignore=backend/tests/unit/test_village_mixins.py",
     "--ignore=backend/tests/unit/test_villages_api.py",
     "--ignore=backend/tests/unit/test_batch_service.py"],
    capture_output=True, text=True, cwd=r"C:\military-Rural Revitalization-system",
    timeout=600
)

# Parse coverage lines
lines = result.stdout.split('\n') + result.stderr.split('\n')
for line in lines:
    if re.search(r'\d+%', line) and 'app/' in line:
        parts = line.strip().split()
        if len(parts) >= 4:
            name = parts[0]
            stmts = parts[1]
            missing_str = parts[2] if len(parts) > 2 else ''
            cov_str = parts[3] if len(parts) > 3 else ''
            try:
                cov = int(cov_str.replace('%', ''))
                if cov < 85 and 'test_' not in name:
                    print(f"  {cov:3d}% | {stmts:5s} stmts | {name}")
            except:
                pass
