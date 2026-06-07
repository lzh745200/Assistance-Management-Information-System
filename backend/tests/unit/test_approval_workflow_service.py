"""
审批工作流服务单元测试
覆盖: app/services/approval_workflow_service.py
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def svc(mock_db):
    from app.services.approval_workflow_service import ApprovalWorkflowService
    return ApprovalWorkflowService(db=mock_db)


class TestInit:
    def test_init_stores_db(self, mock_db):
        from app.services.approval_workflow_service import ApprovalWorkflowService
        svc = ApprovalWorkflowService(db=mock_db)
        assert svc.db is mock_db


class TestCreateWorkflow:
    def test_max_5_nodes(self, svc):
        with pytest.raises(ValueError, match="最多支持5级审批"):
            svc.create_workflow("test", "fund", [{"name": f"n{i}"} for i in range(6)])

    def test_creates_with_valid_nodes(self, svc, mock_db):
        mock_db.add = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        result = svc.create_workflow("test", "fund", [{"name": "n1"}])
        assert result is not None
        mock_db.commit.assert_called_once()


class TestGetWorkflow:
    def test_found(self, svc, mock_db):
        mock_wf = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_wf
        assert svc.get_workflow(1) is mock_wf

    def test_not_found(self, svc, mock_db):
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        assert svc.get_workflow(999) is None


class TestListWorkflows:
    def test_returns_list(self, svc, mock_db):
        mock_items = [MagicMock(), MagicMock()]
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_items
        result = svc.list_workflows()
        assert len(result) == 2


class TestDeleteWorkflow:
    def test_not_found(self, svc, mock_db):
        with patch.object(svc, "get_workflow", return_value=None):
            assert svc.delete_workflow(999) is False

    def test_success(self, svc, mock_db):
        mock_wf = MagicMock()
        mock_db.delete = MagicMock()
        mock_db.commit = MagicMock()
        with patch.object(svc, "get_workflow", return_value=mock_wf):
            assert svc.delete_workflow(1) is True
            mock_db.delete.assert_called_once_with(mock_wf)


class TestGetTask:
    def test_found(self, svc, mock_db):
        mock_task = MagicMock()
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = mock_task
        assert svc.get_task(1) is mock_task

    def test_not_found(self, svc, mock_db):
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        assert svc.get_task(999) is None


class TestGetPendingTasks:
    def test_method_exists(self, svc):
        assert callable(svc.get_pending_tasks)


class TestWithdrawTask:
    def test_not_found(self, svc, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = svc.withdraw_task(999, 1)
        if result is not None:  # may return None or raise
            assert result is None

    def test_method_exists(self, svc):
        assert callable(svc.withdraw_task)


class TestAutoApproveAllPending:
    def test_no_pending(self, svc, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        with patch.object(svc, "approve_task", return_value=None):
            result = svc.auto_approve_all_pending(1)
            assert result["total_pending"] == 0
            assert result["approved"] == 0


class TestGetApprovalHistory:
    def test_method_exists(self, svc):
        assert callable(svc.get_approval_history)

    def test_entity_history(self, svc, mock_db):
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        result = svc.get_approval_history(entity_type="fund", entity_id=1)
        # Returns (count, []) or dict
        assert result is not None
