"""覆盖率攻坚: app/services/data_sync_service.py 缺口行 69-70（同步目录创建失败降级）."""
from unittest.mock import MagicMock, patch


class TestDataSyncServiceMkdirFailure:
    def test_mkdir_failure_logs_warning_and_continues(self):
        """sync_dir.mkdir 抛异常时记录 warning 并继续初始化（第 69-70 行）."""
        bad_base = MagicMock(name="app_data_dir")
        bad_sync_dir = bad_base.__truediv__.return_value
        bad_sync_dir.mkdir.side_effect = OSError("disk read-only")

        with patch("app.utils.paths.get_app_data_dir", return_value=bad_base):
            with patch("app.services.data_sync_service.app_logger") as mock_logger:
                from app.services.data_sync_service import DataSyncService

                svc = DataSyncService()

        mock_logger.warning.assert_called_once()
        assert "创建同步目录失败" in mock_logger.warning.call_args[0][0]
        assert svc.sync_dir is bad_sync_dir
        assert "supported_villages" in svc.syncable_tables
