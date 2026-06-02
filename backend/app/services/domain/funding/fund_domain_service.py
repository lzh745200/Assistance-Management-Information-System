"""
经费领域服务
"""

from decimal import Decimal
from .fund_aggregate import FundAggregate
from .budget_value import BudgetValue


class FundDomainService:
    """经费领域服务"""

    def calculate_budget_usage_rate(self, budget: BudgetValue, spent: Decimal) -> float:
        """计算预算使用率"""
        if budget.amount == 0:
            return 0.0
        return float(spent / budget.amount * 100)

    def check_budget_overrun(self, budget: BudgetValue, spent: Decimal) -> bool:
        """检查是否超预算"""
        return spent > budget.amount

    def can_allocate_fund(self, fund: FundAggregate, amount: Decimal) -> bool:
        """检查是否可以分配经费"""
        # 简化实现，实际应该检查预算余额
        return amount > 0
