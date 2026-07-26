"""覆盖率攻坚: app/services/reminder_engine.py 缺口行 74（预算告警 approved<=0 跳过）."""
from unittest.mock import MagicMock


class TestBudgetWarningSkip:
    def test_zero_amount_fund_is_skipped(self):
        """amount 为 0 的经费触发 continue 分支（第 74 行），不产生告警."""
        from app.services.reminder_engine import scan_budget_warnings

        mock_db = MagicMock()
        zero_fund = MagicMock()
        zero_fund.id = 1
        zero_fund.name = "零额经费"
        zero_fund.amount = 0
        zero_fund.used_amount = 0
        mock_db.query.return_value.filter.return_value.all.return_value = [zero_fund]

        results = scan_budget_warnings(mock_db)
        assert results == []

    def test_none_amount_fund_is_skipped(self):
        """amount 为 None 时 `or 0` 后仍为 0，同样跳过（第 74 行）."""
        from app.services.reminder_engine import scan_budget_warnings

        mock_db = MagicMock()
        none_fund = MagicMock()
        none_fund.id = 2
        none_fund.name = "未设额经费"
        none_fund.amount = None
        none_fund.used_amount = 100.0
        mock_db.query.return_value.filter.return_value.all.return_value = [none_fund]

        results = scan_budget_warnings(mock_db)
        assert results == []
