"""
预算值对象
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class BudgetPeriod:
    """预算周期值对象"""

    start_date: date
    end_date: date

    def __post_init__(self):
        if self.start_date > self.end_date:
            raise ValueError("开始日期不能晚于结束日期")


@dataclass
class BudgetValue:
    """预算值对象"""

    amount: Decimal
    period: BudgetPeriod
    category: Optional[str] = None
    description: Optional[str] = None

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("预算金额不能为负数")

    def is_within_period(self, check_date: date) -> bool:
        """检查日期是否在预算周期内"""
        return self.period.start_date <= check_date <= self.period.end_date

    def get_remaining_budget(self, spent: Decimal) -> Decimal:
        """计算剩余预算"""
        return self.amount - spent
