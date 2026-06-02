"""
审批工作流域

核心业务：
- 审批流程管理
- 审批任务分配
- 审批历史记录
- 审批规则引擎
"""

from .approval_aggregate import ApprovalAggregate, ApprovalStatus, ApprovalType
from .approval_step import ApprovalStep, ApprovalStepStatus
from .approval_repository import ApprovalRepository
from .approval_domain_service import ApprovalDomainService
from .value_objects import ApprovalStatus as ApprovalStatusVO

__all__ = [
    "ApprovalAggregate",
    "ApprovalStatus",
    "ApprovalType",
    "ApprovalStep",
    "ApprovalStepStatus",
    "ApprovalRepository",
    "ApprovalDomainService",
    "ApprovalStatusVO",
]
