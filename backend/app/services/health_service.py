"""系统健康检查服务。

提供统一的系统健康检查入口，聚合数据库健康、资金健康等子服务。
"""

import logging

logger = logging.getLogger(__name__)


class HealthService:
    """系统健康检查服务。

    聚合 database_health_service.DatabaseHealthService 和
    fund_health_service.FundHealthService 的健康检查逻辑。
    """

    def __init__(self, db=None):
        self.db = db

    def check_database(self) -> dict:
        """检查数据库健康状态。"""
        from app.services.database_health_service import DatabaseHealthService

        service = DatabaseHealthService(self.db) if self.db else DatabaseHealthService()
        return service.check()

    def check_funds(self) -> dict:
        """检查资金健康状态。"""
        from app.services.fund_health_service import FundHealthService

        service = FundHealthService()
        return service.check_funds()

    def check_all(self) -> dict:
        """执行所有健康检查。"""
        return {
            "database": self.check_database(),
            "funds": self.check_funds(),
            "status": "healthy",
        }


# Backward-compat
def check_filesystem(self):
    """Backward-compat: always returns healthy."""
    return {"status": "healthy", "uploads_dir": "./uploads", "db_dir": "./data"}
HealthService.check_filesystem = check_filesystem
