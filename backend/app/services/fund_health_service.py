"""资金健康评分服务。

从 projects.py 提取的健康评分逻辑。
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.fund import Fund
from app.models.fund_lifecycle import FundAnomaly

logger = logging.getLogger(__name__)


class FundHealthService:
    """资金健康状态计算和监控。"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_health_score(self, fund_id: int) -> dict:
        """计算单个资金记录的健康评分（0-100）。"""
        fund = await self.db.get(Fund, fund_id)
        if not fund:
            return {"fund_id": fund_id, "score": 0, "status": "not_found"}

        score = 100

        # 检查未解决的异常
        anomalies_result = await self.db.execute(
            select(func.count(FundAnomaly.id))
            .where(FundAnomaly.fund_id == fund_id, FundAnomaly.resolved == False)  # noqa: E712
        )
        unresolved = anomalies_result.scalar() or 0
        score -= min(unresolved * 10, 40)

        # 检查预算使用率（使用批准金额或计划金额作为预算基准）
        budget = fund.approved_amount or fund.planned_amount or fund.amount
        if budget and float(budget) > 0:
            usage_rate = float(fund.used_amount or 0) / float(budget)
            if usage_rate > 1.0:
                score -= 20  # 超预算
            elif usage_rate > 0.9:
                score -= 5   # 接近超预算

        score = max(0, min(100, score))
        status = "healthy" if score >= 80 else ("warning" if score >= 60 else "critical")
        return {
            "fund_id": fund_id,
            "score": score,
            "status": status,
            "unresolved_anomalies": unresolved,
        }
