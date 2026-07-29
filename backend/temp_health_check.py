"""全面健康检查：编译所有Python文件 + 导入所有路由模块"""
import py_compile
import os
import importlib
import sys

os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-for-ci-12345678901234567890123456789012"

# ========== 1. 编译检查所有 .py 文件 ==========
compile_errors = []
compile_ok = 0
compile_total = 0

for root, dirs, files in os.walk("app"):
    for f in files:
        if not f.endswith(".py"):
            continue
        compile_total += 1
        path = os.path.join(root, f)
        try:
            py_compile.compile(path, doraise=True)
            compile_ok += 1
        except py_compile.PyCompileError as e:
            lines = str(e).split("\n")
            short = lines[0] if lines else str(e)
            compile_errors.append((path, short))

print(f"1. 编译检查: {compile_ok}/{compile_total} 通过")
if compile_errors:
    for path, err in compile_errors:
        print(f"   FAIL: {path}")
        print(f"     {err}")

# ========== 2. 导入所有路由模块 ==========
route_modules = [
    "app.api.v1.auth", "app.api.v1.auth.auth", "app.api.v1.auth.users",
    "app.api.v1.auth.rbac", "app.api.v1.auth.user_management",
    "app.api.v1.data", "app.api.v1.data.data",
    "app.api.v1.data.data.analytics", "app.api.v1.data.data.dashboard",
    "app.api.v1.data.data.dashboard_trends", "app.api.v1.data.data.data_packages",
    "app.api.v1.data.data.data_quality", "app.api.v1.data.data.data_reports",
    "app.api.v1.data.data.reports", "app.api.v1.data.data.statistics",
    "app.api.v1.import_export", "app.api.v1.import_export.import_data",
    "app.api.v1.import_export.export", "app.api.v1.import_export.async_export",
    "app.api.v1.import_export.chunked_upload",
    "app.api.v1.system", "app.api.v1.system.admin", "app.api.v1.system.audit",
    "app.api.v1.system.backup", "app.api.v1.system.cache",
    "app.api.v1.system.config_package", "app.api.v1.system.env",
    "app.api.v1.system.error_report", "app.api.v1.system.health",
    "app.api.v1.system.help", "app.api.v1.system.i18n",
    "app.api.v1.system.init", "app.api.v1.system.metrics",
    "app.api.v1.system.monitor", "app.api.v1.system.system",
    "app.api.v1.system.system_config", "app.api.v1.system.tasks",
    "app.api.v1.system.update_logs", "app.api.v1.system.zero_trust",
]
# 加上所有业务模块
business_modules = [
    "app.api.v1.ai", "app.api.v1.ai_enhanced", "app.api.v1.approval",
    "app.api.v1.batch_operations", "app.api.v1.data_quality",
    "app.api.v1.data_scope", "app.api.v1.data_sync",
    "app.api.v1.effectiveness", "app.api.v1.encryption",
    "app.api.v1.feedback", "app.api.v1.funds", "app.api.v1.fund_budgets",
    "app.api.v1.fund_lifecycle", "app.api.v1.machine_code",
    "app.api.v1.map", "app.api.v1.menus", "app.api.v1.messages",
    "app.api.v1.messages_extended", "app.api.v1.monitoring",
    "app.api.v1.monitoring_legacy", "app.api.v1.offline_map",
    "app.api.v1.organization", "app.api.v1.performance",
    "app.api.v1.permission_package", "app.api.v1.policy",
    "app.api.v1.projects", "app.api.v1.project_milestones",
    "app.api.v1.report_templates", "app.api.v1.rural_tasks",
    "app.api.v1.rural_works", "app.api.v1.school",
    "app.api.v1.search", "app.api.v1.sentiment",
    "app.api.v1.supported_village", "app.api.v1.supported_village_export",
    "app.api.v1.sync", "app.api.v1.system_config", "app.api.v1.system_health",
    "app.api.v1.todos", "app.api.v1.user_permissions",
    "app.api.v1.validation", "app.api.v1.villages",
    "app.api.v1.village_templates", "app.api.v1.work_logs",
    "app.api.v1.assessment",
]
all_modules = route_modules + business_modules

import_errors = []
import_ok = 0
for mod_name in all_modules:
    try:
        importlib.import_module(mod_name)
        import_ok += 1
    except Exception as e:
        import_errors.append((mod_name, f"{type(e).__name__}: {e}"))

print(f"\n2. 路由模块导入: {import_ok}/{len(all_modules)} 成功")
if import_errors:
    for name, err in import_errors:
        print(f"   FAIL: {name}")
        print(f"     {err}")

# ========== 3. 检查关键服务层导入 ==========
service_modules = [
    "app.services.machine_code_service",
    "app.services.machine_code_permission_service",
    "app.services.permission_package_service",
    "app.services.excel_importer_service",
    "app.services.approval_workflow_service",
    "app.services.audit_service",
    "app.services.policy_service",
    "app.services.user_service",
    "app.services.organization_service",
    "app.services.rbac_service",
    "app.services.data_validator_service",
    "app.services.export_service",
    "app.services.backup_service",
    "app.services.data_package_service",
    "app.services.chunked_upload_service",
    "app.services.async_export_service",
    "app.services.config_package_service",
    "app.services.system_config_service",
    "app.services.work_log_service",
    "app.services.lockout_service",
    "app.services.two_factor_service",
    "app.services.analytics_service",
    "app.services.batch_service",
    "app.services.data_sync_encryption_service",
]
svc_errors = []
svc_ok = 0
for mod_name in service_modules:
    try:
        importlib.import_module(mod_name)
        svc_ok += 1
    except Exception as e:
        svc_errors.append((mod_name, f"{type(e).__name__}: {e}"))

print(f"\n3. 服务模块导入: {svc_ok}/{len(service_modules)} 成功")
if svc_errors:
    for name, err in svc_errors:
        print(f"   FAIL: {name}")
        print(f"     {err}")

# ========== 总结 ==========
total_issues = len(compile_errors) + len(import_errors) + len(svc_errors)
print(f"\n{'='*60}")
print(f"健康检查总结: {total_issues} 个问题")
if total_issues == 0:
    print("系统 100% 健康！")
else:
    print(f"  编译错误: {len(compile_errors)}")
    print(f"  路由导入失败: {len(import_errors)}")
    print(f"  服务导入失败: {len(svc_errors)}")
