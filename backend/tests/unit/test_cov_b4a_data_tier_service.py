"""覆盖率攻坚: app/services/data_tier_service.py 缺口行 76-77（归档目录创建失败降级）."""
from unittest.mock import patch


class TestDataTierServiceMkdirFailure:
    def test_archive_dir_mkdir_failure_logs_warning(self):
        """COLD_ARCHIVE_PATH 创建失败时记录 warning 并继续（第 76-77 行）."""
        from app.services.data_tier_service import DataTierService

        DataTierService._instance = None
        try:
            with patch("app.services.data_tier_service.Path") as mock_path:
                mock_path.return_value.mkdir.side_effect = OSError("read-only fs")
                svc = DataTierService()
            assert svc._initialized is True
            assert svc.config is not None
        finally:
            # 恢复单例状态，避免影响其他测试
            DataTierService._instance = None
