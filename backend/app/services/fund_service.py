"""Fund 业务服务 — 基本 CRUD 委托层。"""
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.fund import Fund

logger = logging.getLogger(__name__)


class FundService:
    """Fund 聚合根的基本数据操作。复杂业务逻辑委托给 lifecycle 子服务。"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_funds(self, *, page: int = 1, page_size: int = 20,
                        village_id: Optional[int] = None,
                        project_id: Optional[int] = None,
                        organization_id: Optional[int] = None) -> dict:
        query = select(Fund)
        count_q = select(func.count(Fund.id))
        if village_id:
            query = query.where(Fund.village_id == village_id)
            count_q = count_q.where(Fund.village_id == village_id)
        if project_id:
            query = query.where(Fund.project_id == project_id)
            count_q = count_q.where(Fund.project_id == project_id)
        if organization_id:
            query = query.where(Fund.organization_id == organization_id)
            count_q = count_q.where(Fund.organization_id == organization_id)
        total = (await self.db.execute(count_q)).scalar() or 0
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return {"items": result.scalars().all(), "total": total, "page": page, "page_size": page_size}

    async def get_fund(self, fund_id: int) -> Optional[Fund]:
        result = await self.db.execute(select(Fund).where(Fund.id == fund_id))
        return result.scalar_one_or_none()

    async def create_fund(self, **kwargs) -> Fund:
        fund = Fund(**kwargs)
        self.db.add(fund)
        await self.db.commit()
        await self.db.refresh(fund)
        logger.info("Fund %d created", fund.id)
        return fund

    async def update_fund(self, fund_id: int, **kwargs) -> Optional[Fund]:
        fund = await self.get_fund(fund_id)
        if not fund:
            return None
        for key, value in kwargs.items():
            if hasattr(fund, key) and value is not None:
                setattr(fund, key, value)
        await self.db.commit()
        await self.db.refresh(fund)
        return fund

    async def delete_fund(self, fund_id: int) -> bool:
        fund = await self.get_fund(fund_id)
        if not fund:
            return False
        await self.db.delete(fund)
        await self.db.commit()
        return True


# ── Backward-compat stubs（已删除的同步工具函数/数据类，供旧测试引用）──

def calculate_utilization_rate(actual: float, planned: float) -> float:
    """经费使用率 = min(实际/计划 * 100, 100)，planned≤0 且 actual>0 时返回100"""
    if planned <= 0:
        return 100.0 if actual > 0 else 0.0
    return min(actual / planned * 100.0, 100.0)


def calculate_total_from_yearly_values(values: list) -> float:
    """年度值列表求和，忽略 None"""
    return sum(v for v in values if v is not None)


class FundStatistics:
    """经费统计数据结构 — backward compat"""
    def __init__(self, fund_type: str, fund_type_label: str,
                 military_investment: float = 0.0, local_investment: float = 0.0,
                 planned_investment: float = 0.0, total_investment: float = 0.0,
                 utilization_rate: float = 0.0):
        self.fund_type = fund_type
        self.fund_type_label = fund_type_label
        self.military_investment = military_investment
        self.local_investment = local_investment
        self.planned_investment = planned_investment
        self.total_investment = total_investment
        self.utilization_rate = utilization_rate

    def to_dict(self) -> dict:
        return {
            "fund_type": self.fund_type,
            "fund_type_label": self.fund_type_label,
            "military_investment": round(self.military_investment, 2),
            "local_investment": round(self.local_investment, 2),
            "planned_investment": round(self.planned_investment, 2),
            "total_investment": round(self.total_investment, 2),
            "utilization_rate": round(self.utilization_rate, 2),
        }


class YearlyFundSummary:
    """年度经费汇总 — backward compat"""
    def __init__(self, year: int, total_military: float = 0.0, total_local: float = 0.0,
                 total_planned: float = 0.0, total_actual: float = 0.0,
                 utilization_rate: float = 0.0, by_type: dict | None = None):
        self.year = year
        self.total_military = total_military
        self.total_local = total_local
        self.total_planned = total_planned
        self.total_actual = total_actual
        self.utilization_rate = utilization_rate
        self.by_type = by_type or {}

    def to_dict(self) -> dict:
        return {
            "year": self.year,
            "total_military": round(self.total_military, 2),
            "total_local": round(self.total_local, 2),
            "total_planned": round(self.total_planned, 2),
            "total_actual": round(self.total_actual, 2),
            "utilization_rate": round(self.utilization_rate, 2),
            "by_type": {k: v.to_dict() if hasattr(v, "to_dict") else v for k, v in self.by_type.items()},
        }


FUND_TYPES = {
    "transition": "过渡期经费",
    "industry": "产业帮扶",
    "infrastructure": "基础设施",
    "party_building": "党建帮扶",
    "medical": "医疗帮扶",
    "education": "教育帮扶",
}
