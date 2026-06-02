"""
经费聚合根

经费是资金管理的聚合根，封装了经费的生命周期和业务规则。
"""

from datetime import timezone, datetime
from decimal import Decimal
from typing import List, Optional
from enum import Enum

from app.services.domain import AggregateRoot, DomainEvent, ValueObject
from app.services.event_bus import event_bus


class FundStatus(str, Enum):
    """经费状态"""

    DRAFT = "draft"  # 草稿
    PENDING = "pending"  # 待审批
    APPROVED = "approved"  # 已批准
    ALLOCATED = "allocated"  # 已拨付
    IN_USE = "in_use"  # 使用中
    FROZEN = "frozen"  # 已冻结
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class BudgetAllocation(ValueObject):
    """预算分配值对象"""

    def __init__(
        self, category: str, amount: Decimal, used_amount: Decimal = Decimal("0"), frozen_amount: Decimal = Decimal("0")
    ):
        self.category = category
        self.amount = amount
        self.used_amount = used_amount
        self.frozen_amount = frozen_amount

    @property
    def available_amount(self) -> Decimal:
        """可用金额"""
        return self.amount - self.used_amount - self.frozen_amount

    def can_allocate(self, amount: Decimal) -> bool:
        """检查是否可分配指定金额"""
        return self.available_amount >= amount


class FundAggregate(AggregateRoot):
    """
    经费聚合根

    职责：
    - 维护经费的基本信息和状态
    - 管理预算分配
    - 确保业务规则的一致性
    """

    def __init__(
        self,
        fund_id: str,
        project_id: str,
        total_budget: Decimal,
        fiscal_year: int,
        status: FundStatus = FundStatus.DRAFT,
    ):
        super().__init__(fund_id)
        self._project_id = project_id
        self._total_budget = total_budget
        self._fiscal_year = fiscal_year
        self._status = status
        self._allocations: List[BudgetAllocation] = []
        self._created_at = datetime.now(timezone.utc)
        self._updated_at = datetime.now(timezone.utc)

    # 属性访问
    @property
    def project_id(self) -> str:
        return self._project_id

    @property
    def total_budget(self) -> Decimal:
        return self._total_budget

    @property
    def fiscal_year(self) -> int:
        return self._fiscal_year

    @property
    def status(self) -> FundStatus:
        return self._status

    @property
    def allocations(self) -> List[BudgetAllocation]:
        return self._allocations.copy()

    # 业务方法
    def submit_for_approval(self) -> None:
        """提交审批"""
        if self._status != FundStatus.DRAFT:
            raise ValueError(f"无法从 {self._status} 状态提交审批")

        self._status = FundStatus.PENDING
        self._updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="FUND_SUBMITTED",
            aggregate_id=self.id,
            aggregate_type="Fund",
            occurred_at=datetime.now(timezone.utc),
            payload={"previous_status": FundStatus.DRAFT.value},
        )
        self.apply_event(event)

        # 发布事件到事件总线
        event_bus.publish_sync(event)

    def approve(self, approver_id: str, comment: Optional[str] = None) -> None:
        """批准经费"""
        if self._status != FundStatus.PENDING:
            raise ValueError(f"无法批准 {self._status} 状态的经费")

        self._status = FundStatus.APPROVED
        self._updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="FUND_APPROVED",
            aggregate_id=self.id,
            aggregate_type="Fund",
            occurred_at=datetime.now(timezone.utc),
            payload={"approver_id": approver_id, "comment": comment},
        )
        self.apply_event(event)

        # 发布事件到事件总线
        event_bus.publish_sync(event)

    def allocate_budget(self, category: str, amount: Decimal) -> None:
        """分配预算"""
        if self._status not in [FundStatus.APPROVED, FundStatus.ALLOCATED]:
            raise ValueError(f"无法在 {self._status} 状态分配预算")

        # 检查总额度
        current_allocated = sum(a.amount for a in self._allocations)
        if current_allocated + amount > self._total_budget:
            raise ValueError("分配金额超过总预算")

        # 查找或创建分配
        existing = next((a for a in self._allocations if a.category == category), None)
        if existing:
            # 更新现有分配
            new_allocation = BudgetAllocation(
                category=category,
                amount=existing.amount + amount,
                used_amount=existing.used_amount,
                frozen_amount=existing.frozen_amount,
            )
            self._allocations = [a for a in self._allocations if a.category != category]
            self._allocations.append(new_allocation)
        else:
            self._allocations.append(BudgetAllocation(category=category, amount=amount))

        self._status = FundStatus.ALLOCATED
        self._updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="BUDGET_ALLOCATED",
            aggregate_id=self.id,
            aggregate_type="Fund",
            occurred_at=datetime.now(timezone.utc),
            payload={"category": category, "amount": str(amount)},
        )
        self.apply_event(event)

        # 发布事件到事件总线
        event_bus.publish_sync(event)

    def use_funds(self, category: str, amount: Decimal) -> None:
        """使用经费"""
        allocation = next((a for a in self._allocations if a.category == category), None)
        if not allocation:
            raise ValueError(f"类别 {category} 未分配预算")

        if not allocation.can_allocate(amount):
            raise ValueError(f"类别 {category} 可用余额不足")

        # 更新分配
        new_allocation = BudgetAllocation(
            category=category,
            amount=allocation.amount,
            used_amount=allocation.used_amount + amount,
            frozen_amount=allocation.frozen_amount,
        )
        self._allocations = [a for a in self._allocations if a.category != category]
        self._allocations.append(new_allocation)

        self._status = FundStatus.IN_USE
        self._updated_at = datetime.now(timezone.utc)

    def freeze(self, reason: str) -> None:
        """冻结经费"""
        if self._status in [FundStatus.COMPLETED, FundStatus.CANCELLED]:
            raise ValueError(f"无法冻结 {self._status} 状态的经费")

        previous_status = self._status
        self._status = FundStatus.FROZEN
        self._updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="FUND_FROZEN",
            aggregate_id=self.id,
            aggregate_type="Fund",
            occurred_at=datetime.now(timezone.utc),
            payload={"previous_status": previous_status.value, "reason": reason},
        )
        self.apply_event(event)

        # 发布事件到事件总线
        event_bus.publish_sync(event)

    def unfreeze(self) -> None:
        """解冻经费"""
        if self._status != FundStatus.FROZEN:
            raise ValueError("只有冻结状态的经费可以解冻")

        # 恢复到之前的状态（简化处理，实际应存储历史状态）
        self._status = FundStatus.IN_USE
        self._updated_at = datetime.now(timezone.utc)

    def complete(self) -> None:
        """完成经费使用"""
        if self._status not in [FundStatus.IN_USE, FundStatus.ALLOCATED]:
            raise ValueError(f"无法完成 {self._status} 状态的经费")

        self._status = FundStatus.COMPLETED
        self._updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="FUND_COMPLETED",
            aggregate_id=self.id,
            aggregate_type="Fund",
            occurred_at=datetime.now(timezone.utc),
            payload={},
        )
        self.apply_event(event)

        # 发布事件到事件总线
        event_bus.publish_sync(event)

    # 查询方法
    def get_total_used(self) -> Decimal:
        """获取已使用总额"""
        return sum(a.used_amount for a in self._allocations)

    def get_total_available(self) -> Decimal:
        """获取可用总额"""
        return sum(a.available_amount for a in self._allocations)

    def get_utilization_rate(self) -> float:
        """获取使用率"""
        if self._total_budget == 0:
            return 0.0
        return float(self.get_total_used() / self._total_budget)
