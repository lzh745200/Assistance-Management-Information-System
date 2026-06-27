"""
村庄级联删除服务
由于 SQLite 外键约束未正确设置 CASCADE,需要在应用层实现级联删除
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class VillageCascadeDeleteService:
    """村庄级联删除服务"""

    # 需要级联删除的表(按依赖顺序)
    DEPENDENT_TABLES = [
        # 年度数据表
        ("annual_population", "supported_village_id"),
        ("annual_infrastructure", "supported_village_id"),
        ("annual_industry", "supported_village_id"),
        ("annual_income", "supported_village_id"),
        # 帮扶支持表
        ("consumption_support", "supported_village_id"),
        ("education_support", "supported_village_id"),
        ("employment_support", "supported_village_id"),
        ("force_investment", "supported_village_id"),
        ("industry_support", "supported_village_id"),
        ("infrastructure_improvement", "supported_village_id"),
        ("medical_support", "supported_village_id"),
        ("party_building_support", "supported_village_id"),
        ("support_funding", "supported_village_id"),
        # 村委会信息
        ("village_committee_members", "supported_village_id"),
        ("village_committee_info", "supported_village_id"),
        # 村庄数据
        ("village_income", "supported_village_id"),
        ("village_population", "supported_village_id"),
        # 资金和项目
        ("fund_transactions", "village_id"),
        ("fund_budgets", "village_id"),
        ("funds", "village_id"),
        ("projects", "village_id"),
        # 工作日志
        ("work_logs", "village_id"),
    ]

    def __init__(self, db: Session):
        self.db = db

    def delete_village_cascade(self, village_id: int) -> dict:
        """
        级联删除村庄及其所有相关数据

        Args:
            village_id: 村庄ID

        Returns:
            删除统计信息
        """
        logger.info(f"开始级联删除村庄 ID={village_id}")

        delete_stats = {}
        total_deleted = 0

        try:
            # 1. 删除所有依赖表的记录
            for table_name, column_name in self.DEPENDENT_TABLES:
                try:
                    result = self.db.execute(
                        text(f"DELETE FROM {table_name} WHERE {column_name} = :village_id"),  # nosec B608
                        {"village_id": village_id},
                    )
                    deleted_count = result.rowcount
                    if deleted_count > 0:
                        delete_stats[table_name] = deleted_count
                        total_deleted += deleted_count
                        logger.info(f"  删除 {table_name}: {deleted_count} 条记录")
                except Exception as e:
                    # 表可能不存在或列名不同,记录警告但继续
                    logger.warning(f"  删除 {table_name} 失败: {e}")

            # 2. 删除村庄本身
            result = self.db.execute(
                text("DELETE FROM supported_villages WHERE id = :village_id"),
                {"village_id": village_id},
            )
            village_deleted = result.rowcount

            if village_deleted == 0:
                logger.warning(f"村庄 ID={village_id} 不存在")
                return {"success": False, "message": "村庄不存在", "deleted_records": 0}

            # 3. 提交事务
            self.db.commit()

            logger.info(f"级联删除完成: 村庄 ID={village_id}, 总计删除 {total_deleted + 1} 条记录")

            return {
                "success": True,
                "message": "删除成功",
                "village_id": village_id,
                "deleted_records": total_deleted + 1,
                "details": delete_stats,
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"级联删除失败: {e}", exc_info=True)
            raise

    def check_village_references(self, village_id: int) -> dict:
        """
        检查村庄的引用情况

        Args:
            village_id: 村庄ID

        Returns:
            引用统计信息
        """
        reference_stats = {}
        total_refs = 0

        for table_name, column_name in self.DEPENDENT_TABLES:
            try:
                result = self.db.execute(
                    text(f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} = :village_id"),  # nosec B608
                    {"village_id": village_id},
                )
                count = result.scalar()
                if count > 0:
                    reference_stats[table_name] = count
                    total_refs += count
            except Exception:
                # 表可能不存在,忽略
                pass

        return {
            "village_id": village_id,
            "total_references": total_refs,
            "details": reference_stats,
        }
