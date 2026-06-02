"""
数据库迁移脚本
添加新字段和表
"""

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def migrate_database(db: Session):
    """
    执行数据库迁移

    Args:
        db: 数据库会话
    """
    migrations = [
        # 1. 用户表添加data_scope字段
        {
            "name": "add_user_data_scope",
            "check": "SELECT COUNT(*) FROM pragma_table_info('users') WHERE name='data_scope'",
            "sql": "ALTER TABLE users ADD COLUMN data_scope VARCHAR(20) DEFAULT 'org'",
        },
        # 2. 创建系统配置表
        {
            "name": "create_system_configs_table",
            "check": "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='system_configs'",
            "sql": """
                CREATE TABLE IF NOT EXISTS system_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key VARCHAR(100) UNIQUE NOT NULL,
                    value TEXT,
                    description VARCHAR(200),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
        },
        # 3. 创建数据包版本表
        {
            "name": "create_package_versions_table",
            "check": "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='package_versions'",
            "sql": """
                CREATE TABLE IF NOT EXISTS package_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    package_id INTEGER NOT NULL,
                    version VARCHAR(20) NOT NULL,
                    changes TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    FOREIGN KEY (package_id) REFERENCES data_packages(id) ON DELETE CASCADE,
                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
            """,
        },
        # 4. 创建数据包编辑日志表
        {
            "name": "create_package_edit_logs_table",
            "check": "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='package_edit_logs'",
            "sql": """
                CREATE TABLE IF NOT EXISTS package_edit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    package_id INTEGER NOT NULL,
                    data_type VARCHAR(50) NOT NULL,
                    record_id INTEGER NOT NULL,
                    field_name VARCHAR(100) NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    edited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    edited_by INTEGER,
                    FOREIGN KEY (package_id) REFERENCES data_packages(id) ON DELETE CASCADE,
                    FOREIGN KEY (edited_by) REFERENCES users(id)
                )
            """,
        },
        # 5. 为system_configs表创建索引
        {
            "name": "create_system_configs_index",
            "check": "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name='idx_system_configs_key'",
            "sql": "CREATE INDEX IF NOT EXISTS idx_system_configs_key ON system_configs(key)",
        },
        # 6. 为package_versions表创建索引
        {
            "name": "create_package_versions_index",
            "check": "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name='idx_package_versions_package_id'",
            "sql": "CREATE INDEX IF NOT EXISTS idx_package_versions_package_id ON package_versions(package_id)",
        },
        # 7. 为package_edit_logs表创建索引
        {
            "name": "create_package_edit_logs_index",
            "check": (
                "SELECT COUNT(*) FROM sqlite_master WHERE type='index' " "AND name='idx_package_edit_logs_package_id'"
            ),
            "sql": "CREATE INDEX IF NOT EXISTS idx_package_edit_logs_package_id ON package_edit_logs(package_id)",
        },
    ]

    success_count = 0
    error_count = 0
    skipped_count = 0

    for migration in migrations:
        try:
            # 检查是否需要执行
            result = db.execute(text(migration["check"])).scalar()

            # 对于表创建，result为0表示表不存在，需要创建
            # 对于字段添加，result为0表示字段不存在，需要添加
            # 对于索引创建，result为0表示索引不存在，需要创建
            needs_migration = result == 0

            if needs_migration:
                # 执行迁移
                db.execute(text(migration["sql"]))
                db.commit()
                success_count += 1
                logger.info(f"迁移成功: {migration['name']}")
            else:
                skipped_count += 1
                logger.debug(f"跳过迁移: {migration['name']} (已存在)")

        except Exception as e:
            error_count += 1
            logger.error(f"迁移失败: {migration['name']}, 错误: {str(e)}")
            db.rollback()

    logger.info(f"数据库迁移完成: 成功 {success_count} 个, " f"跳过 {skipped_count} 个, 失败 {error_count} 个")

    return {
        "success": success_count,
        "skipped": skipped_count,
        "failed": error_count,
        "total": len(migrations),
    }


def check_migration_status(db: Session) -> dict:
    """
    检查迁移状态

    Args:
        db: 数据库会话

    Returns:
        迁移状态
    """
    status = {
        "user_data_scope": False,
        "system_configs_table": False,
        "package_versions_table": False,
        "package_edit_logs_table": False,
    }

    try:
        # 检查用户表data_scope字段
        result = db.execute(text("SELECT COUNT(*) FROM pragma_table_info('users') WHERE name='data_scope'")).scalar()
        status["user_data_scope"] = result > 0

        # 检查system_configs表
        result = db.execute(
            text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='system_configs'")
        ).scalar()
        status["system_configs_table"] = result > 0

        # 检查package_versions表
        result = db.execute(
            text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='package_versions'")
        ).scalar()
        status["package_versions_table"] = result > 0

        # 检查package_edit_logs表
        result = db.execute(
            text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='package_edit_logs'")
        ).scalar()
        status["package_edit_logs_table"] = result > 0

    except Exception as e:
        logger.error(f"检查迁移状态失败: {str(e)}")

    return status
