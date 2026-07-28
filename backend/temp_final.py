"""最终验证：编译检查 + 导入检查"""
import py_compile
import os

# 1. 编译检查所有关键文件
files = [
    "app/api/v1/import_export/__init__.py",
    "app/api/v1/import_export/import_data.py",
    "app/api/v1/import_export/export.py",
    "app/api/v1/import_export/async_export.py",
    "app/api/v1/import_export/chunked_upload.py",
    "app/services/excel_importer_service.py",
    "app/services/chunked_upload_service.py",
    "app/services/async_export_service.py",
    "app/services/backup_service.py",
    "app/services/data_package_service.py",
    "app/api/v1/data_sync.py",
    "app/api/v1/policies.py",
    "app/api/v1/funds.py",
    "app/api/v1/rural_tasks.py",
    "app/api/v1/project_milestones.py",
    "app/services/approval_workflow_service.py",
    "app/services/audit_service.py",
    "app/services/policy_service.py",
]

errors = []
ok = 0
for f in files:
    if not os.path.exists(f):
        errors.append(f"{f}: FILE NOT FOUND")
        continue
    try:
        py_compile.compile(f, doraise=True)
        ok += 1
    except py_compile.PyCompileError as e:
        errors.append(f"{f}: {e}")

print(f"Compile check: {ok}/{len(files)} files OK")
if errors:
    for e in errors:
        print(f"  FAIL: {e}")
else:
    print("All files compiled successfully!")

# 2. 检查 __init__.py 路由加载
os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-for-ci-12345678901234567890123456789012"

try:
    import app.api.v1 as api_v1
    # 尝试获取路由列表
    if hasattr(api_v1, "router"):
        routes = [r.path for r in api_v1.router.routes] if hasattr(api_v1.router, "routes") else []
        print(f"\nTotal routes registered: {len(routes)}")
    print("app.api.v1 imported successfully!")
except Exception as e:
    print(f"\napp.api.v1 import error: {e}")

print("\n=== Verification complete ===")
