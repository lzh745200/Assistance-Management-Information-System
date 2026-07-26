"""b3 攻坚：覆盖 app.models.approval 的 level_count 与各状态属性"""
from app.models.approval import (
    ApprovalAction,
    ApprovalNode,
    ApprovalRecord,
    ApprovalStatus,
    ApprovalTask,
    ApprovalWorkflow,
)


class TestApprovalWorkflow:
    def test_repr(self):
        wf = ApprovalWorkflow(id=1, name="经费审批", entity_type="fund")
        assert "经费审批" in repr(wf)

    def test_level_count_empty(self):
        wf = ApprovalWorkflow(name="流程A", entity_type="fund")
        wf.nodes = []
        assert wf.level_count == 0

    def test_level_count_with_nodes(self):
        wf = ApprovalWorkflow(name="流程B", entity_type="fund")
        wf.nodes = [
            ApprovalNode(level=1, name="初审"),
            ApprovalNode(level=2, name="复审"),
        ]
        assert wf.level_count == 2


class TestApprovalNode:
    def test_repr(self):
        node = ApprovalNode(id=3, level=2, name="复审")
        assert "level=2" in repr(node)


class TestApprovalTask:
    def test_repr(self):
        task = ApprovalTask(id=1, entity_type="fund", entity_id=9, status=ApprovalStatus.PENDING.value)
        assert "fund:9" in repr(task)

    def test_is_pending(self):
        assert ApprovalTask(status=ApprovalStatus.PENDING.value).is_pending is True
        assert ApprovalTask(status=ApprovalStatus.APPROVED.value).is_pending is False

    def test_is_approved(self):
        assert ApprovalTask(status=ApprovalStatus.APPROVED.value).is_approved is True
        assert ApprovalTask(status=ApprovalStatus.PENDING.value).is_approved is False

    def test_is_rejected(self):
        assert ApprovalTask(status=ApprovalStatus.REJECTED.value).is_rejected is True
        assert ApprovalTask(status=ApprovalStatus.PENDING.value).is_rejected is False

    def test_is_withdrawn(self):
        assert ApprovalTask(status=ApprovalStatus.WITHDRAWN.value).is_withdrawn is True
        assert ApprovalTask(status=ApprovalStatus.PENDING.value).is_withdrawn is False


class TestApprovalRecord:
    def test_repr(self):
        rec = ApprovalRecord(id=1, task_id=2, action=ApprovalAction.APPROVE.value)
        assert "task_id=2" in repr(rec)

    def test_is_approved(self):
        assert ApprovalRecord(action=ApprovalAction.APPROVE.value).is_approved is True
        assert ApprovalRecord(action=ApprovalAction.REJECT.value).is_approved is False

    def test_is_rejected(self):
        assert ApprovalRecord(action=ApprovalAction.REJECT.value).is_rejected is True
        assert ApprovalRecord(action=ApprovalAction.APPROVE.value).is_rejected is False

    def test_is_transferred(self):
        assert ApprovalRecord(action=ApprovalAction.TRANSFER.value).is_transferred is True
        assert ApprovalRecord(action=ApprovalAction.APPROVE.value).is_transferred is False
