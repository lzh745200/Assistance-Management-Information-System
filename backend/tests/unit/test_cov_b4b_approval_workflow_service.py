"""补齐 app.services.approval_workflow_service 覆盖率缺口（221-225 行：审批消息推送异常分支）."""
import sys
from unittest.mock import MagicMock, patch

from app.services.approval_workflow_service import ApprovalWorkflowService


def _svc_with_workflow():
    db = MagicMock()
    node = MagicMock(approver_id=7)
    workflow = MagicMock(id=3, nodes=[node])
    db.query.return_value.options.return_value.filter.return_value.first.return_value = workflow
    return ApprovalWorkflowService(db), db


class TestSubmitApprovalMessagePush:
    def test_message_module_import_error_is_tolerated(self):
        svc, db = _svc_with_workflow()
        with patch.dict(sys.modules, {"app.models.message": None}):
            task = svc.submit_approval("fund", 1, submitter_id=2, title="经费审批")
        assert task is not None
        db.rollback.assert_not_called()

    def test_message_push_failure_rolls_back(self):
        svc, db = _svc_with_workflow()
        with patch("app.models.message.Message", side_effect=RuntimeError("boom")):
            task = svc.submit_approval("fund", 1, submitter_id=2, title="经费审批")
        assert task is not None
        db.rollback.assert_called_once()
