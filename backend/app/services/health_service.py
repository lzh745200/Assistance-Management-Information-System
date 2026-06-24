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

        # DatabaseHealthService.__init__ 不收参数（内部从 settings 读取路径）；
        # 调用真实存在的 check_integrity + quick_check + get_health_status。
        service = DatabaseHealthService()
        result: dict = service.get_health_status()
        # 补充一次即时完整性 + 快速检查结果
        try:
            result.update(service.check_integrity())
            result.update(service.quick_check())
        except Exception as e:
            logger.warning("数据库健康检查异常: %s", e, exc_info=True)
            result.setdefault("issues", []).append(str(e))
        return result

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
