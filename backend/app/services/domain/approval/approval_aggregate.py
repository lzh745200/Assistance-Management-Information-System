"""
审批聚合根

审批流是工作流的核心，管理审批的全生命周期。
"""

from datetime import timezone, datetime
from typing import List, Optional
from enum import Enum

from app.services.domain import AggregateRoot, DomainEvent
from app.services.event_bus import event_bus, EventPriority


class ApprovalStatus(str, Enum):
    """审批状态"""

    DRAFT = "draft"  # 草稿
    SUBMITTED = "submitted"  # 已提交
    IN_REVIEW = "in_review"  # 审批中
    APPROVED = "approved"  # 已通过
    REJECTED = "rejected"  # 已拒绝
    RETURNED = "returned"  # 已退回
    CANCELLED = "cancelled"  # 已取消


class ApprovalType(str, Enum):
    """审批类型"""

    FUND_APPLICATION = "fund_application"  # 经费申请
    PROJECT_PROPOSAL = "project_proposal"  # 项目申报
    EXPENSE_CLAIM = "expense_claim"  # 费用报销
    CONTRACT_REVIEW = "contract_review"  # 合同审核
    OTHER = "other"  # 其他


class ApprovalStep:
    """审批步骤值对象"""

    def __init__(
        self,
        step_id: str,
        step_number: int,
        approver_id: str,
        approver_name: str,
        step_name: str = "审批",
        status: str = "pending",
    ):
        self.step_id = step_id
        self.step_number = step_number
        self.approver_id = approver_id
        self.approver_name = approver_name
        self.step_name = step_name
        self.status = status
        self.comment: Optional[str] = None
        self.acted_at: Optional[datetime] = None

    def approve(self, comment: Optional[str] = None) -> None:
        """批准步骤"""
        self.status = "approved"
        self.comment = comment
        self.acted_at = datetime.now(timezone.utc)

    def reject(self, comment: str) -> None:
        """拒绝步骤"""
        self.status = "rejected"
        self.comment = comment
        self.acted_at = datetime.now(timezone.utc)

    def return_to(self, comment: str) -> None:
        """退回步骤"""
        self.status = "returned"
        self.comment = comment
        self.acted_at = datetime.now(timezone.utc)


class ApprovalAggregate(AggregateRoot):
    """
    审批聚合根

    职责：
    - 管理审批流程的生命周期
    - 维护审批步骤序列
    - 记录审批历史
    - 触发审批相关事件
    """

    def __init__(
        self,
        approval_id: str,
        approval_type: ApprovalType,
        applicant_id: str,
        applicant_name: str,
        target_id: str,  # 关联的业务对象ID
        target_type: str,  # 关联的业务对象类型
        title: str,
        description: Optional[str] = None,
        status: ApprovalStatus = ApprovalStatus.DRAFT,
    ):
        super().__init__(approval_id)
        self._type = approval_type
        self._applicant_id = applicant_id
        self._applicant_name = applicant_name
        self._target_id = target_id
        self._target_type = target_type
        self._title = title
        self._description = description
        self._status = status
        self._steps: List[ApprovalStep] = []
        self._current_step_index: int = 0
        self._created_at = datetime.now(timezone.utc)
        self._updated_at = datetime.now(timezone.utc)
        self._completed_at: Optional[datetime] = None

    # 属性访问
    @property
    def approval_type(self) -> ApprovalType:
        return self._type

    @property
    def status(self) -> ApprovalStatus:
        return self._status

    @property
    def applicant_id(self) -> str:
        return self._applicant_id

    @property
    def target_id(self) -> str:
        return self._target_id

    @property
    def target_type(self) -> str:
        return self._target_type

    @property
    def steps(self) -> List[ApprovalStep]:
        return self._steps.copy()

    @property
    def current_step(self) -> Optional[ApprovalStep]:
        if 0 <= self._current_step_index < len(self._steps):
            return self._steps[self._current_step_index]
        return None

    # 业务方法
    def add_step(self, step: ApprovalStep) -> None:
        """添加审批步骤"""
        if self._status != ApprovalStatus.DRAFT:
            raise ValueError("只有草稿状态的审批可以添加步骤")
        self._steps.append(step)
        self._updated_at = datetime.now(timezone.utc)

    def submit(self) -> None:
        """提交审批"""
        if self._status != ApprovalStatus.DRAFT:
            raise ValueError(f"无法从 {self._status} 状态提交")

        if not self._steps:
            raise ValueError("审批流程至少需要一步")

        self._status = ApprovalStatus.SUBMITTED
        self._updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="APPROVAL_SUBMITTED",
            aggregate_id=self.id,
            aggregate_type="Approval",
            occurred_at=datetime.now(timezone.utc),
            payload={
                "applicant_id": self._applicant_id,
                "approval_type": self._type.value,
                "target_id": self._target_id,
                "target_type": self._target_type,
            },
            priority=EventPriority.HIGH,
        )
        self.apply_event(event)
        event_bus.publish_sync(event)

        # 自动开始第一步
        self._start_current_step()

    def _start_current_step(self) -> None:
        """开始当前步骤"""
        current = self.current_step
        if current:
            self._status = ApprovalStatus.IN_REVIEW
            self._updated_at = datetime.now(timezone.utc)

            event = DomainEvent(
                event_id=f"evt_{self.id}_{self.version}",
                event_type="APPROVAL_STEP_STARTED",
                aggregate_id=self.id,
                aggregate_type="Approval",
                occurred_at=datetime.now(timezone.utc),
                payload={
                    "step_id": current.step_id,
                    "step_number": current.step_number,
                    "approver_id": current.approver_id,
                },
            )
            self.apply_event(event)
            event_bus.publish_sync(event)

    def approve_current_step(self, approver_id: str, comment: Optional[str] = None) -> None:
        """批准当前步骤"""
        if self._status != ApprovalStatus.IN_REVIEW:
            raise ValueError("审批不在进行中状态")

        current = self.current_step
        if not current:
            raise ValueError("没有当前步骤")

        if current.approver_id != approver_id:
            raise ValueError("只有指定审批人可以审批")

        current.approve(comment)
        self._updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="APPROVAL_STEP_COMPLETED",
            aggregate_id=self.id,
            aggregate_type="Approval",
            occurred_at=datetime.now(timezone.utc),
            payload={
                "step_id": current.step_id,
                "step_number": current.step_number,
                "result": "approved",
                "comment": comment,
            },
        )
        self.apply_event(event)
        event_bus.publish_sync(event)

        # 进入下一步或完成审批
        self._current_step_index += 1
        if self._current_step_index >= len(self._steps):
            self._complete_approval()
        else:
            self._start_current_step()

    def reject(self, approver_id: str, reason: str) -> None:
        """拒绝审批"""
        if self._status not in [ApprovalStatus.IN_REVIEW, ApprovalStatus.SUBMITTED]:
            raise ValueError("无法拒绝当前状态的审批")

        current = self.current_step
        if current and current.approver_id != approver_id:
            raise ValueError("只有当前步骤的审批人可以拒绝")

        self._status = ApprovalStatus.REJECTED
        self._updated_at = datetime.now(timezone.utc)
        self._completed_at = datetime.now(timezone.utc)

        if current:
            current.reject(reason)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="APPROVAL_REJECTED",
            aggregate_id=self.id,
            aggregate_type="Approval",
            occurred_at=datetime.now(timezone.utc),
            payload={"rejected_by": approver_id, "reason": reason, "step_id": current.step_id if current else None},
            priority=EventPriority.HIGH,
        )
        self.apply_event(event)
        event_bus.publish_sync(event)

    def return_to_applicant(self, approver_id: str, comment: str) -> None:
        """退回给申请人"""
        if self._status != ApprovalStatus.IN_REVIEW:
            raise ValueError("只有进行中的审批可以退回")

        current = self.current_step
        if current and current.approver_id != approver_id:
            raise ValueError("只有当前步骤的审批人可以退回")

        self._status = ApprovalStatus.RETURNED
        self._updated_at = datetime.now(timezone.utc)

        if current:
            current.return_to(comment)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="APPROVAL_RETURNED",
            aggregate_id=self.id,
            aggregate_type="Approval",
            occurred_at=datetime.now(timezone.utc),
            payload={"returned_by": approver_id, "comment": comment},
        )
        self.apply_event(event)
        event_bus.publish_sync(event)

    def _complete_approval(self) -> None:
        """完成审批（全部通过）"""
        self._status = ApprovalStatus.APPROVED
        self._updated_at = datetime.now(timezone.utc)
        self._completed_at = datetime.now(timezone.utc)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="APPROVAL_COMPLETED",
            aggregate_id=self.id,
            aggregate_type="Approval",
            occurred_at=datetime.now(timezone.utc),
            payload={"target_id": self._target_id, "target_type": self._target_type, "total_steps": len(self._steps)},
            priority=EventPriority.HIGH,
        )
        self.apply_event(event)
        event_bus.publish_sync(event)

    def cancel(self, canceller_id: str) -> None:
        """取消审批"""
        if self._status in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]:
            raise ValueError("已完成的审批不能取消")

        self._status = ApprovalStatus.CANCELLED
        self._updated_at = datetime.now(timezone.utc)

        event = DomainEvent(
            event_id=f"evt_{self.id}_{self.version}",
            event_type="APPROVAL_CANCELLED",
            aggregate_id=self.id,
            aggregate_type="Approval",
            occurred_at=datetime.now(timezone.utc),
            payload={"cancelled_by": canceller_id},
        )
        self.apply_event(event)
        event_bus.publish_sync(event)

    # 查询方法
    @property
    def is_completed(self) -> bool:
        return self._status in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]

    @property
    def total_steps(self) -> int:
        return len(self._steps)

    @property
    def completed_steps(self) -> int:
        return sum(1 for s in self._steps if s.status == "approved")

    @property
    def progress_percentage(self) -> float:
        if not self._steps:
            return 0.0
        return (self.completed_steps / len(self._steps)) * 100

    def get_step_history(self) -> List[ApprovalStep]:
        """获取已完成的步骤历史"""
        return [s for s in self._steps if s.acted_at is not None]
