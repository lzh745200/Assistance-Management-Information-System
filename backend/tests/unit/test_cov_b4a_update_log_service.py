"""覆盖率攻坚: app/services/update_log_service.py 缺口行 429（历史数据为空时的 else 日志分支）."""
from unittest.mock import MagicMock, patch


class TestInitializeVersionHistoryEmptyData:
    def test_empty_version_history_data_hits_else_branch(self):
        """VERSION_HISTORY_DATA 为空时 initialized_count==0，走 else 日志分支（第 429 行）."""
        from app.services.update_log_service import UpdateLogService

        mock_db = MagicMock()
        mock_db.query.return_value.count.return_value = 0

        svc = UpdateLogService(mock_db)
        with patch("app.services.update_log_service.VERSION_HISTORY_DATA", []):
            result = svc.initialize_version_history(updated_by="tester")

        assert result["status"] == "success"
        assert result["initialized_count"] == 0
        mock_db.commit.assert_not_called()
