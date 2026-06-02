"""
审批领域服务

处理跨聚合的业务逻辑
"""

from typing import List, Optional, Dict
from datetime import timezone, datetime

from app.services.domain import DomainService
from .approval_aggregate import ApprovalAggregate, ApprovalStatus, ApprovalType


class ApprovalDomainService(DomainService):
    """审批领域服务"""

    def execute(self, *args, **kwargs):
        """执行领域服务"""

    def calculate_approval_metrics(self, approvals: List[ApprovalAggregate]) -> Dict:
        """计算审批统计指标"""
        total = len(approvals)
        if total == 0:
            return {
                "total": 0,
                "approved": 0,
                "rejected": 0,
                "pending": 0,
                "approval_rate": 0.0,
                "avg_duration_hours": 0.0,
            }

        approved = sum(1 for a in approvals if a.status == ApprovalStatus.APPROVED)
        rejected = sum(1 for a in approvals if a.status == ApprovalStatus.REJECTED)
        pending = sum(1 for a in approvals if a.status in [ApprovalStatus.SUBMITTED, ApprovalStatus.IN_REVIEW])

        # 计算平均审批时长
        durations = []
        for a in approvals:
            if a.is_completed and hasattr(a, "_completed_at") and hasattr(a, "_created_at"):
                # 简化的时长计算
                durations.append(24.0)  # 默认24小时，实际需要改进

        avg_duration = sum(durations) / len(durations) if durations else 0.0

        return {
            "total": total,
            "approved": approved,
            "rejected": rejected,
            "pending": pending,
            "approval_rate": approved / total if total > 0 else 0.0,
            "avg_duration_hours": avg_duration,
        }

    def can_approve(self, approval: ApprovalAggregate, approver_id: str) -> bool:
        """检查用户是否可以审批"""
        if approval.status != ApprovalStatus.IN_REVIEW:
            return False

        current_step = approval.current_step
        if not current_step:
            return False

        return current_step.approver_id == approver_id

    def build_approval_chain(self, approval_type: ApprovalType, amount: Optional[float] = None) -> List[Dict]:
        """根据审批类型和金额构建审批链"""
        chain = []

        # 基础审批链
        if approval_type == ApprovalType.FUND_APPLICATION:
            if amount and amount > 100000:  # 大额资金
                chain = [
                    {"step_name": "部门初审", "role": "dept_manager"},
                    {"step_name": "财务审核", "role": "finance"},
                    {"step_name": "领导审批", "role": "leader"},
                ]
            else:
                chain = [
                    {"step_name": "部门初审", "role": "dept_manager"},
                    {"step_name": "财务审核", "role": "finance"},
                ]
        elif approval_type == ApprovalType.PROJECT_PROPOSAL:
            chain = [
                {"step_name": "项目初审", "role": "project_manager"},
                {"step_name": "专家评审", "role": "expert"},
                {"step_name": "领导审批", "role": "leader"},
            ]
        elif approval_type == ApprovalType.EXPENSE_CLAIM:
            if amount and amount > 5000:
                chain = [
                    {"step_name": "部门审核", "role": "dept_manager"},
                    {"step_name": "财务审批", "role": "finance"},
                ]
            else:
                chain = [{"step_name": "部门审核", "role": "dept_manager"}]
        else:
            chain = [{"step_name": "审批", "role": "manager"}]

        return chain

    def check_approval_deadline(self, approval: ApprovalAggregate, deadline_hours: int = 48) -> Dict:
        """检查审批是否临近或已超期"""
        if approval.is_completed:
            return {"status": "completed", "overdue": False}

        if approval.status not in [ApprovalStatus.SUBMITTED, ApprovalStatus.IN_REVIEW]:
            return {"status": "not_active", "overdue": False}

        # 简化的超期检查
        created = getattr(approval, "_created_at", datetime.now(timezone.utc))
        aware_created = created.replace(tzinfo=timezone.utc) if created.tzinfo is None else created
        elapsed = (datetime.now(timezone.utc) - aware_created).total_seconds() / 3600

        overdue = elapsed > deadline_hours
        approaching = elapsed > (deadline_hours * 0.75) and not overdue

        return {
            "status": "overdue" if overdue else "approaching" if approaching else "normal",
            "overdue": overdue,
            "elapsed_hours": round(elapsed, 2),
            "deadline_hours": deadline_hours,
        }

    def get_approval_summary(self, approval: ApprovalAggregate) -> Dict:
        """获取审批摘要"""
        return {
            "approval_id": approval.id,
            "title": getattr(approval, "_title", ""),
            "type": approval.approval_type.value,
            "status": approval.status.value,
            "applicant_id": approval.applicant_id,
            "progress": f"{approval.completed_steps}/{approval.total_steps}",
            "progress_percentage": round(approval.progress_percentage, 1),
            "is_completed": approval.is_completed,
        }
