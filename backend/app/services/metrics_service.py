"""指标服务 — 委托给 BusinessMetricsService。"""
from app.services.business_metrics_service import BusinessMetricsService


class MetricsService:
    @staticmethod
    async def get_kpi_dashboard(db):
        service = BusinessMetricsService(db)
        return await service.get_kpi_summary()
