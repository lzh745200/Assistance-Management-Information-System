"""
经费管理领域 (Funding Domain)

核心业务：
- 经费预算管理
- 经费申请与审批
- 资金拨付跟踪
- 经费使用监控
"""

from .fund_aggregate import FundAggregate, FundStatus, BudgetAllocation
from .budget_value import BudgetValue, BudgetPeriod
from .fund_repository import FundRepository
from .fund_domain_service import FundDomainService
from .value_objects import Money

__all__ = [
    "FundAggregate",
    "FundStatus",
    "BudgetAllocation",
    "BudgetValue",
    "BudgetPeriod",
    "FundRepository",
    "FundDomainService",
    "Money",
]
