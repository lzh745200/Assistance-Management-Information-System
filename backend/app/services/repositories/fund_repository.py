"""Fund 聚合根数据访问。"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from .base import BaseRepository
from app.models.fund import Fund
from app.models.fund_lifecycle import (
    ProjectFundPhase, BudgetBaseline,
    FundAnomaly,
)
from app.models.fund_budget import FundTransaction


class FundRepository(BaseRepository):
    """Fund 及其子实体的聚合根查询。"""

    async def get_with_attachments(self, fund_id: int) -> Optional[Fund]:
        result = await self.db.execute(
            select(Fund).where(Fund.id == fund_id)
            .options(selectinload(Fund.attachments))
        )
        return result.scalar_one_or_none()

    async def get_lifecycle_phases(self, fund_id: int) -> List[ProjectFundPhase]:
        result = await self.db.execute(
            select(ProjectFundPhase).where(ProjectFundPhase.fund_id == fund_id)
            .order_by(ProjectFundPhase.phase_order)
        )
        return list(result.scalars().all())

    async def get_transactions(self, fund_id: int,
                               *, date_range: Optional[tuple] = None) -> List[FundTransaction]:
        query = select(FundTransaction).where(FundTransaction.fund_id == fund_id)
        if date_range:
            start, end = date_range
            query = query.where(FundTransaction.created_at.between(start, end))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_budget_baselines(self, fund_id: int) -> List[BudgetBaseline]:
        result = await self.db.execute(
            select(BudgetBaseline).where(BudgetBaseline.fund_id == fund_id)
        )
        return list(result.scalars().all())

    async def get_anomalies(self, fund_id: int,
                            *, resolved: Optional[bool] = None) -> List[FundAnomaly]:
        query = select(FundAnomaly).where(FundAnomaly.fund_id == fund_id)
        if resolved is not None:
            query = query.where(FundAnomaly.resolved == resolved)
        result = await self.db.execute(query)
        return list(result.scalars().all())
