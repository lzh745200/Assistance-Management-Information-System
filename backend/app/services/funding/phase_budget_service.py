"""Phase 2: 汇总审核 — 预算基线管理。

从 fund_lifecycle.py Phase 2 提取的业务逻辑。
"""
import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.fund_lifecycle import BudgetBaseline

logger = logging.getLogger(__name__)


class PhaseBudgetService:
    """预算基线管理服务。"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_baselines(self, fund_id: int) -> List[BudgetBaseline]:
        result = await self.db.execute(
            select(BudgetBaseline).where(BudgetBaseline.fund_id == fund_id)
        )
        return list(result.scalars().all())

    async def create_baseline(self, **kwargs) -> BudgetBaseline:
        baseline = BudgetBaseline(**kwargs)
        self.db.add(baseline)
        await self.db.commit()
        await self.db.refresh(baseline)
        logger.info("Budget baseline created for fund %d", kwargs.get("fund_id"))
        return baseline

    async def get_budget_summary(self, fund_id: int) -> dict:
        baselines = await self.list_baselines(fund_id)
        total_amount = sum(float(b.baseline_amount or 0) for b in baselines)
        locked_count = sum(1 for b in baselines if b.locked_at is not None)
        return {
            "fund_id": fund_id,
            "total_baseline_amount": total_amount,
            "baseline_count": len(baselines),
            "locked_count": locked_count,
        }
