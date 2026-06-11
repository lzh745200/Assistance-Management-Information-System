"""
Fund 业务服务层 (优化版)

军用级离线桌面管理系统 - 经费管理核心业务逻辑
重构亮点：
1. 纠正架构冲突：将 AsyncSession 修正为同步 Session，与 database.py 和 API 层保持一致。
2. 事务一致性：引入 auto_commit 机制，支持在复杂业务流（如 .rrs 导入、审批流）中由外层统一控制事务。
3. 消灭 N+1：在列表和详情查询中默认注入 joinedload/selectinload。
4. 现代化数据类：使用 dataclasses 重构底部的统计数据结构，提升代码可读性与性能。
"""

import logging
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func, update
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.fund import Fund

logger = logging.getLogger(__name__)


class FundService:
    """
    Fund 聚合根的核心数据操作与业务逻辑。
    设计原则：
    - 单一职责：只处理 Fund 实体的状态变更和查询。
    - 事务控制：默认自动提交，但在复杂编排中可通过 auto_commit=False 挂起事务，防止半截子数据。
    """

    def __init__(self, db: Session):
        self.db = db

    def get_funds(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        village_id: Optional[int] = None,
        project_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> dict:
        """
        获取经费分页列表。
        优化：使用 select(func.count()) 替代 query.count()，并预加载关联数据解决 N+1。
        """
        # 1. 构建基础查询与预加载
        base_stmt = select(Fund).options(
            joinedload(Fund.project),
            joinedload(Fund.village),
            selectinload(Fund.organization)
        )

        # 2. 构建过滤条件
        filters = []
        if village_id:
            filters.append(Fund.village_id == village_id)
        if project_id:
            filters.append(Fund.project_id == project_id)
        if organization_id:
            filters.append(Fund.organization_id == organization_id)
        if status:
            filters.append(Fund.status == status)
        if keyword:
            kw = f"%{keyword}%"
            filters.append(
                (Fund.name.ilike(kw)) | (Fund.code.ilike(kw)) | (Fund.purpose.ilike(kw))
            )

        # 3. 执行 Count 查询 (不包含 eager_loads，提升 count 性能)
        count_stmt = select(func.count()).select_from(Fund)
        for f in filters:
            count_stmt = count_stmt.where(f)
        total = self.db.execute(count_stmt).scalar_one()

        # 4. 执行 Data 查询
        data_stmt = base_stmt
        for f in filters:
            data_stmt = data_stmt.where(f)

        data_stmt = data_stmt.order_by(Fund.id.desc()).offset((page - 1) * page_size).limit(page_size)

        # 使用 unique() 防止 joinedload 产生笛卡尔积重复行
        items = self.db.execute(data_stmt).scalars().unique().all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_fund(self, fund_id: int) -> Optional[Fund]:
        """获取单条经费详情，预加载关联数据。"""
        stmt = (
            select(Fund)
            .where(Fund.id == fund_id)
            .options(
                joinedload(Fund.project),
                joinedload(Fund.village),
                selectinload(Fund.organization),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create_fund(self, *, auto_commit: bool = True, **kwargs) -> Fund:
        """
        创建经费记录。
        :param auto_commit: 是否自动提交事务。在复杂业务流（如 .rrs 数据导入）中应设为 False。
        """
        fund = Fund(**kwargs)
        self.db.add(fund)
        if auto_commit:
            self.db.commit()
            self.db.refresh(fund)
            logger.info("Fund %d created and committed", fund.id)
        else:
            self.db.flush()  # flush 可以生成 ID 但不提交事务
            logger.info("Fund %d created (flushed, not committed)", fund.id)
        return fund

    def update_fund(self, fund_id: int, *, auto_commit: bool = True, **kwargs) -> Optional[Fund]:
        """更新经费记录。"""
        fund = self.get_fund(fund_id)
        if not fund:
            return None

        for key, value in kwargs.items():
            if hasattr(fund, key) and value is not None:
                setattr(fund, key, value)

        if auto_commit:
            self.db.commit()
            self.db.refresh(fund)
        else:
            self.db.flush()
        return fund

    def delete_fund(self, fund_id: int, *, auto_commit: bool = True) -> bool:
        """物理删除经费记录。"""
        fund = self.get_fund(fund_id)
        if not fund:
            return False

        self.db.delete(fund)
        if auto_commit:
            self.db.commit()
        else:
            self.db.flush()
        return True

    def batch_update_status(self, fund_ids: List[int], new_status: str, *, auto_commit: bool = True) -> int:
        """
        批量更新经费状态 (用于 .rrs 数据同步或批量审批)。
        优化：使用 SQLAlchemy 2.0 的 bulk update，避免 N+1 循环，性能极高。
        """
        if not fund_ids:
            return 0

        stmt = (
            update(Fund)
            .where(Fund.id.in_(fund_ids))
            .values(status=new_status)
        )
        result = self.db.execute(stmt)

        if auto_commit:
            self.db.commit()
        else:
            self.db.flush()

        return result.rowcount


# ============================================================================
# Backward-compat stubs (现代化重构：使用 dataclasses 替代老旧的 class)
# ============================================================================

def calculate_utilization_rate(actual: float, planned: float) -> float:
    """经费使用率 = min(实际/计划 * 100, 100)，planned≤0 且 actual>0 时返回100"""
    if planned <= 0:
        return 100.0 if actual > 0 else 0.0
    return min(actual / planned * 100.0, 100.0)


def calculate_total_from_yearly_values(values: list) -> float:
    """年度值列表求和，忽略 None"""
    return sum(v for v in values if v is not None)


@dataclass
class FundStatistics:
    """经费统计数据结构 (Dataclass 优化版，自带 __init__ 和 __repr__)"""
    fund_type: str
    fund_type_label: str
    military_investment: float = 0.0
    local_investment: float = 0.0
    planned_investment: float = 0.0
    total_investment: float = 0.0
    utilization_rate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        for k in ["military_investment", "local_investment", "planned_investment",
                  "total_investment", "utilization_rate"]:
            data[k] = round(data[k], 2)
        return data


@dataclass
class YearlyFundSummary:
    """年度经费汇总 (Dataclass 优化版)"""
    year: int
    total_military: float = 0.0
    total_local: float = 0.0
    total_planned: float = 0.0
    total_actual: float = 0.0
    utilization_rate: float = 0.0
    by_type: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        for k in ["total_military", "total_local", "total_planned",
                  "total_actual", "utilization_rate"]:
            data[k] = round(data[k], 2)

        # 递归转换 by_type
        data["by_type"] = {
            k: v.to_dict() if hasattr(v, "to_dict") else v
            for k, v in self.by_type.items()
        }
        return data


FUND_TYPES = {
    "transition": "过渡期经费",
    "industry": "产业帮扶",
    "infrastructure": "基础设施",
    "party_building": "党建帮扶",
    "medical": "医疗帮扶",
    "education": "教育帮扶",
}
