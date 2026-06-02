#!/usr/bin/env python3
"""
验证系统整合完成情况
检查所有新增功能的文件是否存在
"""
import os
import sys

def check_file(path, description):
    """检查文件是否存在"""
    exists = os.path.exists(path)
    status = "OK" if exists else "MISSING"
    print(f"[{status}] {description}: {path}")
    return exists

def main():
    """主函数"""
    base_dir = r"C:\military-Rural Revitalization-system"

    print("=" * 80)
    print("系统整合验证")
    print("=" * 80)

    all_ok = True

    # 后端服务文件
    print("\n[后端服务文件]")
    services = [
        ("backend/app/services/data_sync_service.py", "数据同步服务"),
        ("backend/app/services/offline_map_service.py", "离线地图服务"),
        ("backend/app/services/batch_service.py", "批量操作服务"),
        ("backend/app/services/data_masking_service.py", "数据脱敏服务"),
        ("backend/app/services/performance_monitor.py", "性能监控服务"),
    ]

    for file_path, desc in services:
        full_path = os.path.join(base_dir, file_path)
        if not check_file(full_path, desc):
            all_ok = False

    # 后端API文件
    print("\n[后端API文件]")
    apis = [
        ("backend/app/api/v1/data_sync.py", "数据同步API"),
        ("backend/app/api/v1/offline_map.py", "离线地图API"),
        ("backend/app/api/v1/batch_operations.py", "批量操作API"),
        ("backend/app/api/v1/encryption.py", "加密管理API"),
    ]

    for file_path, desc in apis:
        full_path = os.path.join(base_dir, file_path)
        if not check_file(full_path, desc):
            all_ok = False

    # 后端模型文件
    print("\n[后端模型文件]")
    models = [
        ("backend/app/models/data_sync.py", "数据同步模型"),
    ]

    for file_path, desc in models:
        full_path = os.path.join(base_dir, file_path)
        if not check_file(full_path, desc):
            all_ok = False

    # 前端页面
    print("\n[前端页面]")
    views = [
        ("frontend/src/views/dataSync/Export.vue", "数据导出页面"),
        ("frontend/src/views/dataSync/Import.vue", "数据导入页面"),
        ("frontend/src/views/system/MapTileManager.vue", "地图瓦片管理"),
        ("frontend/src/views/system/EncryptionSettings.vue", "加密设置"),
        ("frontend/src/views/help/HelpCenter.vue", "帮助中心"),
    ]

    for file_path, desc in views:
        full_path = os.path.join(base_dir, file_path)
        if not check_file(full_path, desc):
            all_ok = False

    # 前端组件
    print("\n[前端组件]")
    components = [
        ("frontend/src/components/map/OfflineMap.vue", "离线地图组件"),
        ("frontend/src/components/common/BatchOperationBar.vue", "批量操作栏"),
    ]

    for file_path, desc in components:
        full_path = os.path.join(base_dir, file_path)
        if not check_file(full_path, desc):
            all_ok = False

    # 前端API封装
    print("\n[前端API封装]")
    api_wrappers = [
        ("frontend/src/api/dataSync.ts", "数据同步API"),
        ("frontend/src/api/offlineMap.ts", "离线地图API"),
    ]

    for file_path, desc in api_wrappers:
        full_path = os.path.join(base_dir, file_path)
        if not check_file(full_path, desc):
            all_ok = False

    # 前端组合式函数
    print("\n[前端组合式函数]")
    composables = [
        ("frontend/src/composables/useBatchOperation.ts", "批量操作"),
    ]

    for file_path, desc in composables:
        full_path = os.path.join(base_dir, file_path)
        if not check_file(full_path, desc):
            all_ok = False

    # 测试文件
    print("\n[测试文件]")
    tests = [
        ("backend/tests/test_data_sync.py", "数据同步测试"),
        ("backend/tests/test_offline_map.py", "离线地图测试"),
        ("backend/tests/test_batch_service.py", "批量操作测试"),
        ("backend/tests/test_encryption_service.py", "加密服务测试"),
        ("backend/tests/test_data_masking_service.py", "数据脱敏测试"),
        ("backend/tests/test_api_integration.py", "API集成测试"),
    ]

    for file_path, desc in tests:
        full_path = os.path.join(base_dir, file_path)
        if not check_file(full_path, desc):
            all_ok = False

    # 文档文件
    print("\n[文档文件]")
    docs = [
        ("docs/USER_MANUAL.md", "用户手册"),
        ("docs/FINAL_REPORT.md", "最终报告"),
        ("docs/INSTALL.md", "安装指南"),
        ("docs/DEVELOPMENT.md", "开发指南"),
        ("docs/INDEX.md", "文档索引"),
        ("CHANGELOG.md", "更新日志"),
        ("README.md", "项目说明"),
        ("docs/help/index.html", "帮助文档"),
        ("docs/implementation/phase1-complete-summary.md", "第一阶段总结"),
        ("docs/implementation/phase2-summary.md", "第二阶段总结"),
        ("docs/implementation/data-sync-summary.md", "数据同步总结"),
        ("docs/implementation/PROJECT_COMPLETE.md", "项目完成文档"),
    ]

    for file_path, desc in docs:
        full_path = os.path.join(base_dir, file_path)
        if not check_file(full_path, desc):
            all_ok = False

    # 总结
    print("\n" + "=" * 80)
    if all_ok:
        print("验证结果: 所有文件已成功整合!")
        print("=" * 80)
        return 0
    else:
        print("验证结果: 部分文件缺失,请检查上述MISSING项")
        print("=" * 80)
        return 1

if __name__ == "__main__":
    sys.exit(main())
