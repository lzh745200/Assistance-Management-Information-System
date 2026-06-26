"""Approval model factories."""

from datetime import datetime, timezone

from app.models.approval import ApprovalWorkflow, ApprovalNode, ApprovalTask, ApprovalRecord


class ApprovalWorkflowFactory:
    @staticmethod
    def build(**kwargs):
        now = datetime.now(timezone.utc)
        data = dict(
            name="测试审批流程",
            entity_type="project",
            description="测试用审批流程",
            is_active=True,
            created_by=1,
            created_at=now,
            updated_at=now,
        )
        data.update(kwargs)
        return ApprovalWorkflow(**data)

    @staticmethod
    def create(db, **kwargs):
        obj = ApprovalWorkflowFactory.build(**kwargs)
        db.add(obj)
        db.flush()
        return obj


class ApprovalNodeFactory:
    @staticmethod
    def build(workflow_id=1, level=1, **kwargs):
        now = datetime.now(timezone.utc)
        data = dict(
            workflow_id=workflow_id,
            level=level,
            name=f"第{level}级审批",
            approver_type="user",
            approver_id=1,
            timeout_hours=24,
            created_at=now,
        )
        data.update(kwargs)
        return ApprovalNode(**data)

    @staticmethod
    def create(db, workflow_id=1, level=1, **kwargs):
        obj = ApprovalNodeFactory.build(workflow_id=workflow_id, level=level, **kwargs)
        db.add(obj)
        db.flush()
        return obj


class ApprovalTaskFactory:
    @staticmethod
    def build(workflow_id=1, **kwargs):
        now = datetime.now(timezone.utc)
        data = dict(
            workflow_id=workflow_id,
            entity_type="project",
            entity_id=1,
            submitter_id=1,
            current_level=1,
            current_approver_id=1,
            status="pending",
            title="测试审批任务",
            description="测试审批任务描述",
            created_at=now,
            updated_at=now,
        )
        data.update(kwargs)
        return ApprovalTask(**data)

    @staticmethod
    def create(db, workflow_id=1, **kwargs):
        obj = ApprovalTaskFactory.build(workflow_id=workflow_id, **kwargs)
        db.add(obj)
        db.flush()
        return obj

    @staticmethod
    def build_approved(**kwargs):
        kwargs.setdefault("status", "approved")
        return ApprovalTaskFactory.build(**kwargs)

    @staticmethod
    def build_rejected(**kwargs):
        kwargs.setdefault("status", "rejected")
        return ApprovalTaskFactory.build(**kwargs)


class ApprovalRecordFactory:
    @staticmethod
    def build(task_id=1, level=1, **kwargs):
        now = datetime.now(timezone.utc)
        data = dict(
            task_id=task_id,
            level=level,
            approver_id=1,
            action="approve",
            opinion="同意",
            created_at=now,
        )
        data.update(kwargs)
        return ApprovalRecord(**data)

    @staticmethod
    def create(db, task_id=1, level=1, **kwargs):
        obj = ApprovalRecordFactory.build(task_id=task_id, level=level, **kwargs)
        db.add(obj)
        db.flush()
        return obj

    @staticmethod
    def build_reject(**kwargs):
        kwargs.setdefault("action", "reject")
        kwargs.setdefault("opinion", "不同意")
        return ApprovalRecordFactory.build(**kwargs)

    @staticmethod
    def build_transfer(**kwargs):
        kwargs.setdefault("action", "transfer")
        kwargs.setdefault("opinion", "转交处理")
        kwargs.setdefault("transfer_to_id", 2)
        return ApprovalRecordFactory.build(**kwargs)
