"""
数据库索引优化脚本
为常用查询字段添加索引，提升查询性能
"""

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def create_indexes(db: Session):
    """
    创建数据库索引

    Args:
        db: 数据库会话
    """
    indexes = [
        # 村庄表索引
        "CREATE INDEX IF NOT EXISTS idx_villages_org_id ON villages(org_id)",
        "CREATE INDEX IF NOT EXISTS idx_villages_name ON villages(name)",
        "CREATE INDEX IF NOT EXISTS idx_villages_code ON villages(code)",
        "CREATE INDEX IF NOT EXISTS idx_villages_created_at ON villages(created_at)",
        # 项目表索引
        "CREATE INDEX IF NOT EXISTS idx_projects_org_id ON projects(organization_id)",
        "CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name)",
        "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)",
        "CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_projects_start_date ON projects(start_date)",
        # 资金表索引
        "CREATE INDEX IF NOT EXISTS idx_funds_org_id ON funds(org_id)",
        "CREATE INDEX IF NOT EXISTS idx_funds_name ON funds(name)",
        "CREATE INDEX IF NOT EXISTS idx_funds_type ON funds(type)",
        "CREATE INDEX IF NOT EXISTS idx_funds_created_at ON funds(created_at)",
        # 学校表索引
        "CREATE INDEX IF NOT EXISTS idx_schools_org_id ON schools(org_id)",
        "CREATE INDEX IF NOT EXISTS idx_schools_name ON schools(name)",
        "CREATE INDEX IF NOT EXISTS idx_schools_type ON schools(type)",
        # 数据包表索引
        "CREATE INDEX IF NOT EXISTS idx_data_packages_org_id ON data_packages(org_id)",
        "CREATE INDEX IF NOT EXISTS idx_data_packages_package_code ON data_packages(package_code)",
        "CREATE INDEX IF NOT EXISTS idx_data_packages_status ON data_packages(status)",
        "CREATE INDEX IF NOT EXISTS idx_data_packages_created_at ON data_packages(created_at)",
        # 数据上报表索引
        "CREATE INDEX IF NOT EXISTS idx_data_reports_source_org_id ON data_reports(source_org_id)",
        "CREATE INDEX IF NOT EXISTS idx_data_reports_target_org_id ON data_reports(target_org_id)",
        "CREATE INDEX IF NOT EXISTS idx_data_reports_status ON data_reports(status)",
        "CREATE INDEX IF NOT EXISTS idx_data_reports_submitted_at ON data_reports(submitted_at)",
        "CREATE INDEX IF NOT EXISTS idx_data_reports_deadline ON data_reports(deadline)",
        # 导入导出历史表索引
        "CREATE INDEX IF NOT EXISTS idx_import_export_history_org_id ON import_export_history(org_id)",
        "CREATE INDEX IF NOT EXISTS idx_import_export_history_type ON import_export_history(type)",
        "CREATE INDEX IF NOT EXISTS idx_import_export_history_created_at ON import_export_history(created_at)",
        # 用户表索引（如果不存在）
        "CREATE INDEX IF NOT EXISTS idx_users_organization_id ON users(organization_id)",
        "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
        "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)",
        # 组织表索引
        "CREATE INDEX IF NOT EXISTS idx_organizations_parent_id ON organizations(parent_id)",
        "CREATE INDEX IF NOT EXISTS idx_organizations_code ON organizations(code)",
        "CREATE INDEX IF NOT EXISTS idx_organizations_is_active ON organizations(is_active)",
        # 村民表索引
        "CREATE INDEX IF NOT EXISTS idx_villagers_village_id ON villagers(village_id)",
        "CREATE INDEX IF NOT EXISTS idx_villagers_name ON villagers(name)",
        "CREATE INDEX IF NOT EXISTS idx_villagers_id_card ON villagers(id_card)",
        # 产业表索引
        "CREATE INDEX IF NOT EXISTS idx_industries_village_id ON industries(village_id)",
        "CREATE INDEX IF NOT EXISTS idx_industries_name ON industries(name)",
        "CREATE INDEX IF NOT EXISTS idx_industries_type ON industries(type)",
        # 资金预算表索引
        "CREATE INDEX IF NOT EXISTS idx_fund_budgets_org_id ON fund_budgets(org_id)",
        "CREATE INDEX IF NOT EXISTS idx_fund_budgets_year ON fund_budgets(year)",
        # 资金拨付单表索引
        "CREATE INDEX IF NOT EXISTS idx_fund_allocation_orders_org_id ON fund_allocation_orders(org_id)",
        "CREATE INDEX IF NOT EXISTS idx_fund_allocation_orders_status ON fund_allocation_orders(status)",
        "CREATE INDEX IF NOT EXISTS idx_fund_allocation_orders_created_at ON fund_allocation_orders(created_at)",
    ]

    success_count = 0
    error_count = 0

    for index_sql in indexes:
        try:
            db.execute(text(index_sql))
            success_count += 1
            logger.debug(f"创建索引成功: {index_sql}")
        except Exception as e:
            error_count += 1
            logger.warning(f"创建索引失败: {index_sql}, 错误: {str(e)}")

    db.commit()

    logger.info(f"索引创建完成: 成功 {success_count} 个, 失败 {error_count} 个")

    return {"success": success_count, "failed": error_count, "total": len(indexes)}


def analyze_database(db: Session):
    """
    分析数据库，更新统计信息

    Args:
        db: 数据库会话
    """
    try:
        # SQLite的ANALYZE命令
        db.execute(text("ANALYZE"))
        db.commit()
        logger.info("数据库分析完成")
        return True
    except Exception as e:
        logger.error(f"数据库分析失败: {str(e)}")
        return False


def get_index_info(db: Session) -> list:
    """
    获取索引信息

    Args:
        db: 数据库会话

    Returns:
        索引信息列表
    """
    try:
        # SQLite查询索引信息
        result = db.execute(
            text("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
        )

        indexes = []
        for row in result:
            indexes.append({"name": row[0], "table": row[1], "sql": row[2]})

        return indexes
    except Exception as e:
        logger.error(f"获取索引信息失败: {str(e)}")
        return []


def optimize_database(db: Session):
    """
    优化数据库

    Args:
        db: 数据库会话
    """
    try:
        # 创建索引
        index_result = create_indexes(db)

        # 分析数据库
        analyze_result = analyze_database(db)

        # 执行VACUUM（清理碎片，回收空间）
        # 注意：VACUUM会锁定数据库，大数据库可能需要较长时间
        # db.execute(text("VACUUM"))
        # db.commit()

        return {
            "indexes": index_result,
            "analyzed": analyze_result,
            "vacuumed": False,
        }  # 暂不执行VACUUM
    except Exception as e:
        logger.error(f"数据库优化失败: {str(e)}")
        return {"error": str(e)}
