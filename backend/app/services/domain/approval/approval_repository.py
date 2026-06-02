"""
审批仓储接口
"""

from typing import List, Optional
from app.services.domain import Repository
from .approval_aggregate import ApprovalAggregate, ApprovalStatus


class ApprovalRepository(Repository[ApprovalAggregate]):
    """审批仓储"""

    def get_by_id(self, id: str) -> Optional[ApprovalAggregate]:
        """根据ID获取审批"""
        raise NotImplementedError()

    def save(self, aggregate: ApprovalAggregate) -> None:
        """保存审批"""
        raise NotImplementedError()

    def delete(self, id: str) -> None:
        """删除审批"""
        raise NotImplementedError()

    def get_by_applicant(self, applicant_id: str) -> List[ApprovalAggregate]:
        """获取申请人的审批列表"""
        raise NotImplementedError()

    def get_by_approver(self, approver_id: str) -> List[ApprovalAggregate]:
        """获取待审批人审批列表"""
        raise NotImplementedError()

    def get_by_target(self, target_id: str, target_type: str) -> List[ApprovalAggregate]:
        """获取关联业务对象的审批历史"""
        raise NotImplementedError()

    def get_by_status(self, status: ApprovalStatus) -> List[ApprovalAggregate]:
        """根据状态获取审批列表"""
        raise NotImplementedError()

    def get_pending_approvals(self, approver_id: str) -> List[ApprovalAggregate]:
        """获取待审批列表"""
        raise NotImplementedError()

    def get_overdue_approvals(self) -> List[ApprovalAggregate]:
        """获取超期审批"""
        raise NotImplementedError()
