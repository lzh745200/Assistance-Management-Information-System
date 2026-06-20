"""数据库查询优化模块

提供数据库索引管理、查询缓存优化和性能分析功能。

Task 11.3: 实施性能优化 - 添加数据库索引优化
Requirements: 10.1 - 实现数据库查询优化（添加必要索引）
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """数据库查询优化器

    功能:
    - 创建推荐索引
    - 分析慢查询
    - 优化查询缓存
    - 数据库维护

    Requirements: 10.1
    """

    # 推荐的数据库索引配置（扩展版）
    RECOMMENDED_INDEXES = [
        # ==================== 用户表索引 ====================
        {
            "table": "users",
            "columns": ["username", "email"],
            "name": "idx_user_credentials",
            "description": "用户登录凭证查询优化",
        },
        {"table": "users", "columns": ["role_id"], "name": "idx_user_role"},
        {
            "table": "users",
            "columns": ["is_active", "created_at"],
            "name": "idx_user_active_created",
        },
        {
            "table": "users",
            "columns": ["organization_id"],
            "name": "idx_user_organization",
            "description": "按组织查询用户",
        },
        # ==================== 审计日志索引 ====================
        {
            "table": "audit_logs",
            "columns": ["user_id", "created_at"],
            "name": "idx_audit_user_time",
        },
        {
            "table": "audit_logs",
            "columns": ["resource_type", "action"],
            "name": "idx_audit_resource_action",
        },
        {
            "table": "audit_logs",
            "columns": ["created_at"],
            "name": "idx_audit_created",
        },
        # ==================== API指标索引 ====================
        {
            "table": "api_metrics",
            "columns": ["endpoint", "created_at"],
            "name": "idx_api_endpoint_time",
        },
        {
            "table": "api_metrics",
            "columns": ["response_time_ms"],
            "name": "idx_api_response_time",
        },
        # ==================== 村庄表索引 ====================
        {
            "table": "villages",
            "columns": ["province", "city", "county"],
            "name": "idx_village_location",
        },
        {"table": "villages", "columns": ["status"], "name": "idx_village_status"},
        # ==================== 学校表索引 ====================
        {
            "table": "schools",
            "columns": ["province", "city", "district"],
            "name": "idx_school_location",
        },
        {
            "table": "schools",
            "columns": ["school_type", "school_level"],
            "name": "idx_school_type_level",
        },
        # ==================== 资金表索引 ====================
        {
            "table": "funds",
            "columns": ["fund_type", "status"],
            "name": "idx_fund_type_status",
        },
        {"table": "funds", "columns": ["created_at"], "name": "idx_fund_created"},
        # ==================== 帮扶村表索引（新增） ====================
        {
            "table": "supported_villages",
            "columns": ["department", "support_unit"],
            "name": "idx_sv_dept_unit",
            "description": "按部门和帮扶单位查询",
        },
        {
            "table": "supported_villages",
            "columns": ["is_three_regions", "is_key_county"],
            "name": "idx_sv_region_flags",
            "description": "按区域标志筛选",
        },
        {
            "table": "supported_villages",
            "columns": ["village_name"],
            "name": "idx_sv_village_name",
            "description": "按村名搜索",
        },
        {
            "table": "supported_villages",
            "columns": ["sequence_no"],
            "name": "idx_sv_sequence",
            "description": "按序号排序",
        },
        # ==================== 导入导出历史索引（新增） ====================
        {
            "table": "import_histories",
            "columns": ["user_id", "status"],
            "name": "idx_import_user_status",
            "description": "用户导入历史查询",
        },
        {
            "table": "import_histories",
            "columns": ["created_at"],
            "name": "idx_import_created",
            "description": "按时间查询导入历史",
        },
        {
            "table": "export_tasks",
            "columns": ["user_id", "status"],
            "name": "idx_export_user_status",
            "description": "用户导出任务查询",
        },
        {
            "table": "export_tasks",
            "columns": ["task_id"],
            "name": "idx_export_task_id",
            "description": "按任务ID查询",
        },
        # ==================== 审批流程索引（新增） ====================
        {
            "table": "approval_tasks",
            "columns": ["submitter_id", "status"],
            "name": "idx_approval_submitter_status",
            "description": "提交人审批任务查询",
        },
        {
            "table": "approval_tasks",
            "columns": ["entity_type", "entity_id"],
            "name": "idx_approval_entity",
            "description": "按实体查询审批",
        },
        {
            "table": "approval_tasks",
            "columns": ["priority", "created_at"],
            "name": "idx_approval_priority_time",
            "description": "审批任务排序",
        },
        {
            "table": "approval_records",
            "columns": ["task_id", "level"],
            "name": "idx_approval_record_task_level",
            "description": "审批记录查询",
        },
        {
            "table": "approval_records",
            "columns": ["approver_id", "created_at"],
            "name": "idx_approval_record_approver",
            "description": "审批人记录查询",
        },
        # ==================== 消息通知索引（新增） ====================
        {
            "table": "messages",
            "columns": ["user_id", "is_read"],
            "name": "idx_message_user_read",
            "description": "用户未读消息查询",
        },
        {
            "table": "messages",
            "columns": ["user_id", "message_type", "created_at"],
            "name": "idx_message_user_type_time",
            "description": "用户消息列表查询",
        },
        {
            "table": "email_logs",
            "columns": ["status", "retry_count"],
            "name": "idx_email_status_retry",
            "description": "邮件重试队列查询",
        },
        # ==================== 组织机构索引（新增） ====================
        {
            "table": "organizations",
            "columns": ["parent_id"],
            "name": "idx_org_parent",
            "description": "组织树查询",
        },
        {
            "table": "organizations",
            "columns": ["code"],
            "name": "idx_org_code",
            "description": "按组织代码查询",
        },
        {
            "table": "organizations",
            "columns": ["org_type", "is_active"],
            "name": "idx_org_type_active",
            "description": "按类型查询活跃组织",
        },
        # ==================== 数据包和报告索引（新增） ====================
        {
            "table": "data_packages",
            "columns": ["status", "created_at"],
            "name": "idx_package_status_time",
            "description": "数据包状态查询",
        },
        {
            "table": "data_reports",
            "columns": ["report_type", "created_at"],
            "name": "idx_report_type_time",
            "description": "报告类型查询",
        },
    ]

    @staticmethod
    def analyze_slow_queries(db: Session) -> List[Dict]:
        """分析慢查询（仅支持PostgreSQL / MySQL）

        Args:
            db: 数据库会话

        Returns:
            List[Dict]: 慢查询列表
        """
        try:
            # SQLite不支持慢查询分析，返回空列表
            # PostgreSQL: SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;
            # MySQL: SELECT * FROM mysql.slow_log ORDER BY query_time DESC LIMIT 10;
            slow_queries = []
            logger.info("慢查询分析功能仅支持PostgreSQL和MySQL")
            return slow_queries
        except Exception:
            logger.error("分析慢查询失败", exc_info=True)
            return []

    @staticmethod
    def create_indexes() -> None:
        """创建推荐的数据库索引"""
        import re

        safe_pattern = re.compile(r"^[a-zA-Z0-9_]+$")

        db = SessionLocal()
        try:
            for idx_config in QueryOptimizer.RECOMMENDED_INDEXES:
                try:
                    table_name = idx_config["table"]
                    columns = idx_config["columns"]
                    index_name = idx_config["name"]

                    # 验证表名、索引名和列名只包含安全字符（防止SQL注入）
                    if not safe_pattern.match(table_name):
                        logger.warning(f"表名 {table_name} 包含非法字符，跳过")
                        continue

                    if not safe_pattern.match(index_name):
                        logger.warning(f"索引名 {index_name} 包含非法字符，跳过")
                        continue

                    for col in columns:
                        if not safe_pattern.match(col):
                            logger.warning(f"列名 {col} 包含非法字符，跳过索引 {index_name}")
                            continue

                    # 检查索引是否已存在
                    check_sql = text("""
                        SELECT name FROM sqlite_master
                        WHERE type='index' AND name=:index_name
                        """)
                    exists = db.execute(check_sql, {"index_name": index_name}).fetchone()

                    if not exists:
                        # 创建索引（使用验证过的安全名称）
                        columns_str = ", ".join(columns)
                        create_sql = text(f"""
                            CREATE INDEX {index_name}
                            ON {table_name} ({columns_str})
                            """)
                        db.execute(create_sql)
                        logger.info("创建索引成功: %s", index_name)
                    else:
                        logger.info("索引已存在: %s", index_name)

                except Exception as e:
                    logger.warning("创建索引 %s 失败: %s", idx_config["name"], str(e))

            db.commit()
            logger.info("索引创建流程完成")

        except Exception:
            db.rollback()
            logger.error("索引创建失败", exc_info=True)
        finally:
            db.close()

    @staticmethod
    def optimize_query_cache() -> None:
        """优化查询缓存（SQLite特定）"""
        db = SessionLocal()
        try:
            # 设置缓存大小（1KB为单位，10000=10MB）
            db.execute(text("PRAGMA cache_size = 10000"))

            # 启用WAL模式(Write - Ahead Logging)
            db.execute(text("PRAGMA journal_mode = WAL"))

            # 设置同步模式为NORMAL（平衡性能和安全）
            db.execute(text("PRAGMA synchronous = NORMAL"))

            # 临时文件存储在内存中
            db.execute(text("PRAGMA temp_store = MEMORY"))

            db.commit()
            logger.info("查询缓存优化完成")

        except Exception:
            logger.error("查询缓存优化失败", exc_info=True)
        finally:
            db.close()

    @staticmethod
    def vacuum_database() -> None:
        """清理数据库碎片"""
        db = SessionLocal()
        try:
            db.execute(text("VACUUM"))
            db.commit()
            logger.info("✅ 数据库清理完成")
        except Exception:
            logger.error("❌ 数据库清理失败", exc_info=True)
        finally:
            db.close()

    @staticmethod
    def analyze_tables() -> None:
        """分析表统计信息"""
        db = SessionLocal()
        try:
            db.execute(text("ANALYZE"))
            db.commit()
            logger.info("✅ 表统计信息分析完成")
        except Exception:
            logger.error("❌ 表统计信息分析失败", exc_info=True)
        finally:
            db.close()

    @staticmethod
    def get_index_stats(db: Session) -> List[Dict[str, Any]]:
        """
        获取索引使用统计信息

        Args:
            db: 数据库会话

        Returns:
            List[Dict]: 索引统计信息列表
        """
        try:
            # SQLite索引信息查询
            result = db.execute(text("""
                SELECT
                    name as index_name,
                    tbl_name as table_name,
                    sql
                FROM sqlite_master
                WHERE type='index' AND sql IS NOT NULL
                ORDER BY tbl_name, name
            """))

            indexes = []
            for row in result:
                indexes.append(
                    {
                        "index_name": row[0],
                        "table_name": row[1],
                        "definition": row[2],
                    }
                )

            return indexes
        except Exception:
            logger.error("获取索引统计失败", exc_info=True)
            return []

    @staticmethod
    def check_missing_indexes() -> List[Dict[str, Any]]:
        """
        检查缺失的推荐索引

        Returns:
            List[Dict]: 缺失索引列表
        """
        db = SessionLocal()
        missing = []

        try:
            # 获取现有索引
            result = db.execute(text("""
                SELECT name FROM sqlite_master WHERE type='index'
            """))
            existing_indexes = {row[0] for row in result}

            # 获取现有表
            result = db.execute(text("""
                SELECT name FROM sqlite_master WHERE type='table'
            """))
            existing_tables = {row[0] for row in result}

            # 检查推荐索引
            for idx_config in QueryOptimizer.RECOMMENDED_INDEXES:
                table_name = idx_config["table"]
                index_name = idx_config["name"]

                # 跳过不存在的表
                if table_name not in existing_tables:
                    continue

                # 检查索引是否存在
                if index_name not in existing_indexes:
                    missing.append(
                        {
                            "table": table_name,
                            "index_name": index_name,
                            "columns": idx_config["columns"],
                            "description": idx_config.get("description", ""),
                        }
                    )

            return missing
        except Exception:
            logger.error("检查缺失索引失败", exc_info=True)
            return []
        finally:
            db.close()

    @staticmethod
    def get_table_sizes() -> List[Dict[str, Any]]:
        """
        获取表大小信息

        Returns:
            List[Dict]: 表大小信息列表
        """
        import re

        safe_pattern = re.compile(r"^[a-zA-Z0-9_]+$")

        db = SessionLocal()
        try:
            # SQLite表大小估算
            result = db.execute(text("""
                SELECT
                    name as table_name,
                    (SELECT COUNT(*) FROM pragma_table_info(name)) as column_count
                FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """))

            tables = []
            for row in result:
                table_name = row[0]

                # 验证表名只包含安全字符
                if not safe_pattern.match(table_name):
                    logger.warning(f"表名 {table_name} 包含非法字符，跳过")
                    continue

                # 获取行数
                try:
                    count_result = db.execute(  # nosec B608 — safe_pattern 白名单已防御
                        text(f"SELECT COUNT(*) FROM [{table_name}]"))
                    row_count = count_result.scalar()
                except Exception:
                    row_count = 0

                tables.append(
                    {
                        "table_name": table_name,
                        "column_count": row[1],
                        "row_count": row_count,
                    }
                )

            return tables
        except Exception:
            logger.error("获取表大小失败", exc_info=True)
            return []
        finally:
            db.close()

    @staticmethod
    def optimize_specific_table(table_name: str) -> bool:
        """
        优化特定表

        Args:
            table_name: 表名

        Returns:
            bool: 是否成功
        """
        import re

        safe_pattern = re.compile(r"^[a-zA-Z0-9_]+$")

        # 验证表名只包含安全字符（防止SQL注入）
        if not safe_pattern.match(table_name):
            logger.error("表名 %s 包含非法字符", table_name)
            return False

        db = SessionLocal()
        try:
            # 重建表索引
            db.execute(text(f"REINDEX {table_name}"))
            db.commit()
            logger.info(f"✅ 表 {table_name} 优化完成")
            return True
        except Exception:
            logger.error("表 %s 优化失败", table_name, exc_info=True)
            return False
        finally:
            db.close()

    @staticmethod
    def get_optimization_report() -> Dict[str, Any]:
        """
        生成优化报告

        Returns:
            Dict: 优化报告
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "missing_indexes": QueryOptimizer.check_missing_indexes(),
            "table_sizes": QueryOptimizer.get_table_sizes(),
            "recommendations": [],
        }

        # 生成建议
        if report["missing_indexes"]:
            report["recommendations"].append(
                {
                    "type": "index",
                    "priority": "high",
                    "message": f"发现 {len(report['missing_indexes'])} 个缺失的推荐索引",
                    "action": "运行 QueryOptimizer.create_indexes() 创建索引",
                }
            )

        # 检查大表
        large_tables = [t for t in report["table_sizes"] if t["row_count"] > 10000]
        if large_tables:
            report["recommendations"].append(
                {
                    "type": "performance",
                    "priority": "medium",
                    "message": f"发现 {len(large_tables)} 个大表（超过10000行）",
                    "action": "考虑添加分区或归档历史数据",
                    "tables": [t["table_name"] for t in large_tables],
                }
            )

        return report


def optimize_database() -> None:
    """执行完整的数据库优化流程"""
    logger.info("=" * 60)
    logger.info("开始数据库优化")
    logger.info("=" * 60)

    # 1. 创建索引
    logger.info("\n步骤1: 创建推荐索引...")
    QueryOptimizer.create_indexes()

    # 2. 优化查询缓存
    logger.info("\n步骤2: 优化查询缓存...")
    QueryOptimizer.optimize_query_cache()

    # 3. 分析表统计信息
    logger.info("\n步骤3: 分析表统计信息...")
    QueryOptimizer.analyze_tables()

    # 4. 清理数据库
    logger.info("\n步骤4: 清理数据库碎片...")
    QueryOptimizer.vacuum_database()

    logger.info("\n" + "=" * 60)
    logger.info("数据库优化完成!")
    logger.info("=" * 60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    optimize_database()


__all__ = ["QueryOptimizer", "optimize_database"]
