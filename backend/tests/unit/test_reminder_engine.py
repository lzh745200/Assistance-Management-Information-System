"""TDD: 自动化提醒引擎."""
import pytest
from unittest.mock import MagicMock


class TestReminderScan:
    def test_overtime_approvals_detected(self):
        from app.services.reminder_engine import scan_overtime_approvals
        from datetime import datetime, timedelta
        mock_db = MagicMock()
        mock_task = MagicMock()
        mock_task.status = "pending"
        mock_task.created_at = datetime.now() - timedelta(hours=72)
        mock_task.id = 1
        mock_task.title = "测试审批"
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_task]
        results = scan_overtime_approvals(mock_db, hours_threshold=48)
        assert len(results) >= 1
        assert results[0]["type"] == "approval_overtime"

    def test_deadline_warning_detected(self):
        from app.services.reminder_engine import scan_deadline_warnings
        from datetime import datetime, timedelta
        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.name = "即将到期项目"
        mock_project.end_date = (datetime.now() + timedelta(days=3)).date()
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_project]
        results = scan_deadline_warnings(mock_db, days_threshold=7)
        assert len(results) >= 1

    def test_budget_warning_detected(self):
        from app.services.reminder_engine import scan_budget_warnings
        mock_db = MagicMock()
        mock_fund = MagicMock()
        mock_fund.id = 1
        mock_fund.name = "超预算经费"
        mock_fund.amount = 100000.0
        mock_fund.used_amount = 90000.0
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_fund]
        results = scan_budget_warnings(mock_db, warning_threshold=0.80)
        assert len(results) >= 1

    def test_no_warnings_when_clean(self):
        from app.services.reminder_engine import scan_overtime_approvals
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        results = scan_overtime_approvals(mock_db)
        assert len(results) == 0


class TestReminderDedup:
    def test_dedup_prevents_duplicate(self):
        from app.services.reminder_engine import should_skip_duplicate
        existing = [
            {"type": "approval_overtime", "entity_id": 1},
            {"type": "budget_warning", "entity_id": 2},
        ]
        assert should_skip_duplicate("approval_overtime", 1, existing) is True
        assert should_skip_duplicate("approval_overtime", 3, existing) is False
