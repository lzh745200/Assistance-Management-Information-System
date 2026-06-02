"""
审批步骤
"""

from dataclasses import dataclass
from datetime import timezone, datetime
from typing import Optional


class ApprovalStepStatus(str):
    """审批步骤状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED = "returned"


@dataclass
class ApprovalStep:
    """审批步骤值对象"""

    step_id: str
    step_number: int
    approver_id: str
    approver_name: str
    step_name: str = "审批"
    status: str = ApprovalStepStatus.PENDING
    comment: Optional[str] = None
    acted_at: Optional[datetime] = None
    due_date: Optional[datetime] = None  # 审批截止日期

    @property
    def is_completed(self) -> bool:
        return self.status in [ApprovalStepStatus.APPROVED, ApprovalStepStatus.REJECTED]

    @property
    def is_approved(self) -> bool:
        return self.status == ApprovalStepStatus.APPROVED

    def approve(self, comment: Optional[str] = None) -> None:
        """批准步骤"""
        self.status = ApprovalStepStatus.APPROVED
        self.comment = comment
        self.acted_at = datetime.now(timezone.utc)

    def reject(self, comment: str) -> None:
        """拒绝步骤"""
        self.status = ApprovalStepStatus.REJECTED
        self.comment = comment
        self.acted_at = datetime.now(timezone.utc)

    def return_to(self, comment: str) -> None:
        """退回步骤"""
        self.status = ApprovalStepStatus.RETURNED
        self.comment = comment
        self.acted_at = datetime.now(timezone.utc)
