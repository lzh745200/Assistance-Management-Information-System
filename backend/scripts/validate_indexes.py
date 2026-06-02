#!/usr/bin/env python3
"""
验证数据库索引优化脚本
检查新增的复合索引是否正确创建
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import engine
from sqlalchemy import inspect, text


def check_indexes():
    """检查数据库索引"""
    inspector = inspect(engine)

    # 预期的新索引
    expected_indexes = {
        'organizations': [
            'idx_organizations_parent_type',
            'idx_organizations_level_parent'
        ],
        'projects': [
            'idx_projects_village_status_date',
            'idx_projects_org_status'
        ],
        'funds': [
            'idx_funds_village_date_status',
            'idx_funds_project_type_date',
            'idx_funds_org_date'
        ],
        'audit_logs': [
            'idx_audit_logs_user_time',
            'idx_audit_logs_entity_action_time',
            'idx_audit_logs_time_action'
        ],
        'users': [
            'idx_users_org_role',
            'idx_users_active_role'
        ],
        'messages': [
            'idx_messages_receiver_read_time',
            'idx_messages_sender_time'
        ],
        'approvals': [
            'idx_approvals_approver_status_time',
            'idx_approvals_entity_status'
        ],
        'villages': [
            'idx_villages_province_city_county',
            'idx_villages_org_province'
        ],
        'token_blacklist': [
            'idx_token_blacklist_token_expires'
        ],
        'user_sessions': [
            'idx_user_sessions_user_active',
            'idx_user_sessions_expires'
        ]
    }

    print("=" * 60)
    print("数据库索引验证报告")
    print("=" * 60)
    print()

    total_expected = 0
    total_found = 0
    missing_indexes = []

    for table_name, index_names in expected_indexes.items():
        total_expected += len(index_names)

        # 检查表是否存在
        if not inspector.has_table(table_name):
            print(f"[警告] 表 {table_name} 不存在")
            missing_indexes.extend([(table_name, idx) for idx in index_names])
            continue

        # 获取表的所有索引
        table_indexes = inspector.get_indexes(table_name)
        existing_index_names = {idx['name'] for idx in table_indexes}

        print(f"表: {table_name}")
        for idx_name in index_names:
            if idx_name in existing_index_names:
                print(f"  [OK] {idx_name}")
                total_found += 1
            else:
                print(f"  [缺失] {idx_name}")
                missing_indexes.append((table_name, idx_name))
        print()

    print("=" * 60)
    print(f"总计: {total_found}/{total_expected} 个索引已创建")

    if missing_indexes:
        print(f"\n缺失的索引 ({len(missing_indexes)} 个):")
        for table, idx in missing_indexes:
            print(f"  - {table}.{idx}")
        print("\n请执行以下命令创建索引:")
        print("  cd backend")
        print("  alembic upgrade head")
        return False
    else:
        print("\n所有索引已正确创建!")
        return True


def check_migration_version():
    """检查迁移版本"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            print(f"\n当前迁移版本: {version}")

            if version and version >= '008':
                print("[OK] 已应用索引优化迁移")
                return True
            else:
                print("[警告] 尚未应用索引优化迁移 (需要版本 008)")
                return False
    except Exception as e:
        print(f"[错误] 无法检查迁移版本: {e}")
        return False


if __name__ == '__main__':
    print("\n开始验证数据库索引优化...\n")

    # 检查迁移版本
    migration_ok = check_migration_version()
    print()

    # 检查索引
    indexes_ok = check_indexes()

    # 总结
    print("\n" + "=" * 60)
    if migration_ok and indexes_ok:
        print("验证通过: 所有优化已正确应用")
        sys.exit(0)
    else:
        print("验证失败: 请执行数据库迁移")
        print("\n执行命令:")
        print("  cd backend")
        print("  alembic upgrade head")
        sys.exit(1)
