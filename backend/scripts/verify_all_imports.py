#!/usr/bin/env python
"""Verify all modified modules import correctly after ok_list refactoring."""
import os
os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-for-ci-1234567890"

modules = [
    "app.api.v1.project_milestones",
    "app.api.v1.projects",
    "app.api.v1.funds",
    "app.api.v1.assessment",
    "app.api.v1.messages",
    "app.api.v1.work_logs",
    "app.api.v1.supported_village",
    "app.api.v1.policy",
    "app.api.v1.system.admin",
    "app.api.v1.machine_code",
]

passed = 0
failed = 0

for mod in modules:
    try:
        __import__(mod)
        print(f"  OK: {mod}")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {mod} -> {e}")
        failed += 1

print(f"\nResult: {passed}/{passed+failed} modules imported successfully")
if failed == 0:
    print("ALL_IMPORTS_PASSED")
else:
    print(f"IMPORT_FAILURES: {failed}")
